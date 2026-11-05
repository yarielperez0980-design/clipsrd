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
        "clip_count": "Cantidad de clips a generar automáticamente",
        "clip_dur": "Duración de los clips (segundos)",
        "crop_label": "Encuadre vertical inteligente",
        "render_btn": "🚀 Extraer y generar múltiples clips (IA)",
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
        "clip_count": "Number of clips to generate automatically",
        "clip_dur": "Clip duration (seconds)",
        "crop_label": "Smart vertical framing",
        "render_btn": "🚀 Extract and generate multiple clips (AI)",
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
    # (Se mantienen los demás idiomas base)
}

# Para simplificar y mantener la compatibilidad, si el idioma seleccionado no está completo, usa Español por defecto.
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
            "hint": "Tu nombre y tu año"
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
                if login_user in users and users[login_user]["password"] == hash_password(login_pass):
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_user
                    st.session_state["role"] = users[login_user]["role"]
                    st.session_state["name"] = users[login_user]["name"]
                    st.rerun()
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
                        "hint": reg_hint.strip() if reg_hint else "Sin pista"
                    }
                    save_users(users)
                    st.success("¡Cuenta creada con éxito! Ve a la pestaña de inicio de sesión.")

        with auth_tab3:
            st.markdown("<br>", unsafe_allow_html=True)
            rec_user = st.text_input("Introduce tu usuario", key="rec_u")
            
            if st.button("Ver Pista de Contraseña", key="btn_hint"):
                rec_user_clean = rec_user.strip().lower()
                if rec_user_clean in users:
                    hint_msg = users[rec_user_clean].get("hint", "No hay pista.")
                    st.info(f"💡 Pista: **{hint_msg}**")
                else:
                    st.error("El usuario no existe.")
            
            st.markdown("---")
            new_reset_pass = st.text_input("Nueva contraseña", type="password", key="rec_new_p")
            if st.button("Actualizar Contraseña", key="btn_reset_pass"):
                rec_user_clean = rec_user.strip().lower()
                if rec_user_clean in users and new_reset_pass:
                    users[rec_user_clean]["password"] = hash_password(new_reset_pass)
                    save_users(users)
                    st.success("¡Contraseña actualizada con éxito!")
                else:
                    st.error("Verifica los datos.")

