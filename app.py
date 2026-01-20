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
    
    /* --- CORREÇÃO DE LEITURA DAS TAGS (MULTISELECT) --- */
    span[data-baseweb="tag"] {
        color: var(--black) !important; /* Texto preto */
    }
    span[data-baseweb="tag"] span {
        color: var(--black) !important; /* Garante texto interno preto */
    }
    span[data-baseweb="tag"] svg {
        fill: var(--black) !important; /* Ícone 'x' preto */
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
    
    # 1. Tabela CRM
    r = requests.get(f"{base_url}/collections/{table_name}", headers=headers, verify=False)
    if r.status_code != 200:
        schema = {"collection": table_name, "schema": {}, "meta": {"icon": "rocket", "note": "Leanttro CRM Table"}}
        requests.post(f"{base_url}/collections", json=schema, headers=headers, verify=False)
    
    # Lista de campos padrão
    campos = [
        {"field": "nome", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "person"}},
        {"field": "empresa", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "domain"}},
        {"field": "email", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "email"}},
        {"field": "telefone", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "phone"}},
        {"field": "origem", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "map"}},
        {"field": "url", "type": "string", "meta": {"interface": "input", "width": "full", "icon": "link"}},
        {"field": "status", "type": "string", "meta": {"interface": "select-dropdown", "options": {"choices": [{"text": "NOVO", "value": "Novo"}, {"text": "QUENTE", "value": "Quente"}, {"text": "CLIENTE", "value": "Cliente"}, {"text": "ENVIADO EM MASSA", "value": "ENVIADO EM MASSA"}]}}},
        {"field": "obs", "type": "text", "meta": {"interface": "input-multiline"}}
    ]
    
    for campo in campos:
        try:
            requests.post(f"{base_url}/fields/{table_name}", json=campo, headers=headers, verify=False)
        except:
            pass 

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
                cols_pri = ['id', 'nome', 'empresa', 'email', 'telefone', 'origem', 'status']
                cols_existentes = [c for c in cols_pri if c in df.columns]
                cols_restantes = [c for c in df.columns if c not in cols_existentes]
                return df[cols_existentes + cols_restantes]
    except: pass
    return pd.DataFrame(columns=["nome", "empresa", "email", "status", "telefone"])

def carregar_dados_bot(token):
    try:
        r = requests.get(f"{DIRECTUS_URL}/items/clients_bot?limit=-1", headers={"Authorization": f"Bearer {token}"}, verify=False)
        if r.status_code == 200:
            df = pd.DataFrame(r.json()['data'])
            if not df.empty:
                rename_map = {}
                if 'name' in df.columns: rename_map['name'] = 'nome'
                if 'whatsapp' in df.columns: rename_map['whatsapp'] = 'telefone'
                df.rename(columns=rename_map, inplace=True)
            cols_desejadas = ['id', 'nome', 'email', 'telefone', 'dor_principal', 'session_uuid']
            cols_existentes = [c for c in cols_desejadas if c in df.columns]
            return df[cols_existentes]
    except: pass
    return pd.DataFrame()

def atualizar_item(token, user_id, item_id, dados):
    table = get_user_table_name(user_id)
    requests.patch(f"{DIRECTUS_URL}/items/{table}/{item_id}", json=dados, headers={"Authorization": f"Bearer {token}"}, verify=False)

