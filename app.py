import streamlit as st
import yt_dlp
import subprocess
import tempfile
import json
from pathlib import Path
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Clips RD", page_icon="🎬", layout="wide")

# --- DICCIONARIO DE TRADUCCIONES (MULTIDIOMA) ---
LANGUAGES = {
    "Español": {
        "title": "🎬 Clips RD",
        "subtitle": "Generador Masivo de Clips Inteligentes para Redes",
        "desc": "Estudio de recorte masivo • Relación 9:16 • Alta Definición MP4 (1080 × 1920)",
        "sidebar_config": "⚙️ Configuración Masiva",
        "lang_label": "🌐 Idioma / Language",
        "aspect_label": "Formato de salida",
        "dur_label": "Duración de cada clip",
        "welcome": "Hola",
        "admin_role": "🛡️ Rol: Propietario (Administrador)",
        "user_role": "👤 Rol: Usuario Estándar",
        "logout": "Cerrar sesión",
        "tab_url": "🔗 Importar desde URL",
        "tab_upload": "📁 Subir archivo local",
        "url_title": "Pega el enlace de la plataforma compatible",
        "url_btn": "⬇️ Obtener y analizar video",
        "upload_title": "Sube tu propio archivo de video",
        "preview": "👀 Vista previa del material",
        "editor": "✂️ Generador Automático de Clips en Lote",
        "clip_dur": "Duración de los clips (segundos)",
        "crop_label": "Encuadre vertical inteligente",
        "render_btn": "🚀 Extraer y generar múltiples clips",
        "success_render": "¡Proceso masivo completado con éxito!",
        "result_title": "🚀 Tus Clips Están Listos para Descargar",
        "login_title": "Clips RD - Acceso",
        "login_sub": "Plataforma de Recorte Masivo",
        "tab_login": "🔑 Iniciar Sesión",
        "tab_reg": "📝 Registrarse",
        "tab_rec": "🔄 Recuperar Contraseña",
        "user": "Usuario",
        "pass": "Contraseña",
        "enter": "Entrar",
        "name_full": "Nombre completo",
        "new_user": "Nombre de usuario nuevo",
        "new_pass": "Contraseña nueva",
        "create_acc": "Crear Cuenta"
    },
    "English": {
        "title": "🎬 Clips RD",
        "subtitle": "Massive Smart Clip Generator for Social Media",
        "desc": "Mass cutting studio • 9:16 Ratio • High Definition MP4 (1080 × 1920)",
        "sidebar_config": "⚙️ Mass Settings",
        "lang_label": "🌐 Language",
        "aspect_label": "Output format",
        "dur_label": "Clip duration",
        "welcome": "Hello",
        "admin_role": "🛡️ Role: Owner (Administrator)",
        "user_role": "👤 Role: Standard User",
        "logout": "Log out",
        "tab_url": "🔗 Import from URL",
        "tab_upload": "📁 Upload local file",
        "url_title": "Paste supported platform link",
        "url_btn": "⬇️ Fetch and analyze video",
        "upload_title": "Upload your own video file",
        "preview": "👀 Material preview",
        "editor": "✂️ Automated Batch Clip Generator",
        "clip_dur": "Clip duration (seconds)",
        "crop_label": "Smart vertical framing",
        "render_btn": "🚀 Extract and generate multiple clips",
        "success_render": "Massive processing completed successfully!",
        "result_title": "🚀 Your Clips Are Ready to Download",
        "login_title": "Clips RD - Access",
        "login_sub": "Mass Cutting Platform",
        "tab_login": "🔑 Log In",
        "tab_reg": "📝 Sign Up",
        "tab_rec": "🔄 Recover Password",
        "user": "Username",
        "pass": "Password",
        "enter": "Enter",
        "name_full": "Full name",
        "new_user": "New username",
        "new_pass": "New password",
        "create_acc": "Create Account"
    }
}

