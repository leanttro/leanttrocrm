import streamlit as st
import pandas as pd
import requests
import google.generativeai as genai
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import time
import os
import random
import urllib.parse
import urllib3
import json

# --- CONFIGURAÇÕES ---
st.set_page_config(page_title="LEANTTRO CRM", layout="wide", page_icon="🚀")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"

# --- CSS LEANTTRO ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    div.stButton > button { background-color: #6366f1; color: white; border: none; border-radius: 6px; font-weight: 600; }
    div.stButton > button:hover { background-color: #4f46e5; }
    .metric-card { background-color: #1F2937; border: 1px solid #374151; padding: 15px; border-radius: 8px; border-left: 4px solid #6366f1; }
    .metric-card h3 { color: #9CA3AF; font-size: 14px; margin: 0; }
    .metric-card h1 { color: #F3F4F6; margin: 5px 0 0 0; }
    section[data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #374151; }
</style>
""", unsafe_allow_html=True)

# --- VARS ---
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") 

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# =========================================================
#  FUNÇÕES DE INFRAESTRUTURA (SAAS)
# =========================================================

def get_user_table_name(user_id):
    """Gera o nome da tabela única para este usuário"""
    clean_id = str(user_id).replace("-", "_")
    return f"crm_{clean_id}"

def inicializar_crm_usuario(token, user_id):
    """Cria a tabela do usuário se não existir"""
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Verifica se existe
    r = requests.get(f"{base_url}/collections/{table_name}", headers=headers, verify=False)
    if r.status_code == 200:
        return True, "CRM Carregado"
    
    # 2. Cria a tabela
    schema = {
        "collection": table_name,
        "schema": {},
        "meta": {"icon": "rocket", "note": "Tabela Privada SaaS"}
    }
    r_create = requests.post(f"{base_url}/collections", json=schema, headers=headers, verify=False)
    
    if r_create.status_code != 200:
        return False, f"Erro ao criar tabela: {r_create.text}"
    
    # 3. Campos Padrão Obrigatórios
    campos_padrao = [
        {"field": "nome", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "person"}},
        {"field": "empresa", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "domain"}},
        {"field": "email", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "email"}},
        {"field": "telefone", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "phone"}},
        {"field": "status", "type": "string", "meta": {"interface": "select-dropdown", "options": {"choices": [{"text": "Novo", "value": "Novo"}, {"text": "Negociando", "value": "Negociando"}, {"text": "Fechado", "value": "Fechado"}]}}},
        {"field": "obs", "type": "text", "meta": {"interface": "input-multiline"}}
    ]
    
    for campo in campos_padrao:
        requests.post(f"{base_url}/fields/{table_name}", json=campo, headers=headers, verify=False)
        
    return True, "CRM Inicializado com Sucesso!"

def criar_coluna_dinamica(token, user_id, nome_campo, tipo_interface):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    slug = nome_campo.lower().strip().replace(" ", "_").replace("ç", "c").replace("ã", "a")
    
    mapa_tipos = {
        "Texto": {"type": "string", "interface": "input"},
        "Número": {"type": "integer", "interface": "input"},
        "Data": {"type": "date", "interface": "datetime"},
        "Sim/Não": {"type": "boolean", "interface": "boolean"},
        "Lista": {"type": "string", "interface": "tags"}
    }
    
    config = mapa_tipos.get(tipo_interface, mapa_tipos["Texto"])
    
    payload = {
        "field": slug,
        "type": config["type"],
        "meta": {
            "interface": config["interface"],
            "display": "raw",
            "width": "full"
        },
        "schema": {"is_nullable": True}
    }
    
    r = requests.post(f"{base_url}/fields/{table_name}", json=payload, headers=headers, verify=False)
    return r.status_code == 200, r.text

# =========================================================
#  FUNÇÕES BACKEND GERAIS
# =========================================================

def login_directus(email, password):
    try:
        r = requests.post(f"{DIRECTUS_URL}/auth/login", json={"email": email, "password": password}, verify=False)
        if r.status_code == 200:
            token = r.json()['data']['access_token']
            u = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
            return token, u.json()['data']
    except: pass
    return None, None

def carregar_dados(token, user_id):
    table = get_user_table_name(user_id)
    try:
        r = requests.get(f"{DIRECTUS_URL}/items/{table}?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if not df.empty and 'id' in df.columns:
                cols = ['id', 'nome', 'empresa', 'email', 'telefone', 'status'] + [c for c in df.columns if c not in ['id', 'nome', 'empresa', 'email', 'telefone', 'status']]
                return df[cols]
            return df
    except: pass
    return pd.DataFrame()

def atualizar_item(token, user_id, item_id, dados):
    table = get_user_table_name(user_id)
    requests.patch(f"{DIRECTUS_URL}/items/{table}/{item_id}", json=dados, headers={"Authorization": f"Bearer {token}"}, verify=False)

def enviar_email_smtp(smtp_config, to, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_config['user']
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        server.starttls()
        server.login(smtp_config['user'], smtp_config['pass'])
        server.sendmail(smtp_config['user'], to, msg.as_string())
        server.quit()
        return True, "Enviado"
    except Exception as e: return False, str(e)

def gerar_copy_ia(nome, empresa, user_contexto):
    if not GEMINI_API_KEY: return "Erro: Configure a IA", "..."
    prompt = f"""
    Aja como um especialista em vendas da empresa: {user_contexto['empresa']}.
    O que a empresa vende: {user_contexto['descricao']}.
    
    Escreva um email frio curto e direto para {nome} da empresa {empresa}.
    Objetivo: Agendar reunião.
    Tom: Profissional mas próximo. Sem clichês de marketing.
    
    Saída: ASSUNTO|||CORPO
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(prompt)
        txt = res.text
        if "|||" in txt:
            return txt.split("|||")
        return "Proposta de Parceria", txt
    except: return "Olá", "Erro ao gerar texto."

# =========================================================
#  APP
# =========================================================

if 'token' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        st.title("🚀 LEANTTRO CRM")
        st.write("Acesse sua conta para gerenciar seus leads.")
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True):
            t, u = login_directus(email, senha)
            if t:
                st.session_state['token'] = t
                st.session_state['user'] = u
                st.rerun()
            else:
                st.error("Credenciais inválidas")
    st.stop()

token = st.session_state['token']
user = st.session_state['user']
user_id = user['id']

# --- SETUP INICIAL AUTOMÁTICO ---
if 'setup_ok' not in st.session_state:
    ok, msg = inicializar_crm_usuario(token, user_id)
    st.session_state['setup_ok'] = ok

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Leanttro CRM")
    st.write(f"Olá, **{user.get('first_name')}**")
    
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()
    
    st.divider()
    
    with st.expander("🛠️ Construtor de Tabela"):
        st.caption("Crie colunas personalizadas para seu negócio.")
        novo_campo = st.text_input("Nome da Coluna (ex: Cargo)")
        tipo_campo = st.selectbox("Tipo", ["Texto", "Número", "Data", "Sim/Não", "Lista"])
        if st.button("➕ Adicionar Coluna"):
            ok, log = criar_coluna_dinamica(token, user_id, novo_campo, tipo_campo)
            if ok: 
                st.success("Coluna criada!")
                time.sleep(1)
                st.rerun()
            else: st.error(log)
            
    with st.expander("📧 Config SMTP"):
        host = st.text_input("Host", value="smtp.gmail.com")
        port = st.number_input("Porta", value=587)
        u_email = st.text_input("Seu Email")
        u_pass = st.text_input("Senha de App", type="password")
        if st.button("Salvar Config Temp"):
            st.session_state['smtp'] = {'host': host, 'port': port, 'user': u_email, 'pass': u_pass}
            st.success("Salvo na sessão")

    with st.expander("🤖 Config da Sua Empresa"):
        st.caption("Para a IA escrever e-mails melhores")
        empresa_nome = st.text_input("Nome da Sua Empresa", value="Minha Agência")
        empresa_desc = st.text_area("O que você vende?", value="Desenvolvimento de Software e Marketing")
        if st.button("Atualizar Contexto IA"):
            st.session_state['contexto_ia'] = {'empresa': empresa_nome, 'descricao': empresa_desc}
            st.success("IA Atualizada")

# --- MAIN ---
df = carregar_dados(token, user_id)

st.title("Visão Geral")

if df.empty:
    st.info("👋 Bem-vindo! Comece adicionando leads na tabela abaixo ou crie colunas no menu lateral.")
    # Cria linha vazia para permitir inserção
    df = pd.DataFrame(columns=["nome", "empresa", "email", "status", "obs"])

# Métricas
c1, c2, c3 = st.columns(3)
c1.metric("Total Leads", len(df))
c2.metric("Novos", len(df[df['status'] == 'Novo']) if 'status' in df.columns else 0)
c3.metric("Fechados", len(df[df['status'] == 'Fechado']) if 'status' in df.columns else 0)

st.divider()

# Abas
tab1, tab2 = st.tabs(["📋 Gestão de Leads", "🎯 Modo Disparo (Sniper)"])

with tab1:
    st.subheader("Base de Dados")
    
    # Grid Editável
    edited = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True,
        key="data_editor"
    )
    
    # Salvar Edições
    if st.button("💾 Salvar Alterações"):
        changes = st.session_state["data_editor"]
        
        # 1. Novos
        for new_row in changes["added_rows"]:
            requests.post(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}", json=new_row, headers={"Authorization": f"Bearer {token}"}, verify=False)
            
        # 2. Edições
        for idx, edits in changes["edited_rows"].items():
            item_id = df.iloc[int(idx)]['id']
            atualizar_item(token, user_id, item_id, edits)
            
        # 3. Deletados
        for idx in changes["deleted_rows"]:
            item_id = df.iloc[int(idx)]['id']
            requests.delete(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}/{item_id}", headers={"Authorization": f"Bearer {token}"}, verify=False)
            
        st.success("Dados sincronizados!")
        time.sleep(1)
        st.rerun()

with tab2:
    st.subheader("Disparo Inteligente")
    
    if 'email' not in df.columns:
        st.warning("Você precisa de uma coluna chamada 'email' para usar esta função.")
    else:
        leads = df[df['email'].str.contains("@", na=False)]
        selecionados = st.multiselect("Selecione os Leads", leads['nome'].tolist())
        
        c_msg1, c_msg2 = st.columns(2)
        with c_msg1:
            assunto = st.text_input("Assunto", "Oportunidade de Parceria")
            corpo = st.text_area("Mensagem (Use {nome} para personalizar)", height=200)
            
        with c_msg2:
            st.markdown("### ✨ Gerar com IA")
            if st.button("Escrever E-mail Persuasivo"):
                ctx = st.session_state.get('contexto_ia', {'empresa': 'Minha Empresa', 'descricao': 'Serviços Gerais'})
                sug_assunto, sug_corpo = gerar_copy_ia("Nome Cliente", "Empresa Cliente", ctx)
                st.info(f"Assunto Sugerido: {sug_assunto}")
                st.code(sug_corpo)
        
        if st.button("🚀 Enviar Sequência (Modo Seguro)"):
            smtp = st.session_state.get('smtp')
            if not smtp:
                st.error("Configure o SMTP na barra lateral primeiro.")
            else:
                progress = st.progress(0)
                status = st.empty()
                
                for i, nome_lead in enumerate(selecionados):
                    # Delay anti-spam
                    if i > 0:
                        wait = random.randint(15, 45)
                        status.info(f"⏳ Aguardando {wait}s (Anti-Spam)...")
                        time.sleep(wait)
                    
                    row = leads[leads['nome'] == nome_lead].iloc[0]
                    msg_final = corpo.replace("{nome}", row['nome']).replace("{empresa}", row.get('empresa', ''))
                    
                    ok, log = enviar_email_smtp(smtp, row['email'], assunto, msg_final)
                    
                    if ok:
                        status.success(f"Enviado para {row['nome']}")
                    else:
                        status.error(f"Erro {row['nome']}: {log}")
                    
                    progress.progress((i+1)/len(selecionados))
                
                st.balloons()