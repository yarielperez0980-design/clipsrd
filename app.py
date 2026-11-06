import streamlit as st
import yt_dlp
import subprocess
import tempfile
import json
from pathlib import Path
import hashlib

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Clips RD AI Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS VISUALES ESTILO CHGPT / MODERNO ---
st.markdown("""
<style>
/* Fondo general estilo ChatGPT Dark Mode */
.stApp {
    background-color: #212121;
    color: #ececec;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Sidebar oscuro y limpio */
[data-testid="stSidebar"] {
    background-color: #171717;
    border-right: 1px solid #2f2f2f;
}

[data-testid="stSidebar"] * {
    color: #ececec !important;
}

/* Títulos y textos */
h1, h2, h3 {
    color: #ffffff !important;
    font-weight: 600;
}

/* Botones principales estilo GPT */
div.stButton > button {
    background-color: #2f2f2f;
    color: #ffffff;
    border: 1px solid #424242;
    border-radius: 8px;
    font-weight: 500;
    padding: 0.5rem 1rem;
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    background-color: #3f3f3f;
    border-color: #525252;
}

/* Botón de acción principal (Primary) */
div.stButton > button[kind="primary"], .stDownloadButton > button {
    background-color: #ffffff !important;
    color: #212121 !important;
    border: none !important;
    font-weight: 600;
}

div.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    background-color: #e0e0e0 !important;
}

/* Entradas de texto estilo chat box */
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #2f2f2f !important;
    border: 1px solid #424242 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

/* Contenedores y tarjetas */
.gpt-card {
    background-color: #2f2f2f;
    border: 1px solid #3f3f3f;
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 15px;
}
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE BASE DE DATOS LOCAL (USUARIOS Y SEGURIDAD) ---
USER_DB = Path("users_db.json")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    default_admin = {
        "yariel": {
            "password": hash_password("YarielY0408$"),
            "role": "admin",
            "name": "Yariel Pérez",
            "approved": True
        }
    }
    if USER_DB.exists():
        try:
            with open(USER_DB, "r") as f:
                data = json.load(f)
                data["yariel"] = default_admin["yariel"]
                return data
        except:
            return default_admin
    else:
        save_users(default_admin)
        return default_admin

def save_users(users_dict):
    with open(USER_DB, "w") as f:
        json.dump(users_dict, f, indent=4)

users = load_users()

# Inicializar estados de sesión
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "name" not in st.session_state:
    st.session_state["name"] = ""

# --- FLUJO DE AUTENTICACIÓN (PANTALLA DE ACCESO SEGURA) ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="font-size: 2rem; margin-bottom: 5px;">⚡ Clips RD Studio</h1>
                <p style="color: #9e9e9e; font-size: 0.9rem;">Sistema Seguro de Generación Inteligente</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            u_input = st.text_input("Usuario", key="l_user")
            p_input = st.text_input("Contraseña", type="password", key="l_pass")
            
            if st.button("Acceder al Sistema", use_container_width=True, type="primary"):
                clean_u = u_input.strip().lower()
                if clean_u in users and users[clean_u]["password"] == hash_password(p_input):
                    if users[clean_u].get("approved", False):
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = clean_u
                        st.session_state["role"] = users[clean_u]["role"]
                        st.session_state["name"] = users[clean_u]["name"]
                        st.rerun()
                    else:
                        st.warning("⏳ Tu cuenta está pendiente de aprobación por seguridad del administrador.")
                else:
                    st.error("⚠️ Credenciales inválidas o acceso no autorizado.")
                    
        with tab_reg:
            st.markdown("<br>", unsafe_allow_html=True)
            r_name = st.text_input("Nombre completo", key="r_name")
            r_user = st.text_input("Nombre de usuario nuevo", key="r_user")
            r_pass = st.text_input("Contraseña segura", type="password", key="r_pass")
            
            if st.button("Solicitar Registro", use_container_width=True):
                clean_r = r_user.strip().lower()
                if not r_name or not clean_r or not r_pass:
                    st.warning("Completa todos los campos obligatorios.")
                elif clean_r == "yariel":
                    st.error("Nombre reservado.")
                elif clean_r in users:
                    st.error("El usuario ya existe.")
                else:
                    users[clean_r] = {
                        "password": hash_password(r_pass),
                        "role": "user",
                        "name": r_name.strip(),
                        "approved": False
                    }
                    save_users(users)
                    st.success("¡Solicitud enviada! El administrador debe admitirte para poder entrar.")

else:
    # --- APLICACIÓN PRINCIPAL (ESTILO SIDEBAR TIPO CHATGPT) ---
    with st.sidebar:
        st.markdown(f"### ⚡ Workspace")
        st.markdown(f"👤 **{st.session_state['name']}**")
        role_badge = "🛡️ Administrador" if st.session_state["role"] == "admin" else "👤 Operador"
        st.markdown(f"<span style='color: #9e9e9e; font-size: 0.8rem;'>{role_badge}</span>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🎛️ Parámetros de Comando")
        
        # Comandos / Opciones avanzadas
        command_mode = st.selectbox("Modo de Operación", ["🎬 Generación Masiva de Clips", "🔗 Analizador de Enlace Directo", "📁 Gestor de Archivos Locales"])
        aspect_ratio = st.selectbox("Relación de Aspecto", ["9:16 Vertical (TikTok/Shorts)", "1:1 Cuadrado", "16:9 Horizontal"])
        clip_sec = st.slider("Duración por Clip (seg)", 15, 60, 30)
        total_clips = st.slider("Cantidad objetivo de clips", 5, 20, 10)
        
        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # Interfaz Central Principal
    st.markdown("## 🤖 Clips RD — Command Center")
    st.markdown("<p style='color: #9e9e9e;'>Panel de control inteligente para procesamiento masivo de video mediante comandos seguros.</p>", unsafe_allow_html=True)
    st.divider()

    # Panel exclusivo de administración para aprobar usuarios
    if st.session_state["role"] == "admin":
        with st.expander("🛡️ Panel de Seguridad y Auditoría (Aprobación de Usuarios)", expanded=False):
            pending = [u for u, data in users.items() if not data.get("approved", False) and u != "yariel"]
            if not pending:
                st.info("No hay solicitudes de acceso pendientes de aprobación.")
            else:
                for p_u in pending:
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        st.text(f"Usuario: {p_u} ({users[p_u]['name']})")
                    with c2:
                        if st.button(f"✅ Aprobar", key=f"app_{p_u}"):
                            users[p_u]["approved"] = True
                            save_users(users)
                            st.rerun()
                    with c3:
                        if st.button(f"❌ Denegar", key=f"del_{p_u}"):
                            del users[p_u]
                            save_users(users)
                            st.rerun()
        st.markdown("")

    # --- ZONA DE ENTRADA TIPO CHAT / COMANDOS ---
    st.markdown("### 📥 Inserción de Fuente")
    input_source_type = st.radio("Selecciona método de entrada:", ["Pegar URL de YouTube / Plataforma", "Subir Archivo Local"], horizontal=True)

    video_source_path = None
    workspace_dir = tempfile.mkdtemp(prefix="gpt_clips_")

    if "Pegar URL" in input_source_type:
        url_query = st.text_input("Comando / URL del recurso", placeholder="Ej. /url https://www.youtube.com/watch?v=...")
        if st.button("🚀 Ejecutar Análisis de URL", type="primary"):
            if not url_query.strip():
                st.warning("Introduce una URL válida para procesar.")
            else:
                try:
                    ydl_opts = {
                        "format": "best/bestvideo+bestaudio",
                        "outtmpl": str(Path(workspace_dir) / "source.%(ext)s"),
                        "noplaylist": True,
                        "quiet": True,
                        "merge_output_format": "mp4",
                        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
                        "nocheckcertificate": True,
                        "geo_bypass": True,
                    }
                    if Path("cookies.txt").exists():
                        ydl_opts["cookiefile"] = "cookies.txt"
                    }
                    if Path("cookies.txt").exists():
                        ydl_opts["cookiefile"] = "cookies.txt"

                    with st.spinner("⚡ Conectando de forma segura con el servidor y extrayendo recurso..."):
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            meta = ydl.extract_info(url_query.strip(), download=True)
                            video_source_path = ydl.prepare_filename(meta)
                    st.session_state["active_video"] = video_source_path
                    st.success(f"¡Recurso vinculado con éxito: {meta.get('title', 'Video')}!")
                except Exception as ex:
                    st.error(f"Error crítico en el comando de extracción: {ex}")
    else:
        uploaded_file = st.file_uploader("Sube tu archivo de video local", type=["mp4", "mov", "mkv"])
        if uploaded_file is not None:
            dest_file = Path(workspace_dir) / uploaded_file.name
            dest_file.write_bytes(uploaded_file.getbuffer())
            st.session_state["active_video"] = str(dest_file)
            st.success("¡Archivo cargado localmente con éxito!")

    video_source_path = st.session_state.get("active_video")

    # --- PROCESAMIENTO Y GENERACIÓN DE CLIPS ---
    if video_source_path and Path(video_source_path).exists():
        st.divider()
        col_prev, col_actions = st.columns([1.1, 0.9], gap="large")
        
        with col_prev:
            st.markdown("#### 📺 Vista Previa del Recurso")
            st.video(video_source_path)
            
        with col_actions:
            st.markdown("#### ⚙️ Consola de Recorte Masivo")
            st.info(f"Se generarán **{total_clips} clips** automáticos de **{clip_sec} segundos** aplicando el formato seleccionado.")
            
            if st.button("⚡ Iniciar Procesamiento por Lotes", type="primary", use_container_width=True):
                rendered_files = []
                
                # Obtener duración total con ffprobe
                probe_process = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_source_path]
                try:
                    dur_res = subprocess.run(probe_process, capture_output=True, text=True, check=True)
                    video_duration = float(dur_res.stdout.strip())
                except:
                    video_duration = 1800

                time_step = max(20.0, (video_duration - clip_sec) / max(1, total_clips))
                progress_bar = st.progress(0)
                status_box = st.empty()

                for idx in range(total_clips):
                    start_sec = idx * time_step
                    if start_sec + clip_sec > video_duration:
                        break
                        
                    output_filename = str(Path(workspace_dir) / f"clip_result_{idx+1}.mp4")
                    status_box.text(f"Procesando clip {idx+1} de {total_clips} (Minuto {int(start_sec//60)})...")
                    
                    if "9:16" in aspect_ratio:
                        vf_filter = "crop='ih*9/16':'ih':iw/2-ih*9/32:0,scale=1080:1920"
                    else:
                        vf_filter = "scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2"
                    
                    ffmpeg_command = [
                        "ffmpeg", "-y", "-ss", str(start_sec), "-i", video_source_path, "-t", str(clip_sec),
                        "-vf", vf_filter, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                        "-c:a", "aac", "-b:a", "128k", output_filename
                    ]
                    try:
                        subprocess.run(ffmpeg_command, capture_output=True, text=True, check=True)
                        rendered_files.append(output_filename)
                    except:
                        pass
                        
                    progress_bar.progress((idx + 1) / total_clips)
                
                status_box.empty()
                progress_bar.empty()
                st.session_state["rendered_clips"] = rendered_files
                st.success("¡Lote completado con éxito!")

    # --- SALIDA Y DESCARGA DE RESULTADOS ---
    final_clips_list = st.session_state.get("rendered_clips", [])
    if final_clips_list:
        st.divider()
        st.markdown("### 🚀 Resultados Listos para Descargar")
        st.write(f"Se han obtenido **{len(final_clips_list)} clips optimizados** para su distribución:")
        
        grid_cols = st.columns(3)
        for i, clip_file_path in enumerate(final_clips_list):
            with grid_cols[i % 3]:
                st.markdown(f"**Clip #{i+1}**")
                st.video(clip_file_path)
                st.download_button(
                    f"⬇️ Descargar Clip #{i+1}",
                    data=Path(clip_file_path).read_bytes(),
                    file_name=f"ClipsRD_GPT_part_{i+1}.mp4",
                    mime="video/mp4",
                    key=f"dl_gpt_{i}"
                )
                st.markdown("---")
