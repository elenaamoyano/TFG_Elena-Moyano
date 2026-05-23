import streamlit as st
import requests
import json
import time
import os
from datetime import datetime

st.set_page_config(
    page_title="Corrector + Knowledge Base",
    page_icon="🐳",
    layout="wide"
)

# URLs de servicios
WEBHOOK_URL_FICHEROS = "http://localhost:5678/webhook-test/config"
WEBHOOK_URL_APPS = "http://localhost:5678/webhook-test/apps"
FASTAPI_URL = "http://localhost:8001"

if 'procesando' not in st.session_state:
    st.session_state.procesando = False
if 'resultado' not in st.session_state:
    st.session_state.resultado = None
if 'modo_admin' not in st.session_state:
    st.session_state.modo_admin = False
if 'ultimo_reporte' not in st.session_state:
    st.session_state.ultimo_reporte = None
if 'ruta_yml_validada' not in st.session_state:
    st.session_state.ruta_yml_validada = None
if 'archivos_yml' not in st.session_state:
    st.session_state.archivos_yml = []

st.sidebar.title("🐳 Navegación")
st.sidebar.divider()

modo = st.sidebar.radio("Mode:", ["👤 User", "👑 Admin"])

if modo == "👑 Admin":
    password = st.sidebar.text_input("Contraseña Admin:", type="password")
    if password == "admin123":
        st.session_state.modo_admin = True
        st.sidebar.success("✅ Admin mode activated")
    else:
        st.session_state.modo_admin = False
        if password:
            st.sidebar.error("❌ Incorrect password")
        st.sidebar.info("Admin mode requires password")
else:
    st.session_state.modo_admin = False

st.sidebar.divider()

if st.session_state.modo_admin:
    st.sidebar.info("🛠️ You have admin license")
else:
    st.sidebar.info("👤 User mode - Just querys")

