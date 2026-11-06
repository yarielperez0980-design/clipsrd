import os
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
.stApp {
    background-color: #212121;
    color: #ececec;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
[data-testid="stSidebar"] {
    background-color: #171717;
    border-right: 1px solid #2f2f2f;
}
[data-testid="stSidebar"] * {
    color: #ececec !important;
}
h1, h2, h3 {
    color: #ffffff !important;
    font-weight: 600;
}
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
div.stButton > button[kind="primary"], .stDownloadButton > button {
    background-color: #ffffff !important;
    color: #212121 !important;
    border: none !important;
    font-weight: 600;
}
div.stButton > button[kind="primary"]:hover, .stDownloadButton > button:hover {
    background-color: #e0e0e0 !important;
}
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #2f2f2f !important;
    border: 1px solid #424242 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# --- GESTIÓN DE BASE DE DATOS LOCAL (USUARIOS Y SEGURIDAD) ---
USER_DB = Path("users_db.json")

# La contraseña del administrador ya NO está en el código.
# Se lee de la variable de entorno CLIPS_ADMIN_PASSWORD.
ADMIN_PASSWORD = os.environ.get("CLIPS_ADMIN_PASSWORD", "")


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def load_users():
    default_admin = {
        "yariel": {
            "password": hash_password(ADMIN_PASSWORD) if ADMIN_PASSWORD else None,
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
        except Exception:
            return default_admin
    else:
        save_users(default_admin)
        return default_admin


def save_users(users_dict):
    with open(USER_DB, "w") as f:
        json.dump(users_dict, f, indent=4)


users = load_users()

for key, default in (("logged_in", False), ("username", ""), ("role", ""), ("name", "")):
    if key not in st.session_state:
        st.session_state[key] = default

# Carpeta de trabajo estable durante toda la sesión (antes se creaba una nueva en cada interacción)
if "workspace_dir" not in st.session_state:
    st.session_state["workspace_dir"] = tempfile.mkdtemp(prefix="gpt_clips_")
workspace_dir = st.session_state["workspace_dir"]


def download_video(url, dest_dir):
    """Descarga el video con yt-dlp y devuelve (ruta_mp4, título)."""
    ydl_opts = {
        # Acepta cualquier mejor video + mejor audio; si no hay, cae a un formato único.
        "format": "bv*+ba/b",
        "outtmpl": str(Path(dest_dir) / "source.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "merge_output_format": "mp4",
        "nocheckcertificate": True,
        "geo_bypass": True,
    }
    if Path("cookies.txt").exists():
        ydl_opts["cookiefile"] = "cookies.txt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        meta = ydl.extract_info(url, download=True)

        # Ruta real del archivo final (después de fusionar video + audio)
        filepath = None
        downloads = meta.get("requested_downloads") or []
        if downloads:
            filepath = downloads[0].get("filepath")
        if not filepath or not Path(filepath).exists():
            filepath = str(Path(ydl.prepare_filename(meta)).with_suffix(".mp4"))
        if not Path(filepath).exists():
            candidates = sorted(Path(dest_dir).glob("source.*"))
            if candidates:
                filepath = str(candidates[0])

    return filepath, meta.get("title", "Video")


# --- FLUJO DE AUTENTICACIÓN ---
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

        if not ADMIN_PASSWORD:
            st.warning(
                "La cuenta de administrador está desactivada porque falta la variable de entorno "
                "CLIPS_ADMIN_PASSWORD. Defínela y reinicia la app."
            )

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
    # --- APLICACIÓN PRINCIPAL ---
    with st.sidebar:
        st.markdown("### ⚡ Workspace")
        st.markdown(f"👤 **{st.session_state['name']}**")
        role_badge = "🛡️ Administrador" if st.session_state["role"] == "admin" else "👤 Operador"
        st.markdown(f"<span style='color: #9e9e9e; font-size: 0.8rem;'>{role_badge}</span>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### 🎛️ Parámetros de Comando")

        aspect_ratio = st.selectbox("Relación de Aspecto", ["9:16 Vertical (TikTok/Shorts)", "1:1 Cuadrado", "16:9 Horizontal"])
        clip_sec = st.slider("Duración por Clip (seg)", 15, 60, 30)
        total_clips = st.slider("Cantidad objetivo de clips", 5, 20, 10)

        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    st.markdown("## 🤖 Clips RD — Command Center")
    st.markdown("<p style='color: #9e9e9e;'>Panel de control inteligente para procesamiento masivo de video mediante comandos seguros.</p>", unsafe_allow_html=True)
    st.divider()

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
                        if st.button("✅ Aprobar", key=f"app_{p_u}"):
                            users[p_u]["approved"] = True
                            save_users(users)
                            st.rerun()
                    with c3:
                        if st.button("❌ Denegar", key=f"del_{p_u}"):
                            del users[p_u]
                            save_users(users)
                            st.rerun()
        st.markdown("")

    st.markdown("### 📥 Inserción de Fuente")
    input_source_type = st.radio("Selecciona método de entrada:", ["Pegar URL de YouTube / Plataforma", "Subir Archivo Local"], horizontal=True)

    if "Pegar URL" in input_source_type:
        url_query = st.text_input("Comando / URL del recurso", placeholder="Ej. https://www.youtube.com/watch?v=...")
        if st.button("🚀 Ejecutar Análisis de URL", type="primary"):
            if not url_query.strip():
                st.warning("Introduce una URL válida para procesar.")
            else:
                try:
                    with st.spinner("⚡ Conectando de forma segura con el servidor y extrayendo recurso..."):
                        video_path, video_title = download_video(url_query.strip(), workspace_dir)
                    if video_path and Path(video_path).exists():
                        st.session_state["active_video"] = video_path
                        st.session_state["rendered_clips"] = []
                        st.success(f"¡Recurso vinculado con éxito: {video_title}!")
                    else:
                        st.error("La descarga terminó pero no se encontró el archivo de video.")
                except Exception as ex:
                    st.error(f"Error en la extracción: {ex}")
                    st.caption(
                        "Sugerencias: actualiza yt-dlp (`pip install -U yt-dlp`), verifica que ffmpeg esté en el PATH, "
                        "instala Deno si YouTube lo exige, o coloca un cookies.txt junto a este archivo."
                    )
    else:
        uploaded_file = st.file_uploader("Sube tu archivo de video local", type=["mp4", "mov", "mkv"])
        if uploaded_file is not None:
            dest_file = Path(workspace_dir) / uploaded_file.name
            dest_file.write_bytes(uploaded_file.getbuffer())
            st.session_state["active_video"] = str(dest_file)
            st.success("¡Archivo cargado localmente con éxito!")

    video_source_path = st.session_state.get("active_video")

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

                probe_process = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", video_source_path]
                try:
                    dur_res = subprocess.run(probe_process, capture_output=True, text=True, check=True)
                    video_duration = float(dur_res.stdout.strip())
                except Exception:
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
                    elif "1:1" in aspect_ratio:
                        vf_filter = "crop='min(iw,ih)':'min(iw,ih)',scale=1080:1080"
                    else:
                        vf_filter = "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

                    ffmpeg_command = [
                        "ffmpeg", "-y", "-ss", str(start_sec), "-i", video_source_path, "-t", str(clip_sec),
                        "-vf", vf_filter, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                        "-c:a", "aac", "-b:a", "128k", output_filename
                    ]
                    try:
                        subprocess.run(ffmpeg_command, capture_output=True, text=True, check=True)
                        rendered_files.append(output_filename)
                    except Exception:
                        pass

                    progress_bar.progress((idx + 1) / total_clips)

                status_box.empty()
                progress_bar.empty()
                st.session_state["rendered_clips"] = rendered_files
                if rendered_files:
                    st.success("¡Lote completado con éxito!")
                else:
                    st.error("No se pudo generar ningún clip. Verifica que ffmpeg esté instalado y en el PATH.")

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