# --- FUNÇÕES SMTP (PERSISTÊNCIA CORRIGIDA) ---
def carregar_config_smtp(token):
    try:
        base_url = DIRECTUS_URL.rstrip('/')
        # Busca a configuração criada pelo usuário atual (user_created = $CURRENT_USER)
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
        # --- CORREÇÃO DE SEGURANÇA: CONVERSÃO DE TIPOS ESTRITA ---
        # 1. Garante que a porta é um INTEIRO
        try:
            porta_safe = int(float(smtp_config['port']))
        except:
            return False, "Porta SMTP inválida (deve ser número inteiro)"
            
        # 2. Garante que os campos de texto sejam STRINGS limpas
        to_safe = str(to).strip()
        subject_safe = str(subject).strip()
        host_safe = str(smtp_config['host']).strip()
        user_safe = str(smtp_config['user']).strip()
        pass_safe = str(smtp_config['pass']).strip()

        # Validação simples
        if not to_safe or "@" not in to_safe:
            return False, "Email destinatário inválido"

        usar_imagem_inline = False
        if anexo is not None and "{{imagem}}" in body.lower():
            if "image" in anexo.type:
                usar_imagem_inline = True

        if usar_imagem_inline:
            msg = MIMEMultipart('related')
            msg['From'] = user_safe
            msg['To'] = to_safe
            msg['Subject'] = subject_safe
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
            msg['From'] = user_safe
            msg['To'] = to_safe
            msg['Subject'] = subject_safe
            msg.attach(MIMEText(body, 'html'))
            if anexo is not None:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(anexo.getvalue())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{anexo.name}"')
                msg.attach(part)

        server = smtplib.SMTP(host_safe, porta_safe)
        server.starttls()
        server.login(user_safe, pass_safe)
        server.sendmail(user_safe, to_safe, msg.as_string())
        server.quit()
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_copy_ia(ctx, dados_cliente=None):
    if not groq_client: return "Erro", "Configure a GROQ_API_KEY no ambiente"
    
    empresa = ctx.get('empresa', 'Nossa Empresa')
    descricao = ctx.get('descricao', 'Soluções Digitais')
    segmento_alvo = ctx.get('segmento_alvo', '') 
    
    dor_cliente = ""
    if dados_cliente is not None and 'dor_principal' in dados_cliente:
        d = dados_cliente['dor_principal']
        if d and str(d).lower() != 'none':
            dor_cliente = f"A principal dor/necessidade deste cliente é: {d}. Use isso para personalizar o texto."
    
    instrucao_segmento = ""
    if segmento_alvo:
        instrucao_segmento = f"CONTEXTO IMPORTANTE: O público alvo deste disparo são empresas/pessoas do seguinte perfil/segmento: '{segmento_alvo}'. Adapte a linguagem e exemplos para eles."

    prompt = f"""
    Aja como um copywriter profissional B2B.
    Escreva um email curto (max 3 parágrafos) de prospecção fria.
    Minha Empresa: {empresa}
    O que vendemos: {descricao}
    {instrucao_segmento}
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
    st.session_state['setup_ok'] = True

# --- FIX CRUCIAL: CARREGAR SMTP DO BANCO PARA OS WIDGETS ANTES DA RENDERIZAÇÃO ---
if 'smtp_loaded' not in st.session_state:
    cfg = carregar_config_smtp(token)
    
    # Define valores padrão se não existir no banco
    host_init = cfg.get('smtp_host', 'smtp.gmail.com')
    # Força conversão para inteiro para o widget number_input
    try:
        port_init = int(cfg.get('smtp_port', 587))
    except:
        port_init = 587
    user_init = cfg.get('smtp_user', '')
    pass_init = cfg.get('smtp_pass', '')

    # Salva na sessao para uso nas funcoes de envio
    st.session_state['smtp'] = {
        'host': host_init,
        'port': port_init,
        'user': user_init,
        'pass': pass_init
    }
    
    # Salva nas KEYS EXATAS dos widgets para que eles já apareçam preenchidos visualmente
    st.session_state['smtp_host_input'] = host_init
    st.session_state['smtp_port_input'] = port_init
    st.session_state['smtp_user_input'] = user_init
    st.session_state['smtp_pass_input'] = pass_init
    
    st.session_state['smtp_loaded'] = True

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

    with st.expander("📧 SMTP CONFIG", expanded=True):
        # Os valores são puxados automaticamente do st.session_state pelas keys (smtp_host_input, etc)
        h = st.text_input("HOST", key="smtp_host_input")
        # step=1 garante que seja tratado como inteiro na interface
        p = st.number_input("PORT", step=1, format="%d", key="smtp_port_input") 
        u = st.text_input("USER", key="smtp_user_input")
        pw = st.text_input("PASS", type="password", key="smtp_pass_input")
        
        if st.button("SALVAR E CONECTAR"):
            st.session_state['smtp'] = {'host': h, 'port': p, 'user': u, 'pass': pw}
            salvar_config_smtp(token, {'smtp_host': h, 'smtp_port': p, 'smtp_user': u, 'smtp_pass': pw})
            st.toast("Configurações salvas no DB e conectadas!", icon="✅")
            time.sleep(1)

# --- MAIN ---
render_header()
df = carregar_dados(token, user_id)
df_bot = carregar_dados_bot(token)

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

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["/// BASE DE LEADS & AÇÕES", "/// MODO SNIPER (DISPARO)"])

# --- ABA 1: BASE + WHATSAPP ---
with tab1:
    # 1. ÁREA DE FILTROS & COLUNAS
    with st.expander("🔎 FILTRAR & PERSONALIZAR TABELA", expanded=True):
        f_c1, f_c2 = st.columns([1, 1])
        
        with f_c1:
            st.markdown("##### 👁️ COLUNAS VISÍVEIS (ARRASTE PARA ORDENAR)")
            all_cols = list(df.columns)
            
            if 'cols_visiveis_save' not in st.session_state:
                st.session_state['cols_visiveis_save'] = all_cols
                
            cols_visiveis = st.multiselect("Escolha e ordene as colunas:", all_cols, default=st.session_state['cols_visiveis_save'])
            
            if cols_visiveis != st.session_state['cols_visiveis_save']:
                st.session_state['cols_visiveis_save'] = cols_visiveis
                st.rerun()
        
        with f_c2:
            st.markdown("##### 🌪️ FILTRAR DADOS")
            col_para_filtrar = st.selectbox("Filtrar na coluna:", ["(Sem Filtro)"] + all_cols)
            
            filtro_valores = []
            if col_para_filtrar != "(Sem Filtro)":
                valores_unicos = df[col_para_filtrar].unique().tolist()
                valores_unicos = [str(x) for x in valores_unicos] 
                filtro_valores = st.multiselect(f"Selecione valores de '{col_para_filtrar}':", valores_unicos)

    df_visual = df.copy()
    if col_para_filtrar != "(Sem Filtro)" and filtro_valores:
        df_visual = df_visual[df_visual[col_para_filtrar].astype(str).isin(filtro_valores)]

    if cols_visiveis:
        cols_final = [c for c in cols_visiveis]
        if 'id' not in cols_final and 'id' in df_visual.columns:
            cols_final.append('id')
        df_visual = df_visual[cols_final]

    sub_t1, sub_t2 = st.tabs(["📋 TABELA MESTRE", "🤖 TABELA BOT"])
    
    with sub_t1:
        col_config = {}
        if 'id' in df_visual.columns and 'id' not in cols_visiveis:
             col_config['id'] = st.column_config.Column("id", disabled=True, hidden=True)

        edited = st.data_editor(
            df_visual, 
            num_rows="dynamic", 
            use_container_width=True, 
            key="editor",
            column_config=col_config
        )
        
        if st.button("💾 SALVAR ALTERAÇÕES NA BASE"):
            chg = st.session_state["editor"]
            
            # EXCLUIR
            deleted_indices = chg.get("deleted_rows", [])
            for idx in deleted_indices:
                try:
                    if not df_visual.empty and idx < len(df_visual):
                        item_id_del = df_visual.iloc[idx]['id']
                        requests.delete(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}/{item_id_del}", headers={"Authorization": f"Bearer {token}"}, verify=False)
                except Exception as e:
                    st.error(f"Erro ao excluir linha: {e}")

            # EDITAR
            for idx, row in chg["edited_rows"].items():
                try:
                    if int(idx) < len(df_visual):
                        item_id = df_visual.iloc[int(idx)]['id']
                        atualizar_item(token, user_id, item_id, row)
                except: pass
            
            # ADICIONAR
            max_id = 0
            df_fresh = carregar_dados(token, user_id)
            if not df_fresh.empty and 'id' in df_fresh.columns:
                try:
                    max_id = pd.to_numeric(df_fresh['id'], errors='coerce').max()
                    if pd.isna(max_id): max_id = 0
                except: max_id = 0
            proximo_id = int(max_id) + 1

            for row in chg["added_rows"]:
                if 'id' not in row or not row['id']:
                    row['id'] = proximo_id
                    proximo_id += 1
                requests.post(f"{DIRECTUS_URL}/items/{get_user_table_name(user_id)}", json=row, headers={"Authorization": f"Bearer {token}"}, verify=False)
            
            # REORGANIZAR
            if deleted_indices:
                try:
                    df_reorg = carregar_dados(token, user_id)
                    if not df_reorg.empty and 'id' in df_reorg.columns:
                        df_reorg['id'] = pd.to_numeric(df_reorg['id'], errors='coerce')
                        df_reorg = df_reorg.sort_values(by='id')
                        novo_contador = 1
                        table_n = get_user_table_name(user_id)
                        headers_api = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                        for i, r_row in df_reorg.iterrows():
                            id_atual = int(r_row['id'])
                            if id_atual != novo_contador:
                                requests.patch(f"{DIRECTUS_URL}/items/{table_n}/{id_atual}", json={"id": novo_contador}, headers=headers_api, verify=False)
                            novo_contador += 1
                except: pass

            st.toast("Dados atualizados!", icon="✅")
            time.sleep(1)
            st.rerun()
    
    with sub_t2:
        st.markdown("### DADOS CAPTURADOS (READ-ONLY)")
        st.dataframe(df_bot, use_container_width=True, height=400)

    st.divider()

    # 3. ÁREA DE AÇÕES
    st.markdown("### ⚡ AÇÕES RÁPIDAS (LINHA ÚNICA)")
    
    col_fonte, col_cli, col_vazio = st.columns([1, 2, 3])
    with col_fonte:
        fonte = st.radio("Fonte de Dados:", ["Base Mestre", "Bot Automático"], horizontal=True)
    
    df_ativo = df if fonte == "Base Mestre" else df_bot
    col_nome = 'nome' 
    
    with col_cli:
        nomes = []
        if not df_ativo.empty and col_nome in df_ativo.columns:
            nomes = df_ativo[col_nome].tolist()
        sel_cli = st.selectbox("Selecione o Cliente para Agir:", ["Selecione..."] + nomes)

    if sel_cli != "Selecione..." and not df_ativo.empty:
        dados_cli = df_ativo[df_ativo[col_nome] == sel_cli].iloc[0]
        nome_cliente = dados_cli.get(col_nome, '')
        email_cliente = dados_cli.get('email', '')
        tel = str(dados_cli.get('telefone', '')).replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if tel == 'nan' or tel == 'None': tel = ""
        
        act_c1, act_c2 = st.columns(2)
        with act_c1:
            st.markdown("#### 💬 WHATSAPP")
            msg_zap = st.text_area("Mensagem:", value=f"Olá {nome_cliente}, tudo bem?", height=100)
            if tel:
                link_zap = f"https://wa.me/55{tel}?text={urllib.parse.quote(msg_zap)}"
                st.link_button("ENVIAR WHATSAPP", link_zap, use_container_width=True)
            else:
                st.warning("Sem telefone cadastrado.")

        with act_c2:
            st.markdown("#### 📧 GMAIL (IA)")
            if st.button("GERAR TEXTO COM IA"):
                assunto_ia, corpo_ia = gerar_copy_ia(st.session_state.get('ctx', {}), dados_cli)
                corpo_final = corpo_ia.replace("{nome}", nome_cliente)
                link_gmail = f"https://mail.google.com/mail/?view=cm&fs=1&to={email_cliente}&su={urllib.parse.quote(assunto_ia)}&body={urllib.parse.quote(corpo_final)}"
                st.markdown(f"**Assunto:** {assunto_ia}")
                st.link_button("ABRIR NO GMAIL", link_gmail, use_container_width=True)

# --- ABA 2: MODO SNIPER (INTERNO E EXTERNO) ---
with tab2:
    if saldo_envios <= 0:
        st.warning("BLOQUEADO: COTA ATINGIDA")
        st.stop()

    subtab_int, subtab_ext = st.tabs(["[ 1 ] DISPARO INTERNO", "[ 2 ] IMPORTAR EXCEL"])

    with subtab_int:
        lista_mestre = pd.DataFrame()
        lista_bot_u = pd.DataFrame()

        if not df.empty and 'email' in df.columns:
            lista_mestre = df.copy()
            lista_mestre['origem'] = 'Mestre'
        
        if not df_bot.empty and 'email' in df_bot.columns:
            lista_bot_u = df_bot.copy()
            lista_bot_u['origem'] = 'Bot'

        df_unificado = pd.concat([lista_mestre, lista_bot_u], ignore_index=True)
        # Filtro básico de @
        df_unificado = df_unificado[df_unificado['email'].astype(str).str.contains("@", na=False)]
        
        with st.expander("🎯 FILTRAGEM INTELIGENTE (SEGMENTAÇÃO)", expanded=True):
            f_s1, f_s2, f_s3 = st.columns([1, 2, 1])
            with f_s1:
                col_sniper = st.selectbox("Filtrar por:", ["(Todos)"] + list(df_unificado.columns), key="col_sniper")
            with f_s2:
                vals_sniper = []
                if col_sniper != "(Todos)":
                    unique_vals = [str(x) for x in df_unificado[col_sniper].unique()]
                    vals_sniper = st.multiselect(f"Valores em '{col_sniper}':", unique_vals, key="vals_sniper")
            with f_s3:
                ocultar_enviados = st.checkbox("Ocultar Status 'ENVIADO EM MASSA'?", value=True)
        
        if col_sniper != "(Todos)" and vals_sniper:
            df_unificado = df_unificado[df_unificado[col_sniper].astype(str).isin(vals_sniper)]

        if ocultar_enviados and 'status' in df_unificado.columns:
             df_unificado = df_unificado[df_unificado['status'] != "ENVIADO EM MASSA"]

        if not df_unificado.empty:
            if 'nome' in df_unificado.columns:
                df_unificado['label'] = df_unificado['nome'] + " (" + df_unificado['origem'] + ")"
            else:
                df_unificado['label'] = df_unificado['email']

        c1, c2 = st.columns([1, 1])
        
        with c1:
            st.markdown("### SELEÇÃO (FILTRADA)")
            opcoes = df_unificado['label'].tolist() if not df_unificado.empty else []
            if 'status' in df_unificado.columns:
                df_unificado.sort_values(by='status', key=lambda x: x == 'ENVIADO EM MASSA', inplace=True)
                opcoes = df_unificado['label'].tolist()

            sels = st.multiselect("ALVOS", opcoes)
            col_lote, col_info = st.columns([1,1])
            with col_lote:
                modo_lote = st.checkbox("⚡ Enviar Lote de 10?", value=False)
            
            alvos_finais = sels
            if modo_lote:
                alvos_finais = sels[:10]
            
            if len(alvos_finais) > 0:
                st.info(f"{len(alvos_finais)} alvos prontos para envio.")
            
        with c2:
            st.markdown("### MENSAGEM")
            assunto = st.text_input("ASSUNTO", key="ass_int")
            st.caption("Dica: Use {{imagem}} no texto para inserir a imagem no corpo.")
            corpo = st.text_area("CORPO HTML (Use {nome})", height=150, key="body_int")
            file_anexo = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_int")
            
            if st.button("✨ GERAR COM IA (GROQ)"):
                ctx_temp = st.session_state.get('ctx', {}).copy()
                if col_sniper != "(Todos)" and vals_sniper:
                    ctx_temp['segmento_alvo'] = f"{', '.join(vals_sniper)} ({col_sniper})"
                
                sug_a, sug_c = gerar_copy_ia(ctx_temp)
                st.info(f"Assunto: {sug_a}")
                st.code(sug_c)

        if st.button("🚀 DISPARAR NA BASE"):
            # Verifica se o SMTP está carregado na sessão
            if not st.session_state.get('smtp') or not st.session_state['smtp'].get('host'):
                st.error("CONFIGURE O SMTP NA SIDEBAR ANTES DE ENVIAR!")
            elif len(alvos_finais) > saldo_envios:
                st.error(f"SELEÇÃO ({len(alvos_finais)}) MAIOR QUE SALDO ({saldo_envios})")
            else:
                bar = st.progress(0)
                log = st.empty()
                for i, label_sel in enumerate(alvos_finais):
                    if i > 0:
                        wait = random.randint(5, 15)
                        log.warning(f"⏳ RECARREGANDO... {wait}s")
                        time.sleep(wait)
                    
                    tgt_rows = df_unificado[df_unificado['label'] == label_sel]
                    if tgt_rows.empty: continue
                    tgt = tgt_rows.iloc[0]
                    
                    nome_real = tgt.get('nome', 'Parceiro')
                    # FIX: Força string aqui também
                    email_real = str(tgt['email']).strip()
                    item_id_real = tgt.get('id')
                    
                    if not email_real or email_real.lower() == 'nan':
                        continue

                    msg_final = corpo.replace("{nome}", nome_real)
                    
                    res, txt = enviar_email_smtp(st.session_state['smtp'], email_real, assunto, msg_final, file_anexo)
                    registrar_log_envio(token, email_real, assunto, "Enviado" if res else f"Erro: {txt}")
                    
                    if res: 
                        log.success(f"ENVIADO PARA {nome_real}")
                        if item_id_real:
                            try:
                                atualizar_item(token, user_id, item_id_real, {"status": "ENVIADO EM MASSA"})
                            except: pass
                    else: 
                        log.error(f"ERRO {nome_real}: {txt}")
                    
                    bar.progress((i+1)/len(alvos_finais))
                st.balloons()
                time.sleep(2)
                st.rerun()

    with subtab_ext:
        st.markdown("### 📂 UPLOAD DE LISTA (EXCEL .xlsx)")
        up_file = st.file_uploader("ARQUIVO EXCEL (Colunas: nome, email, origem, url...)", type=["xlsx"])
        
        if up_file:
            try:
                df_ext = pd.read_excel(up_file)
                df_ext.columns = [c.lower() for c in df_ext.columns]
                
                if 'email' in df_ext.columns:
                    df_ext = df_ext[df_ext['email'].astype(str).str.contains("@")]
                    st.dataframe(df_ext.head(), use_container_width=True)
                    st.info(f"{len(df_ext)} LEADS ENCONTRADOS")

                    col_imp_btn, col_imp_info = st.columns([1, 2])
                    with col_imp_btn:
                        if st.button("💾 IMPORTAR LISTA PARA O CRM", type="primary"):
                            progress_text = "Importando leads para o banco de dados..."
                            my_bar = st.progress(0, text=progress_text)
                            
                            table_name = get_user_table_name(user_id)
                            base_url = DIRECTUS_URL.rstrip('/')
                            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                            
                            total_imp = len(df_ext)
                            sucesso_imp = 0
                            
                            for idx, row in df_ext.iterrows():
                                payload = {"status": "Novo"}
                                for col in df_ext.columns:
                                    slug = col.strip().lower().replace(' ', '_').replace('ç', 'c').replace('ã', 'a')
                                    val = row[col]
                                    if pd.isna(val): val = ""
                                    payload[slug] = str(val)
                                try:
                                    r_imp = requests.post(f"{base_url}/items/{table_name}", json=payload, headers=headers, verify=False)
                                    if r_imp.status_code in [200, 204]:
                                        sucesso_imp += 1
                                except:
                                    pass
                                my_bar.progress((idx + 1) / total_imp)
                            
                            my_bar.empty()
                            st.success(f"✅ IMPORTAÇÃO CONCLUÍDA! {sucesso_imp} LEADS SALVOS NO CRM.")
                            time.sleep(2)
                            st.rerun()

                    st.markdown("---")

                    assunto_ext = st.text_input("ASSUNTO", key="ass_ext")
                    corpo_ext = st.text_area("CORPO HTML (Use {nome})", height=150, key="body_ext")
                    file_anexo_ext = st.file_uploader("ANEXAR ARQUIVO (IMG vira inline, PDF vira anexo)", key="file_ext")
                    
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
                                email_l = str(row['email']).strip() # FIX: Força string

                                if not email_l or email_l.lower() == 'nan':
                                    continue

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