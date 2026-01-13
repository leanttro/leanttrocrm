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
import urllib3
import json

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="LEANTTRO CRM", layout="wide", page_icon="⚡")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ["STREAMLIT_CLIENT_SHOW_ERROR_DETAILS"] = "false"

# --- CSS VISUAL (BASEADO NO INDEX.HTML) ---
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

</style>
""", unsafe_allow_html=True)

# --- VARS ---
DIRECTUS_URL = os.getenv("DIRECTUS_URL", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") 

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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
    
    r = requests.get(f"{base_url}/collections/{table_name}", headers=headers, verify=False)
    if r.status_code == 200: return True, "CRM Ready"
    
    schema = {
        "collection": table_name,
        "schema": {},
        "meta": {"icon": "rocket", "note": "Leanttro CRM Table"}
    }
    requests.post(f"{base_url}/collections", json=schema, headers=headers, verify=False)
    
    campos_padrao = [
        {"field": "nome", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "person"}},
        {"field": "empresa", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "domain"}},
        {"field": "email", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "email"}},
        {"field": "telefone", "type": "string", "meta": {"interface": "input", "width": "half", "icon": "phone"}},
        {"field": "status", "type": "string", "meta": {"interface": "select-dropdown", "options": {"choices": [{"text": "NOVO", "value": "Novo"}, {"text": "QUENTE", "value": "Quente"}, {"text": "CLIENTE", "value": "Cliente"}]}}},
        {"field": "obs", "type": "text", "meta": {"interface": "input-multiline"}}
    ]
    
    for campo in campos_padrao:
        requests.post(f"{base_url}/fields/{table_name}", json=campo, headers=headers, verify=False)
        
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
                cols = ['id', 'nome', 'empresa', 'email', 'status'] + [c for c in df.columns if c not in ['id', 'nome', 'empresa', 'email', 'status']]
                return df[cols]
    except: pass
    return pd.DataFrame(columns=["nome", "empresa", "email", "status"])

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
        return True, "OK"
    except Exception as e: return False, str(e)

def gerar_copy_ia(ctx):
    if not GEMINI_API_KEY: return "Configure a API Key", "..."
    prompt = f"Escreva um email curto de vendas B2B. Empresa: {ctx.get('empresa')}. Vende: {ctx.get('descricao')}. Tom: Agressivo e direto."
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        res = model.generate_content(prompt)
        return "Proposta Comercial", res.text
    except: return "Erro", "Erro IA"

# =========================================================
#  INTERFACE
# =========================================================

if 'token' not in st.session_state:
    c1, c2, c3 = st.columns([1,1,1])
    with c2:
        render_header()
        st.markdown("<p style='text-align:center; color:#888'>// ACESSO RESTRITO</p>", unsafe_allow_html=True)
        email = st.text_input("E-MAIL")
        senha = st.text_input("SENHA", type="password")
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            try:
                r = requests.post(f"{DIRECTUS_URL}/auth/login", json={"email": email, "password": senha}, verify=False)
                if r.status_code == 200:
                    st.session_state['token'] = r.json()['data']['access_token']
                    u = requests.get(f"{DIRECTUS_URL}/users/me", headers={"Authorization": f"Bearer {st.session_state['token']}"}, verify=False)
                    st.session_state['user'] = u.json()['data']
                    st.rerun()
                else:
                    st.error("ACESSO NEGADO")
            except: st.error("ERRO DE CONEXÃO")
    st.stop()

token = st.session_state['token']
user = st.session_state['user']
user_id = user['id']

if 'setup_ok' not in st.session_state:
    inicializar_crm_usuario(token, user_id)
    st.session_state['setup_ok'] = True

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"<h3 style='color:var(--neon)'>// USER: {user.get('first_name').upper()}</h3>", unsafe_allow_html=True)
    
    if st.button("LOGOUT / SAIR"):
        st.session_state.clear()
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

    with st.expander("🤖 DADOS DA EMPRESA"):
        en = st.text_input("NOME EMPRESA", value="Minha Agência")
        ed = st.text_area("O QUE VENDE?", value="Sites de alta conversão")
        if st.button("SALVAR CONTEXTO"):
            st.session_state['ctx'] = {'empresa': en, 'descricao': ed}
            st.success("SALVO")

    with st.expander("📧 SMTP CONFIG"):
        h = st.text_input("HOST", "smtp.gmail.com")
        p = st.number_input("PORT", 587)
        u = st.text_input("USER")
        pw = st.text_input("PASS", type="password")
        if st.button("CONECTAR SMTP"):
            st.session_state['smtp'] = {'host': h, 'port': p, 'user': u, 'pass': pw}
            st.success("CONECTADO")

# --- MAIN ---
render_header()
df = carregar_dados(token, user_id)

k1, k2, k3 = st.columns(3)
k1.metric("TOTAL LEADS", len(df))
k2.metric("NOVOS", len(df[df['status'] == 'Novo']) if 'status' in df.columns else 0)
k3.metric("CONVERSÃO", "0%")

st.markdown("<br>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["/// BASE DE LEADS", "/// MODO SNIPER (DISPARO)"])

with tab1:
    edited = st.data_editor(df, num_rows="dynamic", use_container_width=True, key="editor")
    if st.button("💾 SALVAR ALTERAÇÕES NA BASE"):
        chg = st.session_state["editor"]
        # Lógica simplificada de salvamento
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

with tab2:
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown("### 1. SELEÇÃO")
        leads = df[df['email'].str.contains("@", na=False)] if 'email' in df.columns else pd.DataFrame()
        sels = st.multiselect("SELECIONE OS ALVOS", leads['nome'].tolist() if not leads.empty else [])
        
    with c2:
        st.markdown("### 2. MENSAGEM")
        assunto = st.text_input("ASSUNTO")
        corpo = st.text_area("CORPO HTML (Use {nome})", height=150)
        if st.button("✨ GERAR COM IA"):
            sug_a, sug_c = gerar_copy_ia(st.session_state.get('ctx', {}))
            st.info(f"Assunto: {sug_a}")
            st.code(sug_c)

    if st.button("🚀 INICIAR DISPARO EM MASSA"):
        if not st.session_state.get('smtp'):
            st.error("CONFIGURE O SMTP NA SIDEBAR")
        else:
            bar = st.progress(0)
            log = st.empty()
            for i, nome in enumerate(sels):
                if i > 0:
                    wait = random.randint(15, 45)
                    log.warning(f"⏳ ESPERANDO {wait}s (ANTI-SPAM)...")
                    time.sleep(wait)
                
                tgt = leads[leads['nome'] == nome].iloc[0]
                msg = corpo.replace("{nome}", tgt['nome'])
                res, txt = enviar_email_smtp(st.session_state['smtp'], tgt['email'], assunto, msg)
                
                if res: log.success(f"ENVIADO PARA {nome}")
                else: log.error(f"ERRO {nome}: {txt}")
                bar.progress((i+1)/len(sels))
            st.balloons()