if st.session_state.modo_admin:
    st.title("👑 Administration panel")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📤 Upload documents", 
        "📊 Stadistics", 
        "💬 Transfomr querys",
        "📋 Reports",
        "⚙️ Configuration"
    ])
    
    with tab1:
        st.header("Upload documents to Chroma")
        st.markdown("Add documents to the vector knowledge base.")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_files = st.file_uploader(
                "Select documents",
                accept_multiple_files=True,
                type=['pdf', 'txt', 'docx', 'md'],
                help="PDF, TXT, DOCX o MD"
            )
        
        with col2:
            st.subheader("Options")
            chunk_size = st.number_input("Tamaño de fragmento", 
                                       value=1000, step=100)
            chunk_overlap = st.number_input("Solapamiento", 
                                          value=200, step=50)
        
        if uploaded_files and st.button("🚀 Upload to Chroma", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            resultados = []
            for i, file in enumerate(uploaded_files):
                status_text.text(f"Uploading {file.name}... ({i+1}/{len(uploaded_files)})")
                
                files = {"file": (file.name, file.getvalue(), file.type)}
                data = {"chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
                
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/ingest",
                        files=files,
                        data=data,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        resultados.append(f"✅ {file.name}")
                    else:
                        resultados.append(f"❌ {file.name}: {response.text}")
                        
                except Exception as e:
                    resultados.append(f"❌ {file.name}: {str(e)}")
                
                progress_bar.progress((i + 1) / len(uploaded_files))
            
            progress_bar.progress(100)
            status_text.text("Process completed")
            
            st.subheader("Results:")
            for resultado in resultados:
                st.write(resultado)
    
    with tab2:
        st.header("Chroma statistics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📊 See documents", use_container_width=True):
                try:
                    response = requests.get(f"{FASTAPI_URL}/documents", timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        st.metric("Total documents", data.get("total_documents", 0))
                        
                        if data.get("unique_sources"):
                            st.subheader("Fuentes únicas:")
                            for source in data["unique_sources"][:10]:
                                st.write(f"- {source}")
                    else:
                        st.error("Error obteniendo estadísticas")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col2:
            if st.button("🔄 Health Check", use_container_width=True):
                try:
                    response = requests.get(f"{FASTAPI_URL}/health", timeout=5)
                    if response.status_code == 200:
                        st.json(response.json())
                    else:
                        st.error("API no responde")
                except Exception as e:
                    st.error(f"Error: {e}")
        
        with col3:
            if st.button("⚠️ Reset DB", use_container_width=True):
                st.warning("Sure? This will delete all documents")
                confirm = st.checkbox("Confirm deletion")
                
                if confirm and st.button("YES, DELETE ALL"):
                    try:
                        response = requests.delete(
                            f"{FASTAPI_URL}/reset",
                            params={"confirm": True},
                            timeout=10
                        )
                        if response.status_code == 200:
                            st.success("Knowledge base reset")
                        else:
                            st.error("Error reset")
                    except Exception as e:
                        st.error(f"Error: {e}")
    
    with tab3:
        st.header("Convertir consultas en conocimiento")
        st.markdown("Selecciona consultas anteriores para añadirlas a Chroma")
        
        st.subheader("Entrada manual")
        consulta = st.text_area("Consulta del usuario:")
        respuesta_correcta = st.text_area("Respuesta correcta:")
        
        if st.button("💾 Guardar como documento de conocimiento"):
            if consulta and respuesta_correcta:
                contenido = f"""PREGUNTA: {consulta}
RESPUESTA: {respuesta_correcta}"""
                
                files = {"file": ("consulta_util.txt", contenido, "text/plain")}
                data = {"chunk_size": 500, "chunk_overlap": 50}
                
                try:
                    response = requests.post(
                        f"{FASTAPI_URL}/ingest",
                        files=files,
                        data=data,
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        st.success("✅ Consulta guardada en Chroma")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Completa ambos campos")
    
    with tab4:
        st.header("📋 Reportes de Correcciones")
        st.markdown("Aquí puedes ver y descargar los reportes detallados de las correcciones realizadas.")
        
        if st.session_state.ultimo_reporte:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader("Último reporte")
                contenido = st.session_state.ultimo_reporte['contenido']
                st.text_area("Contenido", contenido, height=300)
            
            with col2:
                st.subheader("Acciones")
                
                st.download_button(
                    label="📥 Download report",
                    data=contenido,
                    file_name=st.session_state.ultimo_reporte['filename'],
                    mime='text/plain',
                    use_container_width=True
                )
                
                st.divider()
                
                if st.button("🧠 Subir a Chroma", use_container_width=True, type="primary"):
                    with st.spinner("Subiendo a base de conocimiento..."):
                        try:
                            files = {
                                "file": (
                                    st.session_state.ultimo_reporte['filename'],
                                    contenido.encode('utf-8'),
                                    "text/plain"
                                )
                            }
                            data = {
                                "chunk_size": 1000,
                                "chunk_overlap": 200
                            }
                            
                            response = requests.post(
                                f"{FASTAPI_URL}/ingest",
                                files=files,
                                data=data,
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                st.success("✅ Reporte subido a Chroma correctamente")
                                st.balloons()
                            else:
                                st.error(f"❌ Error al subir: {response.text}")
                                
                        except Exception as e:
                            st.error(f"❌ Error de conexión: {e}")
                
                st.divider()
                
                if st.button("🗑️ Clean report", use_container_width=True):
                    st.session_state.ultimo_reporte = None
                    st.rerun()
        else:
            st.info("No hay reportes disponibles. Ejecuta una corrección para generar un reporte.")
        
    with tab5:
        st.header("Configuración de Chroma")
        
        st.subheader("Modelo de embeddings actual")
        try:
            health = requests.get(f"{FASTAPI_URL}/health", timeout=5).json()
            st.info(f"Modelo: {health.get('embeddings_model', 'desconocido')}")
            st.metric("Documentos en BD", health.get('documents_in_db', 0))
        except:
            st.warning("No se pudo conectar con FastAPI")
        
        st.divider()
        st.subheader("Configuración de fragmentación")
        col1, col2 = st.columns(2)
        with col1:
            default_chunk = st.number_input("Chunk size por defecto", 500, 2000, 1000)
        with col2:
            default_overlap = st.number_input("Overlap por defecto", 50, 500, 200)
        
        st.caption("Estos valores se usarán por defecto al subir documentos")
    
    st.divider()
    st.markdown("---")

if not st.session_state.modo_admin:
    st.title("🐳 Automatic Corrector")
    st.markdown("Select correction type")
    
    tipo_correccion = st.radio(
        "Correction type",
        options=["📁 Individual files", "📱 Complete app (multiple files)"],
        horizontal=True,
        help="📁 Files: correct syntax, semantic, logic errors in individual files\n📱 Apps: Corrects dependencies between files of the same application"
    )
    
    st.divider()
    
    if tipo_correccion == "📁 Individual files":
        st.subheader("📁 Individual files correction")
        st.markdown("Analyzes and corrects errors in files.")
        
        with st.form("ruta_form"):
            project_path = st.text_input(
                "Project path (path to docker-compose.yml)",
                placeholder="C:\\Desktop\\...",
                help="Folder that includes docker-compose.yml"
            )
            verificar = st.form_submit_button("🔍 Verify path")
        
        if verificar and project_path:
            if os.path.exists(project_path):
                archivos_yml = [f for f in os.listdir(project_path) 
                                if f.endswith(('.yml', '.yaml'))]
                if archivos_yml:
                    st.session_state.project_path_validada = project_path
                    st.session_state.archivos_yml = archivos_yml
                    st.success(f"✅ Valid path. {len(archivos_yml)} file(s) found.")
                else:
                    st.warning("No .yml files in this path")
                    st.session_state.project_path_validada = None
                    st.session_state.archivos_yml = []
            else:
                st.error("❌ Path not found")
                st.session_state.project_path_validada = None
                st.session_state.archivos_yml = []
        
        if st.session_state.get('project_path_validada') and st.session_state.archivos_yml:
            st.divider()
            with st.form("config_form"):
                st.subheader("Select files and services")
                
                selected_yml = st.multiselect(
                    "docker-compose.yml files",
                    options=st.session_state.archivos_yml,
                    default=st.session_state.archivos_yml[0] if st.session_state.archivos_yml else []
                )
                
                file_path = st.text_input(
                    "Folder where the file to correct is located (REQUIRED)",
                    placeholder="C:\\project\\nginx",
                    help="Ejemplo: C:\\project\\nginx"
                )
                
                file_name = st.text_input(
                    "Name of the file to correct (REQUIRED)",
                    placeholder="nginx.conf",
                    help="Example: nginx.conf, my.cnf, postgresql.conf"
                )
                
                service = st.text_input(
                    "docker-compose service name (REQUIRED)",
                    placeholder="nginx",
                    help="Example: nginx, mysql, backend"
                )
                
                output_path = st.text_input(
                    "Alternative path to save corrected configurations",
                    placeholder="C:\\Desktop\\corrected",
                    help="If left empty, the original file will be overwritten"
                )
                
                submitted = st.form_submit_button("🚀 Send to n8n", type="primary")
                
                if submitted:
                    if not selected_yml:
                        st.error("Select one docker-compose.yml file")
                    elif not file_path:
                        st.error("Folder where the file to correct is located is requiered")
                    elif not file_name:
                        st.error("Name of the file to correct is required")
                    elif not service:
                        st.error("Service name is required")
                    else:
                                                
                        payload = {
                            "project_path": st.session_state.project_path_validada,
                            "compose_files": selected_yml,
                            "file_path": file_path,
                            "file_name": file_name,
                            "service": service,
                            "output_path": output_path if output_path else "sobrescribir"
                        }
                                                
                        with st.expander("📋 Sent data"):
                            st.json(payload)
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            status_text.text("📤 Sending to n8n...")
                            progress_bar.progress(25)
                            
                            response = requests.post(WEBHOOK_URL_FICHEROS, json=payload, timeout=180)
                            progress_bar.progress(75)
                            
                            if response.status_code == 200:
                                status_text.text("✅ Processing answer...")
                                content_type = response.headers.get('content-type', '')
                                
                                if 'text/plain' in content_type or 'application/octet-stream' in content_type:
                                    progress_bar.progress(100)
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"app_correction_{timestamp}.txt"

                                    contenido = response.content.decode('utf-8')

                                    st.session_state.ultimo_reporte = {
                                        'content': contenido,
                                        'filename': filename
                                    }

                                    st.success("✅ App correction completed.")
                                    
                                    with st.expander("📋 Report"):
                                        st.text(contenido)
                                else:
                                    respuesta_json = response.json()
                                    st.success(f"✅ {respuesta_json.get('message', 'Processed completed')}")
                            else:
                                st.error(f"❌ Error {response.status_code}")
                                
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            progress_bar.empty()
                            status_text.empty()
        
        st.divider()
        st.caption("The corrected files will be saved to the specified path.")
    
    else:
        st.subheader("📱 Full application correction")
        st.markdown("Analyzes and corrects dependencies between files within the same application.")
        
        if 'app_path_validada' not in st.session_state:
            st.session_state.app_path_validada = ""
        if 'archivos_disponibles' not in st.session_state:
            st.session_state.archivos_disponibles = []
        
        with st.form("apps_ruta_form"):
            app_path = st.text_input(
                "📁 App path",
                placeholder="C:\\Desktop\\...\\my_app",
                value=st.session_state.app_path_validada,
                help="App folder"
            )
            explorar_ruta = st.form_submit_button("🔍 Explore folder")
        
        if explorar_ruta and app_path:
            if os.path.exists(app_path):
                todos_archivos = []
                for root, dirs, files in os.walk(app_path):
                    for file in files:
                        if not any(excl in root for excl in ['__pycache__', '.git', 'node_modules']):
                            ruta_relativa = os.path.relpath(os.path.join(root, file), app_path)
                            todos_archivos.append(ruta_relativa)
                
                if todos_archivos:
                    st.session_state.app_path_validada = app_path
                    st.session_state.archivos_disponibles = todos_archivos
                    st.success(f"✅ {len(todos_archivos)} files found")
                else:
                    st.warning("No files found in the specified path")
            else:
                st.error("❌ The path does not exist")
        
        if st.session_state.archivos_disponibles:
            st.divider()
            
            with st.form("apps_envio_form"):
                st.subheader("📄 Select files to analyze")
                st.caption("You can select multiple files (Ctrl+click)")
                
                # Multiselect de archivos (solo nombres)
                selected_files = st.multiselect(
                    "Files",
                    options=st.session_state.archivos_disponibles,
                    default=st.session_state.archivos_disponibles,
                    help="Select app files"
                )
                
                st.divider()
                
                # Ruta de guardado (opcional)
                output_path_app = st.text_input(
                    "Alternative path to save corrected configurations",
                    placeholder="C:\\Desktop\\...\\corrected",
                    help="If left empty, the original file will be overwritten"
                )
                
                # Botón de envío
                enviar = st.form_submit_button("🚀 Analyze and correct app", type="primary")
                
                if enviar:
                    if not selected_files:
                        st.error("You must select at least one file")
                    else:
                        # Payload: SOLO ruta + nombres de archivos
                        payload = {
                            "app_path": st.session_state.app_path_validada,
                            "archivos": selected_files,  # Solo los nombres
                            "output_path": output_path_app if output_path_app else "sobrescribir",
                            "mode": "apps",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        with st.expander("📋 Sent data", expanded=False):
                            st.write(f"**Folder:** {st.session_state.app_path_validada}")
                            st.write(f"**Selected files:** {len(selected_files)}")
                            for a in selected_files[:10]:
                                st.write(f"- {a}")
                            if len(selected_files) > 10:
                                st.write(f"... y {len(selected_files) - 10} más")
                        
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        try:
                            status_text.text("📤 Sending to n8n...")
                            progress_bar.progress(25)
                            
                            response = requests.post(WEBHOOK_URL_APPS, json=payload, timeout=180)
                            progress_bar.progress(75)
                            
                            if response.status_code == 200:
                                status_text.text("✅ Processing answer...")
                                content_type = response.headers.get('content-type', '')
                                
                                if 'text/plain' in content_type or 'application/octet-stream' in content_type:
                                    progress_bar.progress(100)
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    filename = f"app_correction_{timestamp}.txt"

                                    contenido = response.content.decode('utf-8')

                                    st.session_state.ultimo_reporte = {
                                        'content': contenido,
                                        'filename': filename
                                    }

                                    st.success("✅ App correction completed.")
                                    
                                    with st.expander("📋 Report"):
                                        st.text(contenido)
                                else:
                                    respuesta_json = response.json()
                                    st.success(f"✅ {respuesta_json.get('message', 'Processed completed')}")
                            else:
                                st.error(f"❌ Error {response.status_code}")
                                
                        except Exception as e:
                            st.error(f"❌ Error: {e}")
                        finally:
                            progress_bar.empty()
                            status_text.empty()

st.sidebar.divider()
st.sidebar.caption("🐳 Corrector NGINX + Base Conocimiento v2.0")
st.sidebar.caption("FastAPI + Chroma + Streamlit")