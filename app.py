import streamlit as st
import pandas as pd
import requests
from groq import Groq
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
from datetime import datetime, date
import time
import os
import random
import urllib3
import json
import urllib.parse

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="LEANTTRO CRM", layout="wide", page_icon="⚡")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"

# --- CSS VISUAL (MANTIDO ORIGINAL NEON) ---
st.markdown("""
<style>
    /* IMPORTANDO FONTES DO SITE */
    @import url('https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;700&family=Kanit:ital,wght@0,300;0,600;0,800;1,800&display=swap');

    /* VARIÁVEIS DE COR */
    :root {
        --neon: #D2FF00;
        --black: #050505;
        --carbon: #111111;
        --white: #FAFAFA;
        --gray: #888888;
        --danger: #ff0055;
    }

    /* GLOBAL */
    .stApp {
        background-color: var(--black);
        font-family: 'Kanit', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Kanit', sans-serif;
        font-style: italic;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: -1px;
    }

    p, div, label, input {
        font-family: 'Chakra Petch', monospace;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: var(--carbon);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* BOTÕES (ESTILO LANDO NEON - INCLINADOS) */
    div.stButton > button {
        background-color: var(--neon) !important;
        color: var(--black) !important;
        border: none;
        border-radius: 0px;
        font-weight: 800;
        font-family: 'Kanit', sans-serif;
        font-style: italic;
        text-transform: uppercase;
        transform: skewX(-10deg);
        transition: all 0.3s ease;
        padding: 0.5rem 1rem;
    }
    div.stButton > button:hover {
        background-color: var(--white) !important;
        box-shadow: 0 0 15px rgba(210, 255, 0, 0.4);
    }
    div.stButton > button p {
        transform: skewX(10deg); /* Desentorta o texto */
    }
    
    /* LINK BUTTON (GMAIL) */
    a[data-testid="stLinkButton"] {
        background-color: var(--neon) !important;
        color: var(--black) !important;
        border: none;
        border-radius: 0px;
        font-weight: 800;
        font-family: 'Kanit', sans-serif;
        font-style: italic;
        text-transform: uppercase;
        transform: skewX(-10deg);
        transition: all 0.3s ease;
        padding: 0.5rem 1rem;
        text-decoration: none;
        display: inline-block;
        text-align: center;
    }
    a[data-testid="stLinkButton"]:hover {
        background-color: var(--white) !important;
        box-shadow: 0 0 15px rgba(210, 255, 0, 0.4);
    }

    /* INPUTS */
    div[data-baseweb="input"] {
        background-color: var(--black);
        border: 1px solid #333;
        border-radius: 0px;
    }
    div[data-baseweb="base-input"] input {
        color: var(--neon);
        font-family: 'Chakra Petch', monospace;
    }

    /* CARDS/METRICS */
    div[data-testid="stMetric"] {
        background-color: var(--carbon);
        border: 1px solid #333;
        padding: 15px;
        border-left: 4px solid var(--neon);
        transform: skewX(-5deg);
    }
    div[data-testid="stMetric"] label {
        color: var(--gray);
        font-size: 0.8rem;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: var(--white);
        font-family: 'Kanit', sans-serif;
        font-weight: 800;
        font-style: italic;
    }

    /* DATAFRAME / TABELA */
    div[data-testid="stDataFrame"] {
        border: 1px solid #333;
    }
    
    /* ABAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--carbon);
        border: 1px solid #333;
        color: var(--gray);
        border-radius: 0px;
        font-family: 'Chakra Petch', monospace;
        text-transform: uppercase;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--neon) !important;
        color: var(--black) !important;
        border-color: var(--neon) !important;
    }

    /* LOGO HEADER CUSTOM */
    .leanttro-header {
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 20px;
        margin-bottom: 30px;
    }
    .leanttro-title {
        font-size: 3rem;
        line-height: 1;
        color: var(--white);
        margin: 0;
    }
    .neon-text { color: var(--neon); }
    .leanttro-sub {
        font-family: 'Chakra Petch', monospace;
        color: var(--gray);
        font-size: 0.8rem;
        letter-spacing: 0.2rem;
        margin-top: 5px;
    }
    
    /* PROGRESS BAR CUSTOM */
    .stProgress > div > div > div > div {
        background-color: var(--neon);
    }

</style>
""", unsafe_allow_html=True)