# --- DISEÑO Y ESTÉTICA (UI/UX) ---
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 15% 0%, #1e1138 0, #0b0b12 40%, #050508 100%);
    color: #f5f3ff;
}
[data-testid="stSidebar"] {
    background: #0f0e17;
    border-right: 1px solid #2a2242;
}
h1, h2, h3 {
    color: #f7f2ff !important;
    font-family: 'Inter', sans-serif;
    letter-spacing: -0.5px;
}
div.stButton > button, div.stDownloadButton > button {
    background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%);
    color: white;
    border: none;
    border-radius: 14px;
    font-weight: 600;
    min-height: 3rem;
    box-shadow: 0 4px 20px rgba(139, 92, 246, 0.35);
    transition: all 0.3s ease;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {
    background: linear-gradient(135deg, #9333ea 0%, #7c3aed 100%);
    border: 1px solid #c4b5fd;
    box-shadow: 0 6px 25px rgba(139, 92, 246, 0.5);
    color: white;
    transform: translateY(-1px);
}
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #161325 !important;
    border: 1px solid #322852 !important;
    color: #f5f3ff !important;
    border-radius: 10px !important;
}
.small {
    color: #9ca3af;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE USUARIOS LOCAL (JSON) ---
USER_DB = Path("users_db.json")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    default_users = {
        "yariel": {
            "password": hash_password("YarielY0408$"),
            "role": "admin",
            "name": "Yariel Pérez",
            "hint": "Tu nombre y tu año",
            "approved": True
        }
    }
    if USER_DB.exists():
        try:
            with open(USER_DB, "r") as f:
                data = json.load(f)
                data["yariel"] = default_users["yariel"]
                return data
        except:
            return default_users
    else:
        save_users(default_users)
        return default_users

def save_users(users_dict):
    with open(USER_DB, "w") as f:
        json.dump(users_dict, f, indent=4)

users = load_users()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "name" not in st.session_state:
    st.session_state["name"] = ""

with st.sidebar:
    selected_lang = st.selectbox("🌐 Idioma / Language", list(LANGUAGES.keys()), index=0)

t = LANGUAGES.get(selected_lang, LANGUAGES["Español"])

# --- PANTALLA DE AUTENTICACIÓN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown(f"""
            <div style="background: rgba(25, 22, 38, 0.9); padding: 30px; border-radius: 20px; border: 1px solid #36285c; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
                <h2 style="text-align: center; margin-bottom: 0px;">{t['title']}</h2>
                <p style="text-align: center; color: #a78bfa; font-size: 0.85rem;">{t['login_sub']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        auth_tab1, auth_tab2, auth_tab3 = st.tabs([t['tab_login'], t['tab_reg'], t['tab_rec']])
        
        with auth_tab1:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input(t['user'], key="login_u")
            login_pass = st.text_input(t['pass'], type="password", key="login_p")
            
            if st.button(t['enter'], key="btn_login"):
                login_user_clean = login_user.strip().lower()
                if login_user_clean in users and users[login_user_clean]["password"] == hash_password(login_pass):
                    if users[login_user_clean].get("approved", False):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = login_user_clean
                        st.session_state["role"] = users[login_user_clean]["role"]
                        st.session_state["name"] = users[login_user_clean]["name"]
                        st.rerun()
                    else:
                        st.warning("⏳ Tu cuenta está pendiente de aprobación por el administrador.")
                else:
                    st.error("⚠️ Usuario o contraseña incorrectos.")
                    
        with auth_tab2:
            st.markdown("<br>", unsafe_allow_html=True)
            reg_name = st.text_input(t['name_full'], key="reg_n")
            reg_user = st.text_input(t['new_user'], key="reg_u")
            reg_pass = st.text_input(t['new_pass'], type="password", key="reg_p")
            reg_hint = st.text_input("Pista para recordar contraseña", key="reg_h", placeholder="Ej. Mi primer perro")
            
            if st.button(t['create_acc'], key="btn_reg"):
                reg_user_clean = reg_user.strip().lower()
                if not reg_name or not reg_user_clean or not reg_pass:
                    st.warning("Por favor, completa todos los campos.")
                elif reg_user_clean == "yariel":
                    st.error("Este nombre de usuario está reservado para el propietario.")
                elif reg_user_clean in users:
                    st.error("El nombre de usuario ya existe.")
                else:
                    users[reg_user_clean] = {
                        "password": hash_password(reg_pass),
                        "role": "user",
                        "name": reg_name.strip(),
                        "hint": reg_hint.strip() if reg_hint else "Sin pista",
                        "approved": False
                    }