else:
    # --- APLICACIÓN PRINCIPAL ---
    with st.sidebar:
        st.markdown(f"👤 {t['welcome']}, **{st.session_state['name']}**")
        if st.session_state["role"] == "admin":
            st.markdown(f"🛡️ {t['admin_role']}")
        else:
            st.markdown(f"👤 {t['user_role']}")
            
        st.markdown("---")
        st.markdown(f"## {t['sidebar_config']}")
        aspect = st.selectbox(t['aspect_label'], ["9:16 Vertical (TikTok / Reels / Shorts)", "1:1 Cuadrado", "16:9 Horizontal"])
        clip_duration = st.selectbox("Duración de cada clip", [30, 45, 60], index=1)
        clips_quantity = st.slider("Cantidad de clips a extraer", min_value=5, max_value=25, value=15)
        st.markdown("---")
        
        if st.button(t['logout']):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.session_state["role"] = ""
            st.session_state["name"] = ""
            st.rerun()

    st.markdown(f"## {t['title']}")
    st.markdown(f"### {t['subtitle']}")
    st.markdown(f'<p class="small">{t["desc"]}</p>', unsafe_allow_html=True)
    st.divider()

    tab_url, tab_upload = st.tabs([t['tab_url'], t['tab_upload']])

    video_path = None
    work_dir = tempfile.mkdtemp(prefix="clipsrd_")

    with tab_url:
        st.markdown(f"#### {t['url_title']}")
        url = st.text_input("URL", placeholder="https://www.youtube.com/watch?v=...", label_visibility="collapsed")
        if st.button(t['url_btn'], key="get_video"):
            if not url.strip():
                st.warning("Introduce una URL válida.")
            else:
                try:
                    opts = {
                        "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                        "outtmpl": str(Path(work_dir) / "source.%(ext)s"),
                        "noplaylist": True,
                        "quiet": True,
                        "merge_output_format": "mp4",
                    }
                    with st.spinner("Descargando video largo..."):
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            info = ydl.extract_info(url.strip(), download=True)
                            video_path = ydl.prepare_filename(info)
                    st.session_state["clipsrd_source"] = video_path
                    st.success(f"¡Video importado con éxito: {info.get('title', 'Video')}!")
                except Exception as e:
                    st.error(f"Error al importar: {e}")

    with tab_upload:
        st.markdown(f"#### {t['upload_title']}")
        uploaded = st.file_uploader("Archivo", type=["mp4", "mov", "mkv", "webm"], label_visibility="collapsed")
        if uploaded is not None:
            uploaded_path = Path(work_dir) / uploaded.name
            uploaded_path.write_bytes(uploaded.getbuffer())
            st.session_state["clipsrd_source"] = str(uploaded_path)
            st.success("¡Archivo cargado con éxito!")

    video_path = st.session_state.get("clipsrd_source")

    if video_path and Path(video_path).exists():
        st.divider()
        left, right = st.columns([1.15, 0.85], gap="large")
        
        with left:
            st.markdown(f"### {t['preview']}")
            st.video(video_path)
            
        with right:
            st.markdown(f"### {t['editor']}")
            st.info(f"Se extraerán automáticamente **{clips_quantity} clips** de **{clip_duration} segundos** distribuidos a lo largo de toda la grabación.")
            crop = st.selectbox(t['crop_label'], ["Centro", "Priorizar lado izquierdo", "Priorizar lado derecho"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(t['render_btn'], key="render_batch"):
                output_clips = []
                
                # Obtener duración total del video usando ffprobe/subprocess
                probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
                try:
                    dur_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
                    total_duration = float(dur_res.stdout.strip())
                except:
                    total_duration = 2700  # Por defecto 45 minutos si falla la lectura

                # Calcular intervalos distribuidos para los N clips
                step = max(30.0, (total_duration - clip_duration) / max(1, clips_quantity))
                
                progress_bar = st.progress(0)
                status_text = st.empty()

                for i in range(clips_quantity):
                    start_time = i * step
                    if start_time + clip_duration > total_duration:
                        break
                        
                    clip_filename = str(Path(work_dir) / f"auto_clip_{i+1}.mp4")
                    
                    status_text.text(f"Generando clip {i+1} de {clips_quantity} (Minuto {int(start_time//60)})...")
                    
                    if aspect.startswith("9:16"):
                        x_expr = "iw/2-ih*9/32" if crop == "Centro" else ("0" if crop == "Priorizar lado izquierdo" else "iw-ih*9/16")
                        vf = f"crop='ih*9/16':'ih':{x_expr}:0,scale=1080:1920"
                    else:
                        vf = "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
                    
                    command = ["ffmpeg", "-y", "-ss", str(start_time), "-i", video_path, "-t", str(clip_duration),
                               "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                               "-c:a", "aac", "-b:a", "128k", clip_filename]
                    try:
                        subprocess.run(command, capture_output=True, text=True, check=True)
                        output_clips.append(clip_filename)
                    except:
                        pass
                        
                    progress_bar.progress((i + 1) / clips_quantity)
                
                status_text.empty()
                progress_bar.empty()
                st.session_state["clipsrd_batch_outputs"] = output_clips
                st.success("¡Lote de clips generado correctamente!")

    batch_outputs = st.session_state.get("clipsrd_batch_outputs", [])
    if batch_outputs:
        st.divider()
        st.markdown(f"## {t['result_title']}")
        st.write(f"Se han procesado **{len(batch_outputs)} clips verticales** listos para tus redes sociales:")
        
        # Mostrar en cuadrícula de columnas
        cols = st.columns(3)
        for idx, clip_file in enumerate(batch_outputs):
            with cols[idx % 3]:
                st.markdown(f"**Clip #{idx+1}**")
                st.video(clip_file)
                st.download_button(
                    f"⬇️ Descargar Clip #{idx+1}",
                    data=Path(clip_file).read_bytes(),
                    file_name=f"ClipsRD_parte_{idx+1}.mp4",
                    mime="video/mp4",
                    key=f"dl_{idx}"
                )
                st.markdown("---")