# --- VARS & CLIENTE GROQ ---
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "") 

groq_client = None
if GROQ_API_KEY:
    try:
        groq_client = Groq(api_key=GROQ_API_KEY)
    except Exception as e:
        print(f"Erro ao inicializar Groq: {e}")

# =========================================================
#  FUNÇÕES AUXILIARES
# =========================================================

def render_header():
    st.markdown("""
    <div class="leanttro-header">
        <h1 class="leanttro-title">LEAN<span class="neon-text">TTRO</span>.</h1>
        <div class="leanttro-sub">// DIGITAL SOLUTIONS CRM SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)

def get_user_table_name(user_id):
    clean_id = str(user_id).replace("-", "_")
    return f"crm_{clean_id}"

def inicializar_crm_usuario(token, user_id):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # 1. Tabela CRM (Existente)
    r = requests.get(f"{base_url}/collections/{table_name}", headers=headers, verify=False)
    if r.status_code != 200:
        schema = {"collection": table_name, "schema": {}, "meta": {"icon": "rocket", "note": "Leanttro CRM Table"}}
        requests.post(f"{base_url}/collections", json=schema, headers=headers, verify=False)
        campos = [
            {"field": "nome", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "person"}},
            {"field": "empresa", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "domain"}},
            {"field": "email", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "email"}},
            {"field": "telefone", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "phone"}},
            {"field": "status", "type": "string", "meta": {"interface": "select-dropdown", "options": {"choices": [{"text": "NOVO", "value": "Novo"}, {"text": "QUENTE", "value": "Quente"}, {"text": "CLIENTE", "value": "Cliente"}]}}},
            {"field": "obs", "type": "text", "meta": {"interface": "input-multiline"}}
        ]
        for campo in campos: requests.post(f"{base_url}/fields/{table_name}", json=campo, headers=headers, verify=False)

    # 2. Tabela SMTP
    r_smtp = requests.get(f"{base_url}/collections/config_smtp", headers=headers, verify=False)
    if r_smtp.status_code != 200:
        schema_smtp = {"collection": "config_smtp", "schema": {}, "meta": {"icon": "email", "note": "SMTP Users Config"}}
        requests.post(f"{base_url}/collections", json=schema_smtp, headers=headers, verify=False)
        campos_smtp = [
            {"field": "smtp_host", "type": "string"},
            {"field": "smtp_port", "type": "integer"},
            {"field": "smtp_user", "type": "string"},
            {"field": "smtp_pass", "type": "string"}
        ]
        for c in campos_smtp: requests.post(f"{base_url}/fields/config_smtp", json=c, headers=headers, verify=False)
        
    return True, "CRM Initialized"

def criar_coluna_dinamica(token, user_id, nome_campo, tipo_interface):
    table_name = get_user_table_name(user_id)
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    slug = nome_campo.lower().strip().replace(" ", "_").replace("ç", "c")
    mapa = {"Texto": "string", "Número": "integer", "Data": "date"}
    type_d = mapa.get(tipo_interface, "string")
    
    payload = {
        "field": slug, "type": type_d,
        "meta": {"interface": "input", "width": "full"},
        "schema": {"is_nullable": True}
    }
    r = requests.post(f"{base_url}/fields/{table_name}", json=payload, headers=headers, verify=False)
    return r.status_code == 200

def carregar_dados(token, user_id):
    try:
        table = get_user_table_name(user_id)
        r = requests.get(f"{DIRECTUS_URL}/items/{table}?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if 'id' in df.columns:
                cols_pri = ['id', 'nome', 'empresa', 'email', 'telefone', 'status']
                cols_existentes = [c for c in cols_pri if c in df.columns]
                cols_restantes = [c for c in df.columns if c not in cols_existentes]
                return df[cols_existentes + cols_restantes]
    except: pass
    return pd.DataFrame(columns=["nome", "empresa", "email", "status", "telefone"])

# NOVA FUNÇÃO PARA CARREGAR DADOS DO BOT (ATUALIZADA)
def carregar_dados_bot(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/items/clients_bot?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            
            # Normalizar nomes de colunas para facilitar uso posterior
            # 'name' -> 'nome', 'whatsapp' -> 'telefone'
            if not df.empty:
                rename_map = {}
                if 'name' in df.columns: rename_map['name'] = 'nome'
                if 'whatsapp' in df.columns: rename_map['whatsapp'] = 'telefone'
                df.rename(columns=rename_map, inplace=True)

            # Filtra colunas relevantes para exibição
            cols_desejadas = ['id', 'nome', 'email', 'telefone', 'dor_principal', 'session_uuid']
            cols_existentes = [c for c in cols_desejadas if c in df.columns]
            return df[cols_existentes]
    except: pass
    return pd.DataFrame()

def atualizar_item(token, user_id, item_id, dados):
    table = get_user_table_name(user_id)
    requests.patch(f"{DIRECTUS_URL}/items/{table}/{item_id}", json=dados, headers={"Authorization": f"Bearer {token}"}, verify=False)

# --- FUNÇÕES SMTP (NOVO) ---
def carregar_config_smtp(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        r = requests.get(f"{base_url}/items/config_smtp?filter[user_created][_eq]=$CURRENT_USER&limit=1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            data = r.json()['data']
            if data: return data[0]
    except: pass
    return {}

def salvar_config_smtp(token, dados):
    base_url = DIRECTUS_URL.rstrip('/')
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    existente = carregar_config_smtp(token)
    if existente:
        r = requests.patch(f"{base_url}/items/config_smtp/{existente['id']}", json=dados, headers=headers, verify=False)
    else:
        r = requests.post(f"{base_url}/items/config_smtp", json=dados, headers=headers, verify=False)
    return r.status_code == 200

def contar_envios_hoje(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        hoje_str = datetime.now().strftime("%Y-%m-%d")
        url = f"{base_url}/items/historico_envios?filter[data_envio][_gte]={hoje_str}&filter[user_created][_eq]=$CURRENT_USER&aggregate[count]=*"
        r = requests.get(url, headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            data = r.json()['data']
            if isinstance(data, list) and len(data) > 0:
                return int(data[0].get('count', 0))
    except: pass
    return 0

def registrar_log_envio(token, destinatario, assunto, status):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        payload = {
            "data_envio": datetime.now().isoformat(),
            "destinatario": destinatario,
            "assunto": assunto,
            "status": status
        }
        requests.post(f"{base_url}/items/historico_envios", json=payload, headers={"Authorization": f"Bearer {token}"}, verify=False)
    except: pass

def enviar_email_smtp(smtp_config, to, subject, body, anexo=None):
    try:
        # Verifica se vamos fazer inserção de IMAGEM INLINE
        usar_imagem_inline = False
        if anexo is not None and "{{imagem}}" in body.lower():
            if "image" in anexo.type:
                usar_imagem_inline = True

        if usar_imagem_inline:
            msg = MIMEMultipart('related')
            msg['From'] = smtp_config['user']
            msg['To'] = to
            msg['Subject'] = subject
            msg_alternative = MIMEMultipart('alternative')
            msg.attach(msg_alternative)

            cid_id = "imagem_corpo"
            body_atualizado = body.replace("{{imagem}}", f'<br><img src="cid:{cid_id}" style="max-width:100%; height:auto;"><br>')
            msg_alternative.attach(MIMEText(body_atualizado, 'html'))

            img_data = anexo.getvalue()
            image = MIMEImage(img_data)
            image.add_header('Content-ID', f'<{cid_id}>') 
            image.add_header('Content-Disposition', 'inline', filename=anexo.name)
            msg.attach(image)
        else:
            msg = MIMEMultipart()
            msg['From'] = smtp_config['user']
            msg['To'] = to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            if anexo is not None:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(anexo.getvalue())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{anexo.name}"')
                msg.attach(part)

        server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
        server.starttls()
        server.login(smtp_config['user'], smtp_config['pass'])
        server.sendmail(smtp_config['user'], to, msg.as_string())
        server.quit()
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_copy_ia(ctx, dados_cliente=None):
    if not groq_client: return "Erro", "Configure a GROQ_API_KEY no ambiente"
    
    empresa = ctx.get('empresa', 'Nossa Empresa')
    descricao = ctx.get('descricao', 'Soluções Digitais')
    
    # Extrai dor principal se existir
    dor_cliente = ""
    if dados_cliente and 'dor_principal' in dados_cliente:
        d = dados_cliente['dor_principal']
        if d and str(d).lower() != 'none':
            dor_cliente = f"A principal dor/necessidade deste cliente é: {d}. Use isso para personalizar o texto."

    prompt = f"""
    Aja como um copywriter profissional B2B.
    Escreva um email curto (max 3 parágrafos) de prospecção fria.
    Minha Empresa: {empresa}
    O que vendemos: {descricao}
    {dor_cliente}
    Tom: Persuasivo, direto e sem enrolação corporativa.
    Foco: Marcar uma reunião ou resolver o problema dele.
    IMPORTANTE: Não coloque Assunto: no corpo, apenas o texto do email.
    """
    
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        msg_ia = chat_completion.choices[0].message.content
        return "Proposta Personalizada", msg_ia
    except Exception as e:
        return "Erro IA", str(e)

def validar_token(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200: return r.json()['data']
    except: pass
    return None

# =========================================================
#  INTERFACE
# =========================================================

# --- 1. PERSISTÊNCIA DE SESSÃO ---
if 'token' not in st.session_state:
    token_url = st.query_params.get("token")
    if token_url:
        user_data = validar_token(token_url)
        if user_data:
            st.session_state['token'] = token_url
            st.session_state['user'] = user_data

# --- TELA DE LOGIN ---
if 'token' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        render_header()
        st.markdown("<p style='text-align:center; color:#888'>// ACESSO RESTRITO</p>", unsafe_allow_html=True)
        email = st.text_input("E-MAIL")
        senha = st.text_input("SENHA", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            login_sucesso = False
            try:
                r = requests.post(f"{DIRECTUS_URL}/auth/login", json={"email": email, "password": senha}, verify=False)
                if r.status_code == 200:
                    token = r.json()['data']['access_token']
                    st.session_state['token'] = token
                    u = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {token}"}, verify=False)
                    st.session_state['user'] = u.json()['data']
                    st.query_params["token"] = token
                    login_sucesso = True
                else:
                    st.error("ACESSO NEGADO")
            except: st.error("ERRO DE CONEXÃO")
            
            if login_sucesso:
                st.rerun()
    st.stop()

token = st.session_state['token']
user = st.session_state['user']
user_id = user['id']

st.query_params["token"] = token

if 'setup_ok' not in st.session_state:
    inicializar_crm_usuario(token, user_id)
    # CARREGA SMTP SALVO AO INICIAR
    cfg = carregar_config_smtp(token)
    if cfg:
        st.session_state['smtp'] = {
            'host': cfg.get('smtp_host', 'smtp.gmail.com'),
            'port': cfg.get('smtp_port', 587),
            'user': cfg.get('smtp_user', ''),
            'pass': cfg.get('smtp_pass', '')
        }
    st.session_state['setup_ok'] = True

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h3 style='color:var(--neon)'>// USER: {user.get('first_name').upper()}</h3>", unsafe_allow_html=True)
    
    if st.button("LOGOUT / SAIR"):
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()
    
    st.divider()
    
    with st.expander("🛠️ CONSTRUTOR DE TABELA"):
        nc = st.text_input("NOME COLUNA")
        tc = st.selectbox("TIPO", ["Texto", "Número", "Data"])
        if st.button("CRIAR COLUNA"):
            if criar_coluna_dinamica(token, user_id, nc, tc):
                st.success("CRIADO!")
                time.sleep(1)
                st.rerun()

    with st.expander("🤖 DADOS DA EMPRESA (IA)"):
        en = st.text_input("NOME EMPRESA", value="Minha Agência")
        ed = st.text_area("O QUE VENDE?", value="Sites de alta conversão")
        if st.button("SALVAR CONTEXTO"):
            st.session_state['ctx'] = {'empresa': en, 'descricao': ed}
            st.success("SALVO")

    with st.expander("📧 SMTP CONFIG"):
        # Recupera valores salvos ou usa padrão
        saved = st.session_state.get('smtp', {})
        h = st.text_input("HOST", value=saved.get('host', "smtp.gmail.com"))
        p = st.number_input("PORT", value=int(saved.get('port', 587)))
        u = st.text_input("USER", value=saved.get('user', ""))
        pw = st.text_input("PASS", value=saved.get('pass', ""), type="password")
        
        # Botão agora salva no banco
        if st.button("SALVAR E CONECTAR"):
            st.session_state['smtp'] = {'host': h, 'port': p, 'user': u, 'pass': pw}
            salvar_config_smtp(token, {'smtp_host': h, 'smtp_port': p, 'smtp_user': u, 'smtp_pass': pw})
            st.success("SALVO E CONECTADO")

# --- MAIN ---
render_header()
df = carregar_dados(token, user_id)
df_bot = carregar_dados_bot(token) # CARREGA OS DADOS DO BOT

# --- METRICS & COTA ---
COTA_MAXIMA = 100
envios_realizados = contar_envios_hoje(token)
saldo_envios = COTA_MAXIMA - envios_realizados

k1, k2, k3 = st.columns(3)
k1.metric("TOTAL LEADS (CRM)", len(df))
k2.metric("LEADS BOT", len(df_bot))
k3.metric("SALDO DISPARO", saldo_envios)

if saldo_envios <= 0:
    st.error("⛔ COTA DE ENVIO DIÁRIA ATINGIDA. VOLTE AMANHÃ.")

st.markdown("<br>", unsafe_allow_html=True) # MANTIDA A LINHA AQUI

tab1, tab2 = st.tabs(["/// BASE DE LEADS & AÇÕES", "/// MODO SNIPER (DISPARO)"])

# --- ABA 1: BASE + WHATSAPP ---
with tab1:
    col_left, col_right = st.columns([2, 1])
    
    # LADO ESQUERDO: TABELAS
    with col_left:
        # ABAS INTERNAS PARA ALTERNAR ENTRE MESTRE E BOT
        sub_t1, sub_t2 = st.tabs(["📋 TABELA MESTRE", "🤖 TABELA BOT"])
        
        with sub_t1:
            edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
            if st.button("💾 SALVAR ALTERAÇÕES NA BASE"):
                chg = st.session_state["editor"]
                for idx, row in chg["edited_rows"].items():
                    try:
                        item_id = df.iloc[int(idx)]['id']
                        atualizar_item(token, user_id, item_id, row)
                    except: pass
                for row in chg["added_rows"]:
                    requests.post(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}", json=row, headers={"Authorization": f"Bearer {token}"}, verify=False)
                st.success("DADOS SINCRONIZADOS COM SUCESSO")
                time.sleep(1)
                st.rerun()
        
        with sub_t2:
            st.markdown("### DADOS CAPTURADOS (READ-ONLY)")
            st.dataframe(df_bot, use_container_width=True, height=400)

    # LADO DIREITO: AÇÕES
    with col_right:
        st.markdown("### ⚡ AÇÕES RÁPIDAS")
        
        # Seleção da fonte de dados
        fonte = st.radio("Fonte:", ["Base Mestre", "Bot Automático"], horizontal=True)
        
        df_ativo = df if fonte == "Base Mestre" else df_bot
        # Nota: carregar_dados_bot renomeou 'name' para 'nome' para padronizar
        col_nome = 'nome' 
        
        if not df_ativo.empty and col_nome in df_ativo.columns:
            nomes = df_ativo[col_nome].tolist()
            sel_cli = st.selectbox("Cliente:", ["Selecione..."] + nomes)
            
            if sel_cli != "Selecione...":
                dados_cli = df_ativo[df_ativo[col_nome] == sel_cli].iloc[0]
                
                # Campos comuns
                nome_cliente = dados_cli.get(col_nome, '')
                email_cliente = dados_cli.get('email', '')
                
                # Pega 'telefone' (já renomeado em carregar_dados_bot)
                tel = str(dados_cli.get('telefone', '')).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                if tel == 'nan' or tel == 'None': tel = ""
                
                # Mostra Dor se existir (para debug/visão do usuário)
                if 'dor_principal' in dados_cli:
                    st.info(f"💡 Dor: {dados_cli['dor_principal']}")

                # ABAS DE CANAL DE AÇÃO
                act_w, act_e = st.tabs(["WHATSAPP", "GMAIL (IA)"])
                
                with act_w:
                    msg_zap = st.text_area("Msg WhatsApp:", value=f"Olá {nome_cliente}, tudo bem?")
                    if tel:
                        link_zap = f"https://wa.me/55{tel}?text={urllib.parse.quote(msg_zap)}"
                        st.link_button("💬 ABRIR WHATSAPP", link_zap, use_container_width=True)
                    else:
                        st.warning("Sem telefone cadastrado.")
                
                with act_e:
                    st.caption("Gera um e-mail com IA e abre no seu Gmail para editar.")
                    if st.button("✨ GERAR E-MAIL IA"):
                        # Passa dados do cliente (incluindo dor) para a IA
                        assunto_ia, corpo_ia = gerar_copy_ia(st.session_state.get('ctx', {}), dados_cli)
                        
                        # Substitui placeholder se houver
                        corpo_final = corpo_ia.replace("{nome}", nome_cliente)
                        
                        # Cria link para abrir o Gmail (Web) com os campos preenchidos
                        assunto_safe = urllib.parse.quote(assunto_ia)
                        corpo_safe = urllib.parse.quote(corpo_final)
                        
                        link_gmail = f"https://mail.google.com/mail/?view=cm&fs=1&to={email_cliente}&su={assunto_safe}&body={corpo_safe}"
                        
                        st.markdown(f"**Assunto:** {assunto_ia}")
                        st.link_button("🚀 ABRIR NO GMAIL", link_gmail, use_container_width=True)

# --- ABA 2: MODO SNIPER (INTERNO E EXTERNO) ---
with tab2:
    if saldo_envios <= 0:
        st.warning("BLOQUEADO: COTA ATINGIDA")
        st.stop()

    subtab_int, subtab_ext = st.tabs(["[ 1 ] DISPARO INTERNO", "[ 2 ] IMPORTAR EXCEL"])

    # --- DISPARO INTERNO (BASE MESTRE + BOT) ---
    with subtab_int:
        c1, c2 = st.columns([1, 1])
        
        # PREPARA LISTA UNIFICADA PARA O MULTISELECT
        lista_mestre = pd.DataFrame()
        lista_bot_u = pd.DataFrame()

        if not df.empty and 'email' in df.columns:
            lista_mestre = df[['nome', 'email']].copy()
            lista_mestre['origem'] = 'Mestre'
        
        if not df_bot.empty and 'email' in df_bot.columns:
            lista_bot_u = df_bot[['nome', 'email']].copy()
            lista_bot_u['origem'] = 'Bot'

        # Concatena bases
        df_unificado = pd.concat([lista_mestre, lista_bot_u], ignore_index=True)
        # Filtra emails validos
        df_unificado = df_unificado[df_unificado['email'].str.contains("@", na=False)]
        
        # Cria label única para evitar duplicados de nome
        if not df_unificado.empty:
            df_unificado['label'] = df_unificado['nome'] + " (" + df_unificado['origem'] + ")"
        
        with c1:
            st.markdown("### SELEÇÃO (MESTRE + BOT)")
            opcoes = df_unificado['label'].tolist() if not df_unificado.empty else []
            sels = st.multiselect("ALVOS", opcoes)
            
        with c2:
            st.markdown("### MENSAGEM")
            assunto = st.text_input("ASSUNTO", key="ass_int")
            # Adicionado aviso sobre a tag
            st.caption("Dica: Use {{imagem}} no texto para inserir a imagem no corpo.")
            corpo = st.text_area("CORPO HTML (Use {nome})", height=150, key="body_int")
            file_anexo = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_int")
            
            if st.button("✨ GERAR COM IA (GROQ)"):
                sug_a, sug_c = gerar_copy_ia(st.session_state.get('ctx', {}))
                st.info(f"Assunto: {sug_a}")
                st.code(sug_c)

        if st.button("🚀 DISPARAR NA BASE"):
            if not st.session_state.get('smtp'):
                st.error("CONFIGURE O SMTP NA SIDEBAR")
            elif len(sels) > saldo_envios:
                st.error(f"SELEÇÃO ({len(sels)}) MAIOR QUE SALDO ({saldo_envios})")
            else:
                bar = st.progress(0)
                log = st.empty()
                for i, label_sel in enumerate(sels):
                    if i > 0:
                        wait = random.randint(15, 30)
                        log.warning(f"⏳ RECARREGANDO... {wait}s")
                        time.sleep(wait)
                    
                    # Recupera dados pelo label
                    tgt = df_unificado[df_unificado['label'] == label_sel].iloc[0]
                    nome_real = tgt['nome']
                    email_real = tgt['email']
                    
                    msg_final = corpo.replace("{nome}", nome_real)
                    
                    res, txt = enviar_email_smtp(st.session_state['smtp'], email_real, assunto, msg_final, file_anexo)
                    registrar_log_envio(token, email_real, assunto, "Enviado" if res else f"Erro: {txt}")
                    
                    if res: log.success(f"ENVIADO PARA {nome_real}")
                    else: log.error(f"ERRO {nome_real}: {txt}")
                    
                    bar.progress((i+1)/len(sels))
                st.balloons()
                time.sleep(2)
                st.rerun()

    # --- DISPARO EXTERNO (EXCEL) ---
    with subtab_ext:
        st.markdown("### 📂 UPLOAD DE LISTA (EXCEL .xlsx)")
        up_file = st.file_uploader("ARQUIVO EXCEL (Colunas: nome, email)", type=["xlsx"])
        
        if up_file:
            try:
                df_ext = pd.read_excel(up_file)
                df_ext.columns = [c.lower() for c in df_ext.columns]
                
                if 'email' in df_ext.columns:
                    df_ext = df_ext[df_ext['email'].astype(str).str.contains("@")]
                    st.dataframe(df_ext.head(), use_container_width=True)
                    st.info(f"{len(df_ext)} LEADS ENCONTRADOS")

                    assunto_ext = st.text_input("ASSUNTO", key="ass_ext")
                    st.caption("Dica: Use {{imagem}} no texto para inserir a imagem no corpo.")
                    corpo_ext = st.text_area("CORPO HTML (Use {nome})", height=150, key="body_ext")
                    file_anexo_ext = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_ext")
                    
                    if st.button("✨ GERAR COM IA (GROQ) - EXT"):
                        sug_a, sug_c = gerar_copy_ia(st.session_state.get('ctx', {}))
                        st.info(f"Assunto: {sug_a}")
                        st.code(sug_c)
                    
                    if st.button("🚀 DISPARAR LISTA EXTERNA"):
                        if not st.session_state.get('smtp'):
                            st.error("SMTP OFF")
                        elif len(df_ext) > saldo_envios:
                             st.error(f"LISTA ({len(df_ext)}) MAIOR QUE SALDO ({saldo_envios})")
                        else:
                            bar2 = st.progress(0)
                            log2 = st.empty()
                            
                            for i, row in df_ext.iterrows():
                                if i > 0:
                                    wait = random.randint(15, 30)
                                    log2.warning(f"⏳ ANTI-SPAM... {wait}s")
                                    time.sleep(wait)
                                
                                nome_l = row.get('nome', 'Parceiro')
                                email_l = row['email']
                                msg_final = corpo_ext.replace("{nome}", str(nome_l))
                                
                                res, txt = enviar_email_smtp(st.session_state['smtp'], email_l, assunto_ext, msg_final, file_anexo_ext)
                                registrar_log_envio(token, email_l, assunto_ext, "Enviado [EXT]" if res else f"Erro: {txt}")

                                if res: log2.success(f"ENVIADO: {email_l}")
                                else: log2.error(f"FALHA: {email_l}")
                                
                                bar2.progress((i+1)/len(df_ext))
                            st.balloons()
                            time.sleep(2)
                            st.rerun()
                else:
                    st.error("O EXCEL PRECISA TER UMA COLUNA CHAMADA 'email'")
            except Exception as e:
                st.error(f"ERRO AO LER EXCEL: {e}")