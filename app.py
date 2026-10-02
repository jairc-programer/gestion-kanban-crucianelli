import streamlit as st
import pandas as pd
import re
import os
import json
import io
from datetime import datetime
import pytz
import plotly.express as px

st.set_page_config(page_title="Gestor de Kanbans - Crucianelli", layout="wide")

# ==========================================
# ESTILOS CSS PERSONALIZADOS (DARK PREMIUM)
# ==========================================
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    header {visibility: hidden;}

    div[data-testid="stVerticalBlock"] > div:has(div.card-container) {
        background: rgba(22, 27, 34, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 18px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 16px;
    }
    
    div[data-testid="stMetricLabel"] { font-size: 0.82rem !important; color: #909296 !important; }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #ffffff !important; }

    div[data-baseweb="tab-list"] { gap: 8px; border-bottom: none !important; margin-bottom: 15px; }

    div[data-baseweb="tab"] {
        height: 38px;
        border-radius: 8px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
        color: #c1c2c5 !important;
        padding: 0px 16px !important;
        font-size: 0.88rem !important;
    }

    div[data-baseweb="tab"][aria-selected="true"] {
        border: 1px solid #a83232 !important;
        background-color: rgba(168, 50, 50, 0.15) !important;
        color: #ff8e8e !important;
    }

    .stTextInput input, .stSelectbox select, div[data-baseweb="select"] > div {
        border-radius: 8px !important;
        background-color: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        color: #ffffff !important;
    }

    div.stButton > button { border-radius: 8px !important; font-weight: 500 !important; }
    div.stButton > button[kind="primary"] { background-color: #8b2626 !important; border: 1px solid #b33636 !important; }

    .badge-rol {
        background: rgba(74, 144, 226, 0.2);
        border: 1px solid #4a90e2;
        color: #93c5fd;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 600;
    }

    .header-box {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 12px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def obtener_fecha_hora_arg():
    return datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")

DB_FILE = "TablaZ.xlsx"
PKG_FILE = "Lote packaging.xlsx"
LOG_FILE = "historial_cambios.csv"
TRACKER_FILE = "tracker_ejecucion.csv"
USERS_FILE = "usuarios.json"
SHEET_NAME = "Kanbans CRUCIANELLI"

LOG_COLUMNS = ["Fecha_Hora", "Acción", "Código_K", "Material", "Medio", "Almacén_Destino", "Puesto_Destino", "Detalle_Cambio", "Usuario"]
TRACKER_COLUMNS = ["ID_Solicitud", "Fecha_Solicitud", "Material", "Código_K", "Tipo_KB", "Puesto_Destino", "Medio", "Cambio", "Acción_Requerida", "Cargado_SAP", "Impreso", "Fecha_Impresion", "Estado_Fisico", "Fecha_Finalizacion", "Observación", "Usuario_Procesos"]

ROLES_PREDEFINIDOS = {
    "jairc@crucianelli.com": "Procesos", "mmagarello@crucianelli.com": "Procesos",
    "mcabral@crucianelli.com": "Procesos", "gtuninetti@crucianelli.com": "Procesos",
    "produccion@crucianelli.com": "Procesos", "abacelli@crucianelli.com": "Procesos",
    "tabrate@crucianelli.com": "Procesos", "llatanzi@crucianelli.com": "Procesos",
    
    "mlopez@crucianelli.com": "Logistica", "recepcion3@crucianelli.com": "Logistica",
    "gpereyra@crucianelli.com": "Logistica", "jporta@crucianelli.com": "Logistica",
    "spetetta@crucianelli.com": "Logistica", "ileon@crucianelli.com": "Logistica", 
    "gfianchini@crucianelli.com": "Logistica",
    
    "fany@crucianelli.com": "Consulta", "strillini@crucianelli.com": "Consulta",
    "apicotto@crucianelli.com": "Consulta", "fsolis@crucianelli.com": "Consulta",
    "isola@crucianelli.com": "Consulta", "bfrutos@crucianelli.com": "Consulta",
    "rpaul@crucianelli.com": "Consulta", "mscrofono@crucianelli.com": "Consulta",
    "gigli@crucianelli.com": "Consulta", "ftrillini@crucianelli.com": "Consulta",
    "psantilli@crucianelli.com": "Consulta", "activacion@crucianelli.com": "Consulta"
}

def guardar_usuarios(usuarios_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios_dict, f, indent=4)

def cargar_usuarios():
    dict_users = {}
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data_guardada = json.load(f)
                
            for email, val in data_guardada.items():
                rol_asig = ROLES_PREDEFINIDOS.get(email, "Consulta")
                if isinstance(val, str):
                    dict_users[email] = {"pass": val, "rol": rol_asig}
                elif isinstance(val, dict):
                    dict_users[email] = {
                        "pass": val.get("pass", ""),
                        "rol": val.get("rol", rol_asig)
                    }
        except Exception:
            pass
    return dict_users

USUARIOS_REGISTRADOS = cargar_usuarios()

COLUMNS = [
    'N° Etiquetas', 'Tipo Etiqueta', 'Tipo Kanban', 'Medio', 'Material', 'Centro', 
    'Almacén Origen', 'Almacen Destino', 'Puesto trabajo Origen', 
    'Puesto de trabajo destino', 'Cantidad Reposicion', 
    'Unidad Reposicion', 'Cantidad Punto de Pedido', 
    'Tiempo preparación abast. (en días)',
    'Fecha Modificación', 'Usuario Modificación'
]

ALMACENES_PUESTOS = {
    "P110": ["ARM_HORQ", "ARM_MAZ1", "CORTE_01", "MECANIZA", "PRENBAL1", "ROSC_REM"],
    "P120": [
        "APUNCHAS", "SOLDCHA1", "SOLDMADR", "SOLDMAN1", "SOLDMAN2", "SOLDMAN3", 
        "SOLDMAN4", "SOLDMAN5", "SOLDMAN6", "SOLDMAN7", "SOLDMAP1", "SOLDMAP2", 
        "SOLDMAP3", "SOLROB06", "SOLROB08", "SOLROB09", "SOLROB10", "SOLROB12", 
        "SOLROB13", "SOLROB14", "SOLROB15", "SOLROB16", "SOLROB17"
    ],
    "P130": ["MONTIN01", "MONTIN02", "MONTIN03", "MONTIN04", "MONTJAD1"],
    "P140": ["LAVADO01", "PINTURA1", "PINTURA2"],
    "P150": ["MONFIN01", "MONFIN02", "MONFIN03", "MONFIN04", "MTJBARAP", "MTJF01PD", "MTJF02PD", "MTJF03PD", "MTJPRS"],
    "P160": ["ARCUCH01", "ARMBAR01", "ARMCUERP", "ARMDOSIF", "ARTOLVAS", "SUBCONJU", "TURBINAS"],
    "P180": ["CARGAFIN", "MURFINAL"],
    "P190": ["HOSPITAL"],
    "CC01": ["POSVENTA"],
    "ID01": ["PROTOTIPO"],
    "L010": ["PRINCIPAL"]
}

LISTA_ALMACENES = list(ALMACENES_PUESTOS.keys())
OPCIONES_SOPORTE_TARJETA = ["SIN MEDIO DEFINIDO", "PALLET CHICO", "PALLET GRANDE", "CANASTO", "CAPACHO CHICO", "CAPACHO GRANDE", "RACK"]
OPCIONES_GAVETA = ["S", "M", "L", "XL"]

if 'usuario_email' not in st.session_state:
    st.session_state['usuario_email'] = None
if 'usuario_rol' not in st.session_state:
    st.session_state['usuario_rol'] = None

# ==========================================
# PANTALLA DE AUTENTICACIÓN
# ==========================================
if not st.session_state['usuario_email']:
    st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")
    col_auth, _ = st.columns([1.5, 2])
    with col_auth:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.subheader("🔐 Acceso al Sistema")
        
        email_google = st.text_input("Correo Google Workspace (@crucianelli.com):", key="g_mail_input", placeholder="ejemplo@crucianelli.com").strip().lower()
        if st.button("🌐 Iniciar Sesión con Google (@crucianelli.com)", use_container_width=True, key="btn_g_login"):
            if not email_google:
                st.error("❌ Por favor ingrese su correo corporativo de Google.")
            elif not email_google.endswith("@crucianelli.com"):
                st.error("❌ El correo debe pertenecer obligatoriamente a @crucianelli.com.")
            else:
                rol_asig = ROLES_PREDEFINIDOS.get(email_google, "Consulta")
                if email_google not in USUARIOS_REGISTRADOS:
                    USUARIOS_REGISTRADOS[email_google] = {"pass": "google_oauth", "rol": rol_asig}
                    guardar_usuarios(USUARIOS_REGISTRADOS)
                
                st.session_state['usuario_email'] = email_google
                st.session_state['usuario_rol'] = rol_asig
                st.success(f"Bienvenido/a {email_google}")
                st.rerun()

        st.markdown("<p style='text-align:center; color:#888; margin-top: 15px;'>— o acceso directo con contraseña —</p>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔑 Iniciar Sesión Directo", "📝 Registrarse"])
        
        with tab_login:
            email_input = st.text_input("Correo corporativo (@crucianelli.com):", key="log_email").strip().lower()
            password_input = st.text_input("Contraseña:", type="password", key="log_pass")
            
            if st.button("Ingresar", type="primary", use_container_width=True):
                if not email_input or not password_input:
                    st.error("❌ Complete correo y contraseña.")
                elif not email_input.endswith("@crucianelli.com"):
                    st.error("❌ El correo debe ser del dominio @crucianelli.com.")
                elif email_input in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[email_input]["pass"] == password_input:
                    st.session_state['usuario_email'] = email_input
                    st.session_state['usuario_rol'] = USUARIOS_REGISTRADOS[email_input]["rol"]
                    st.success(f"Bienvenido/a {email_input}")
                    st.rerun()
                else:
                    st.error("❌ Credenciales incorrectas o usuario no registrado.")

        with tab_register:
            reg_email = st.text_input("Correo corporativo (@crucianelli.com):", key="reg_email").strip().lower()
            reg_pass1 = st.text_input("Cree su contraseña:", type="password", key="reg_pass1")
            reg_pass2 = st.text_input("Confirme su contraseña:", type="password", key="reg_pass2")
            
            if st.button("Crear Cuenta", use_container_width=True):
                if not reg_email or not reg_pass1 or not reg_pass2:
                    st.error("❌ Complete todos los campos.")
                elif not reg_email.endswith("@crucianelli.com"):
                    st.error("❌ El correo debe ser obligatoriamente @crucianelli.com.")
                elif reg_pass1 != reg_pass2:
                    st.error("❌ Las contraseñas no coinciden.")
                elif reg_email in USUARIOS_REGISTRADOS:
                    st.warning("⚠️ Este usuario ya se encuentra registrado. Inicie sesión directamente.")
                else:
                    rol_asignado = ROLES_PREDEFINIDOS.get(reg_email, "Consulta")
                    USUARIOS_REGISTRADOS[reg_email] = {"pass": reg_pass1, "rol": rol_asignado}
                    guardar_usuarios(USUARIOS_REGISTRADOS)
                    st.success(f"✅ ¡Cuenta creada exitosamente para {reg_email}! (Rol asignado: {rol_asignado}). Ya puede iniciar sesión.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# MANEJO CENTRALIZADO Y SINCRONIZADO EN VIVO
# ==========================================
@st.cache_data(ttl=1)
def cargar_base_desde_disco():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = None
            
            df['Material'] = df['Material'].fillna('').astype(str).str.strip().str.upper()
            df['N° Etiquetas'] = df['N° Etiquetas'].fillna('').astype(str).str.strip().str.upper()

            def determinar_tipo_kanban(row):
                cant_repo = row.get('Cantidad Reposicion')
                cant_pp = row.get('Cantidad Punto de Pedido')
                try:
                    if pd.notna(cant_repo) and pd.notna(cant_pp):
                        return "GAVETA" if float(cant_repo) == float(cant_pp) else "TARJETA"
                except (ValueError, TypeError):
                    pass
                return "TARJETA"
            df['Tipo Kanban'] = df.apply(determinar_tipo_kanban, axis=1)
            return df[COLUMNS].reset_index(drop=True)
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def obtener_base_kanbans(force_reload=False):
    if force_reload:
        st.cache_data.clear()
    return cargar_base_desde_disco()

def actualizar_base_kanbans(nuevo_df):
    df_limpio = nuevo_df.reset_index(drop=True)
    try:
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_limpio.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    except Exception as e:
        st.error(f"⚠️ Error al guardar en el archivo Excel físico: {e}")
    # Limpiamos la caché inmediatamente para forzar la lectura del disco en el próximo rerun
    st.cache_data.clear()

def cargar_packaging():
    if os.path.exists(PKG_FILE):
        try:
            df = pd.read_excel(PKG_FILE)
            df['Material'] = df['Material'].astype(str).str.strip().str.upper()
            return df.set_index('Material')['Packaing'].to_dict()
        except Exception:
            return {}
    return {}

def cargar_logs():
    if os.path.exists(LOG_FILE):
        try:
            df_logs = pd.read_csv(LOG_FILE, on_bad_lines='skip')
            for col in LOG_COLUMNS:
                if col not in df_logs.columns:
                    df_logs[col] = None
            mapeo_acciones = {
                'CREAR': 'CREACIÓN', 'CREO': 'CREACIÓN', 'CREACION': 'CREACIÓN',
                'MODIFICAR': 'MODIFICACIÓN', 'ACTUALIZO': 'MODIFICACIÓN', 'MODIFICACION': 'MODIFICACIÓN',
                'ELIMINAR': 'ELIMINACIÓN', 'ELIMINO': 'ELIMINACIÓN', 'ELIMINACION': 'ELIMINACIÓN'
            }
            df_logs['Acción'] = df_logs['Acción'].astype(str).str.upper().map(lambda x: mapeo_acciones.get(x, x))
            return df_logs[LOG_COLUMNS]
        except Exception:
            return pd.DataFrame(columns=LOG_COLUMNS)
    return pd.DataFrame(columns=LOG_COLUMNS)

def registrar_log(accion, codigo_k, material, medio, alm_dest, puesto_dest, usuario, detalle_cambio="-"):
    now = obtener_fecha_hora_arg()
    df_actual = cargar_logs()
    if pd.isna(medio) or str(medio).strip() in ["None", "nan", "N/A", ""]:
        medio = "SIN MEDIO DEFINIDO"
    
    mapeo_guardado = {'CREO': 'CREACIÓN', 'ACTUALIZO': 'MODIFICACIÓN', 'ELIMINO': 'ELIMINACIÓN'}
    accion_norm = mapeo_guardado.get(accion, accion)

    nuevo_log = pd.DataFrame([{
        "Fecha_Hora": now, 
        "Acción": accion_norm, 
        "Código_K": codigo_k,
        "Material": material, 
        "Medio": str(medio), 
        "Almacén_Destino": alm_dest,
        "Puesto_Destino": puesto_dest, 
        "Detalle_Cambio": str(detalle_cambio),
        "Usuario": usuario
    }])
    df_final = pd.concat([df_actual, nuevo_log], ignore_index=True)
    df_final.to_csv(LOG_FILE, index=False)

def cargar_tracker():
    if os.path.exists(TRACKER_FILE):
        try:
            df_tr = pd.read_csv(TRACKER_FILE, on_bad_lines='skip', dtype=str)
            for col in TRACKER_COLUMNS:
                if col not in df_tr.columns:
                    df_tr[col] = "-"
            df_tr = df_tr.fillna("-").astype(str)
            return df_tr[TRACKER_COLUMNS]
        except Exception:
            return pd.DataFrame(columns=TRACKER_COLUMNS)
    return pd.DataFrame(columns=TRACKER_COLUMNS)

def guardar_tracker(df_tr):
    df_tr.to_csv(TRACKER_FILE, index=False)

def crear_solicitud_tracker(material, codigo_k, tipo_kb, puesto_dest, medio, cambio, accion_req, usuario):
    now_date = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
    df_tr = cargar_tracker()
    id_sol = f"SOL-{len(df_tr)+1:05d}"
    
    nueva_fila = pd.DataFrame([{
        "ID_Solicitud": id_sol,
        "Fecha_Solicitud": now_date,
        "Material": str(material),
        "Código_K": str(codigo_k),
        "Tipo_KB": str(tipo_kb),
        "Puesto_Destino": str(puesto_dest),
        "Medio": str(medio),
        "Cambio": str(cambio),
        "Acción_Requerida": str(accion_req),
        "Cargado_SAP": "NO",
        "Impreso": "NO",
        "Fecha_Impresion": "-",
        "Estado_Fisico": "Pendiente",
        "Fecha_Finalizacion": "-",
        "Observación": "-",
        "Usuario_Procesos": str(usuario)
    }])
    df_final = pd.concat([df_tr, nueva_fila], ignore_index=True)
    guardar_tracker(df_final)

def limpiar_historiales_de_prueba():
    df_empty_log = pd.DataFrame(columns=LOG_COLUMNS)
    df_empty_log.to_csv(LOG_FILE, index=False)
    
    df_empty_tracker = pd.DataFrame(columns=TRACKER_COLUMNS)
    df_empty_tracker.to_csv(TRACKER_FILE, index=False)

def obtener_siguiente_codigo_k(df):
    if df.empty or df['N° Etiquetas'].dropna().empty:
        return "K00000001"
    
    numeros = [int(m.group(0)) for val in df['N° Etiquetas'].dropna() if (m := re.search(r'\d+', str(val)))]
    set_numeros = set(numeros)
    
    i = 1
    while True:
        if i not in set_numeros:
            return f"K{i:08d}"
        i += 1

# Carga global inicial de datos
df_kanbans = obtener_base_kanbans()
dict_pkg = cargar_packaging()
rol_actual = st.session_state.get('usuario_rol', 'Consulta')

# ==========================================
# CABECERA Y ROL CON BOTÓN DE ACTUALIZACIÓN
# ==========================================
st.markdown(f"""
<div class="header-box">
    <div style="display: flex; align-items: center; gap: 12px;">
        <span style="font-size: 1.8rem;">📦</span>
        <div>
            <h2 style="margin: 0; padding: 0; color: #f0f6fc; font-weight: 600; font-size: 1.4rem;">Sistema de Gestión de Kanbans - Crucianelli</h2>
            <span style="font-size: 0.85rem; color: #8b949e;">Usuario: <b>{st.session_state['usuario_email']}</b></span>
        </div>
    </div>
    <div>
        <span class="badge-rol">ROL: {rol_actual.upper()}</span>
    </div>
</div>
""", unsafe_allow_html=True)

col_head_space, col_refresh, col_logout = st.columns([3.8, 1.2, 1])
with col_refresh:
    if st.button("🔄 Actualizar Datos", use_container_width=True, help="Releer y actualizar datos desde TablaZ.xlsx"):
        st.cache_data.clear()
        st.toast("🔄 Datos sincronizados correctamente desde TablaZ.xlsx")
        st.rerun()

with col_logout:
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['usuario_email'] = None
        st.session_state['usuario_rol'] = None
        st.cache_data.clear()
        st.rerun()

total_k = len(df_kanbans)
internos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KI'])
externos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KE'])
proximo_k_val = obtener_siguiente_codigo_k(df_kanbans)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Kanbans", total_k)
kpi2.metric("Internos (KI)", internos_k)
kpi3.metric("Externos (KE)", externos_k)
kpi4.metric("Próximo Código K (Libre)", proximo_k_val)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# MENÚ POR PERFILES Y NAVEGACIÓN
# ==========================================
if rol_actual == "Procesos":
    lista_tabs = ["➕ Crear Nuevo Kanban", "✏️ Modificar y Eliminar", "📈 Panel KPIs & Métricas", "🚚 Tracker de Ejecución Logística", "📊 Datos de Kanban", "📜 Historial Auditoría", "👤 Mi Perfil"]
elif rol_actual == "Logistica":
    lista_tabs = ["🚚 Tracker de Ejecución Logística", "📈 Panel KPIs & Métricas", "📊 Datos de Kanban", "📜 Historial Auditoría", "👤 Mi Perfil"]
else:
    lista_tabs = ["📈 Panel KPIs & Métricas", "📊 Datos de Kanban", "🚚 Estado de Solicitudes", "👤 Mi Perfil"]

tabs = st.tabs(lista_tabs)

def obtener_tab(nombre):
    if nombre in lista_tabs:
        return tabs[lista_tabs.index(nombre)]
    return None

# ==========================================
# VISTA: CREAR KANBAN
# ==========================================
tab_crear = obtener_tab("➕ Crear Nuevo Kanban")
if tab_crear:
    with tab_crear:
        st.subheader("Alta de Nuevo Kanban")
        
        if 'msj_creacion' in st.session_state:
            tipo_msj, texto_msj = st.session_state.pop('msj_creacion')
            if tipo_msj == 'success':
                st.markdown(f"""
                <div style="background-color: rgba(16, 185, 129, 0.2); border: 2px solid #10b981; padding: 14px; border-radius: 10px; color: #34d399; font-size: 1.15rem; font-weight: bold; text-align: center; margin-bottom: 20px;">
                    ✅ {texto_msj}
                </div>
                """, unsafe_allow_html=True)
            elif tipo_msj == 'error':
                st.markdown(f"""
                <div style="background-color: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; padding: 14px; border-radius: 10px; color: #f87171; font-size: 1.15rem; font-weight: bold; text-align: center; margin-bottom: 20px;">
                    ❌ {texto_msj}
                </div>
                """, unsafe_allow_html=True)

        st.info(f"Próximo Código K asignado automáticamente: **{proximo_k_val}**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            centro = st.text_input("Centro", value="A110")
            material = st.text_input("Código de Material (ej. PB005075)", max_chars=12).upper().strip()
            
            pkg_sugerido = dict_pkg.get(material, None)
            if pkg_sugerido:
                st.info(f"📦 Lote de Packaging Registrado: **{int(pkg_sugerido)}** unidades.")
            
            tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"])
            if tipo_soporte == "GAVETA":
                tam_gaveta = st.selectbox("Tamaño Gaveta", OPCIONES_GAVETA)
                medio_str = f"GAVETA {tam_gaveta}"
            else:
                medio_str = st.selectbox("Medio Físico", OPCIONES_SOPORTE_TARJETA)

        with col2:
            almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index("L010"))
            almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index("P140"))
            
            es_interno = (almacen_origen != "L010")
            tipo_etiqueta_sap = "KI" if es_interno else "KE"
            
            if es_interno:
                st.info("ℹ️ Abastecimiento INTERNO (KI)")
                puesto_origen_opts = ["-- Seleccionar --"] + ALMACENES_PUESTOS.get(almacen_origen, [])
                puesto_origen_sel = st.selectbox("Puesto de Trabajo Origen", puesto_origen_opts)
                puesto_origen = puesto_origen_sel if puesto_origen_sel != "-- Seleccionar --" else "-"
            else:
                st.info("ℹ️ Abastecimiento EXTERNO (KE)")
                st.text_input("Puesto de Trabajo Origen", value="- No aplica (Externo L010) -", disabled=True)
                puesto_origen = "-"

            opts_p_dest = ALMACENES_PUESTOS.get(almacen_destino, [])
            if opts_p_dest:
                puesto_destino_final = st.selectbox("Puesto de Trabajo Destino", opts_p_dest)
            else:
                puesto_destino_final = st.text_input("Puesto de Trabajo Destino", placeholder="Ingrese el puesto destino").upper().strip()

        with col3:
            cant_repo = st.number_input("Cantidad Reposición (Lote)", min_value=0.0, value=float(pkg_sugerido or 0.0), step=1.0)
            
            if tipo_soporte == "GAVETA":
                cant_pp = st.number_input("Cantidad Punto de Pedido", value=cant_repo, disabled=True)
            else:
                cant_pp = st.number_input("Cantidad Punto de Pedido", min_value=0.0, step=1.0)

            unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
            dias_prep = st.number_input("Tiempo Preparación / Días Abast.", min_value=0, value=1)

        if st.button("💾 Guardar y Crear Kanban", type="primary"):
            df_curr = obtener_base_kanbans()
            
            if not material or not puesto_destino_final:
                st.session_state['msj_creacion'] = ('error', "NO SE PUDO CREAR KANBAN: Código de Material y Puesto Destino son obligatorios.")
                st.rerun()
            elif pkg_sugerido is not None and pkg_sugerido > 0 and (float(cant_repo) <= 0 or float(cant_repo) % float(pkg_sugerido) != 0):
                st.session_state['msj_creacion'] = ('error', f"NO SE PUDO CREAR KANBAN: La Cantidad de Reposición ({cant_repo}) no respeta el Lote de Packaging ({int(pkg_sugerido)} un.). Debe ser múltiplo de {int(pkg_sugerido)}.")
                st.rerun()
            elif tipo_soporte == "TARJETA" and float(cant_pp) >= float(cant_repo):
                st.session_state['msj_creacion'] = ('error', f"NO SE PUDO CREAR KANBAN: En Tipo TARJETA, Punto de Pedido ({cant_pp}) debe ser menor a Reposición ({cant_repo}).")
                st.rerun()
            elif not df_curr.empty and len(
                df_curr[
                    (df_curr['Material'].astype(str).str.strip().str.upper() == material) & 
                    (df_curr['Puesto de trabajo destino'].astype(str).str.strip().str.upper() == puesto_destino_final.upper())
                ]
            ) > 0:
                kb_existente = df_curr[
                    (df_curr['Material'].astype(str).str.strip().str.upper() == material) & 
                    (df_curr['Puesto de trabajo destino'].astype(str).str.strip().str.upper() == puesto_destino_final.upper())
                ].iloc[0]['N° Etiquetas']
                st.session_state['msj_creacion'] = ('error', f"NO SE PUDO CREAR KANBAN: Ya existe el Kanban {kb_existente} para Material {material} en el Puesto {puesto_destino_final}.")
                st.rerun()
            else:
                fecha_actual = obtener_fecha_hora_arg()
                usr_act = st.session_state['usuario_email']
                codigo_k_nuevo = obtener_siguiente_codigo_k(df_curr)
                
                nuevo_reg = {
                    'N° Etiquetas': str(codigo_k_nuevo), 
                    'Tipo Etiqueta': str(tipo_etiqueta_sap),
                    'Tipo Kanban': str(tipo_soporte), 
                    'Medio': str(medio_str), 
                    'Material': str(material),
                    'Centro': str(centro), 
                    'Almacén Origen': str(almacen_origen), 
                    'Almacen Destino': str(almacen_destino),
                    'Puesto trabajo Origen': str(puesto_origen), 
                    'Puesto de trabajo destino': str(puesto_destino_final),
                    'Cantidad Reposicion': cant_repo, 
                    'Unidad Reposicion': str(unidad),
                    'Cantidad Punto de Pedido': cant_pp if tipo_soporte == "TARJETA" else cant_repo, 
                    'Tiempo preparación abast. (en días)': dias_prep,
                    'Fecha Modificación': fecha_actual, 
                    'Usuario Modificación': str(usr_act)
                }
                
                df_actualizado = pd.concat([df_curr, pd.DataFrame([nuevo_reg])], ignore_index=True)
                actualizar_base_kanbans(df_actualizado)
                
                registrar_log("CREO", codigo_k_nuevo, material, medio_str, almacen_destino, puesto_destino_final, usr_act)
                crear_solicitud_tracker(material, codigo_k_nuevo, tipo_etiqueta_sap, puesto_destino_final, medio_str, "CÓDIGO NUEVO", "ARMAR PEDIDO", usr_act)
                
                st.session_state['msj_creacion'] = ('success', f"KANBAN {codigo_k_nuevo} CREADO EXITOSAMENTE")
                st.rerun()

# ==========================================
# VISTA: MODIFICAR Y ELIMINAR
# ==========================================
tab_mod = obtener_tab("✏️ Modificar y Eliminar")
if tab_mod:
    with tab_mod:
        if 'msj_mod' in st.session_state:
            tipo_msj, texto_msj = st.session_state.pop('msj_mod')
            if tipo_msj == 'success':
                st.markdown(f"""
                <div style="background-color: rgba(16, 185, 129, 0.2); border: 2px solid #10b981; padding: 14px; border-radius: 10px; color: #34d399; font-size: 1.15rem; font-weight: bold; text-align: center; margin-bottom: 20px;">
                    ✅ {texto_msj}
                </div>
                """, unsafe_allow_html=True)
            elif tipo_msj == 'error':
                st.markdown(f"""
                <div style="background-color: rgba(239, 68, 68, 0.2); border: 2px solid #ef4444; padding: 14px; border-radius: 10px; color: #f87171; font-size: 1.15rem; font-weight: bold; text-align: center; margin-bottom: 20px;">
                    ❌ {texto_msj}
                </div>
                """, unsafe_allow_html=True)

        df_live = obtener_base_kanbans()
        
        m_col_left, m_col_right = st.columns([2, 1])
        
        with m_col_left:
            st.subheader("✏️ Modificar Kanban Existente")
            busqueda = st.text_input("Ingrese Código de Material a Buscar:", key="search_mod", placeholder="ej. CM000042").upper().strip()
            
            if busqueda:
                kanbans_encontrados = df_live[
                    (df_live['Material'].astype(str).str.strip().str.upper() == busqueda) |
                    (df_live['Material'].astype(str).str.contains(busqueda, na=False, regex=False)) |
                    (df_live['N° Etiquetas'].astype(str).str.strip().str.upper() == busqueda)
                ]
                
                if not kanbans_encontrados.empty:
                    opciones_k = [
                        f"{r['N° Etiquetas']} | Material: {r['Material']} | Puesto: {r['Puesto de trabajo destino']}" 
                        for _, r in kanbans_encontrados.iterrows()
                    ]
                    
                    sel_k_fmt = st.selectbox("Seleccione el Código K a modificar:", opciones_k, key="sel_k_mod_dropdown")
                    k_sel = sel_k_fmt.split(" | ")[0].strip()
                    row = kanbans_encontrados[kanbans_encontrados['N° Etiquetas'] == k_sel].iloc[0]
                    mat_sel = str(row['Material'])
                    
                    pkg_ref = dict_pkg.get(mat_sel, None)
                    if pkg_ref:
                        st.info(f"📦 Lote de Packaging Registrado para {mat_sel}: **{int(pkg_ref)}** unidades.")
                    
                    st.markdown(f"##### **Modificando Kanban:** <span style='color:#10b981; font-weight:bold;'>{k_sel}</span> | **Material:** <span style='color:#3b82f6; font-weight:bold;'>{mat_sel}</span>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                    m_c1, m_c2, m_c3 = st.columns(3)
                    with m_c1:
                        m_centro = st.text_input("Centro", value=str(row['Centro'] if pd.notna(row['Centro']) else "A110"), key=f"m_centro_{k_sel}")
                        
                        tipo_kb_row = str(row['Tipo Kanban']).upper() if pd.notna(row['Tipo Kanban']) else "TARJETA"
                        idx_soporte = 0 if "GAVETA" in tipo_kb_row else 1
                        m_tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"], index=idx_soporte, key=f"m_soporte_{k_sel}")
                        
                        medio_row = str(row['Medio']).strip() if pd.notna(row['Medio']) else ""
                        if m_tipo_soporte == "GAVETA":
                            tam_ext = medio_row.replace("GAVETA", "").strip()
                            idx_tam = OPCIONES_GAVETA.index(tam_ext) if tam_ext in OPCIONES_GAVETA else 0
                            m_tam_gav = st.selectbox("Tamaño Gaveta", OPCIONES_GAVETA, index=idx_tam, key=f"m_gav_{k_sel}")
                            m_medio_str = f"GAVETA {m_tam_gav}"
                        else:
                            idx_med = OPCIONES_SOPORTE_TARJETA.index(medio_row) if medio_row in OPCIONES_SOPORTE_TARJETA else 0
                            m_medio_str = st.selectbox("Medio Físico", OPCIONES_SOPORTE_TARJETA, index=idx_med, key=f"m_tarj_{k_sel}")

                    with m_c2:
                        alm_o_val = str(row['Almacén Origen']).strip() if pd.notna(row['Almacén Origen']) else "L010"
                        alm_d_val = str(row['Almacen Destino']).strip() if pd.notna(row['Almacen Destino']) else "P140"
                        
                        idx_alm_o = LISTA_ALMACENES.index(alm_o_val) if alm_o_val in LISTA_ALMACENES else LISTA_ALMACENES.index("L010")
                        idx_alm_d = LISTA_ALMACENES.index(alm_d_val) if alm_d_val in LISTA_ALMACENES else LISTA_ALMACENES.index("P140")
                        
                        m_almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=idx_alm_o, key=f"m_alm_o_{k_sel}")
                        m_almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=idx_alm_d, key=f"m_alm_d_{k_sel}")
                        
                        m_es_interno = (m_almacen_origen != "L010")
                        p_orig_val = str(row['Puesto trabajo Origen']).strip() if pd.notna(row['Puesto trabajo Origen']) else "-"
                        
                        if m_es_interno:
                            opts_p_orig = ["-- Seleccionar --"] + ALMACENES_PUESTOS.get(m_almacen_origen, [])
                            idx_p_o = opts_p_orig.index(p_orig_val) if p_orig_val in opts_p_orig else 0
                            m_puesto_origen_sel = st.selectbox("Puesto Origen", opts_p_orig, index=idx_p_o, key=f"m_p_orig_{k_sel}")
                            m_puesto_origen = m_puesto_origen_sel if m_puesto_origen_sel != "-- Seleccionar --" else "-"
                        else:
                            st.text_input("Puesto Origen", value="- No aplica (Externo L010) -", disabled=True, key=f"m_p_orig_dis_{k_sel}")
                            m_puesto_origen = "-"

                        p_dest_val = str(row['Puesto de trabajo destino']).strip() if pd.notna(row['Puesto de trabajo destino']) else ""
                        opts_p_dest = ALMACENES_PUESTOS.get(m_almacen_destino, [])
                        if opts_p_dest:
                            idx_p_d = opts_p_dest.index(p_dest_val) if p_dest_val in opts_p_dest else 0
                            m_puesto_destino = st.selectbox("Puesto Destino", opts_p_dest, index=idx_p_d, key=f"m_p_dest_{k_sel}")
                        else:
                            m_puesto_destino = st.text_input("Puesto Destino", value=p_dest_val, key=f"m_p_dest_txt_{k_sel}").upper().strip()

                    with m_c3:
                        try:
                            val_repo_init = float(row['Cantidad Reposicion'])
                        except (ValueError, TypeError):
                            val_repo_init = float(pkg_ref or 0.0)
                            
                        m_cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=val_repo_init, step=1.0, key=f"m_cant_r_{k_sel}")
                        
                        if m_tipo_soporte == "GAVETA":
                            m_cant_pp = st.number_input("Cantidad Punto Pedido", value=m_cant_repo, disabled=True, key=f"m_cant_p_g_{k_sel}")
                        else:
                            try:
                                val_pp_init = float(row['Cantidad Punto de Pedido'])
                            except (ValueError, TypeError):
                                val_pp_init = 0.0
                            m_cant_pp = st.number_input("Cantidad Punto Pedido", min_value=0.0, value=val_pp_init, step=1.0, key=f"m_cant_p_t_{k_sel}")

                        unidades_lista = ["UN", "M", "L", "KG"]
                        un_val = str(row['Unidad Reposicion']).strip() if pd.notna(row['Unidad Reposicion']) else "UN"
                        idx_un = unidades_lista.index(un_val) if un_val in unidades_lista else 0
                        m_unidad = st.selectbox("Unidad Base", unidades_lista, index=idx_un, key=f"m_un_{k_sel}")
                        
                        try:
                            val_dias_init = int(row['Tiempo preparación abast. (en días)'])
                        except (ValueError, TypeError):
                            val_dias_init = 1
                        m_dias = st.number_input("Días Abastecimiento", min_value=0, value=val_dias_init, key=f"m_dias_{k_sel}")

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Guardar Cambios del Kanban", type="primary", key=f"btn_save_{k_sel}"):
                        if not m_puesto_destino:
                            st.session_state['msj_mod'] = ('error', "NO SE PUDO MODIFICAR: El Puesto Destino es obligatorio.")
                            st.rerun()
                        elif pkg_ref is not None and pkg_ref > 0 and (float(m_cant_repo) <= 0 or float(m_cant_repo) % float(pkg_ref) != 0):
                            st.session_state['msj_mod'] = ('error', f"NO SE PUDO MODIFICAR: La Cantidad de Reposición ({m_cant_repo}) no respeta el Lote de Packaging ({int(pkg_ref)} un.). Debe ser múltiplo de {int(pkg_ref)}.")
                            st.rerun()
                        elif m_tipo_soporte == "TARJETA" and float(m_cant_pp) >= float(m_cant_repo):
                            st.session_state['msj_mod'] = ('error', f"NO SE PUDO MODIFICAR: En Tipo TARJETA, Punto de Pedido ({m_cant_pp}) debe ser menor a Reposición ({m_cant_repo}).")
                            st.rerun()
                        else:
                            usr_act = st.session_state['usuario_email']
                            idx = df_live[df_live['N° Etiquetas'] == k_sel].index[0]
                            
                            cant_pp_final = m_cant_repo if m_tipo_soporte == "GAVETA" else m_cant_pp
                            
                            cambios_detectados = []
                            mapeo_campos = [
                                ('Centro', m_centro),
                                ('Tipo Kanban', m_tipo_soporte),
                                ('Medio', m_medio_str),
                                ('Almacén Origen', m_almacen_origen),
                                ('Almacen Destino', m_almacen_destino),
                                ('Puesto trabajo Origen', m_puesto_origen),
                                ('Puesto de trabajo destino', m_puesto_destino),
                                ('Cantidad Reposicion', m_cant_repo),
                                ('Cantidad Punto de Pedido', cant_pp_final),
                                ('Unidad Reposicion', m_unidad),
                                ('Tiempo preparación abast. (en días)', m_dias)
                            ]
                            
                            for col_nombre, val_nuevo in mapeo_campos:
                                val_viejo = df_live.loc[idx, col_nombre]
                                str_v = str(int(val_viejo)) if isinstance(val_viejo, (int, float)) and pd.notna(val_viejo) and float(val_viejo).is_integer() else str(val_viejo)
                                str_n = str(int(val_nuevo)) if isinstance(val_nuevo, (int, float)) and float(val_nuevo).is_integer() else str(val_nuevo)
                                
                                if str_v.strip() != str_n.strip():
                                    cambios_detectados.append(f"{col_nombre}: '{str_v}' ➔ '{str_n}'")
                            
                            texto_detalle_cambios = " | ".join(cambios_detectados) if cambios_detectados else "Sin cambios de valores"

                            df_live.loc[idx, 'Centro'] = m_centro
                            df_live.loc[idx, 'Tipo Kanban'] = m_tipo_soporte
                            df_live.loc[idx, 'Medio'] = m_medio_str
                            df_live.loc[idx, 'Almacén Origen'] = m_almacen_origen
                            df_live.loc[idx, 'Almacen Destino'] = m_almacen_destino
                            df_live.loc[idx, 'Puesto trabajo Origen'] = m_puesto_origen
                            df_live.loc[idx, 'Puesto de trabajo destino'] = m_puesto_destino
                            df_live.loc[idx, 'Cantidad Reposicion'] = m_cant_repo
                            df_live.loc[idx, 'Cantidad Punto de Pedido'] = cant_pp_final
                            df_live.loc[idx, 'Unidad Reposicion'] = m_unidad
                            df_live.loc[idx, 'Tiempo preparación abast. (en días)'] = m_dias
                            df_live.loc[idx, 'Fecha Modificación'] = obtener_fecha_hora_arg()
                            df_live.loc[idx, 'Usuario Modificación'] = usr_act
                            
                            actualizar_base_kanbans(df_live)
                            
                            registrar_log("ACTUALIZO", k_sel, mat_sel, m_medio_str, m_almacen_destino, m_puesto_destino, usr_act, detalle_cambio=texto_detalle_cambios)
                            crear_solicitud_tracker(mat_sel, k_sel, df_live.loc[idx, 'Tipo Etiqueta'], m_puesto_destino, m_medio_str, "ACTUALIZACIÓN", "IMPRIMIR / REEMPLAZAR", usr_act)
                            
                            st.session_state['msj_mod'] = ('success', f"CÓDIGO {k_sel} MODIFICADO CON EXITO")
                            st.rerun()
                else:
                    st.warning(f"⚠️ No se encontraron Kanbans activos para el criterio: **{busqueda}**")
            else:
                st.info("👆 Ingrese un código de material o número K arriba para buscar y editar.")

        with m_col_right:
            st.subheader("🗑️ Eliminar Kanban")
            
            st.markdown("""
            <div style="background-color: rgba(234, 179, 8, 0.12); border: 1px solid #eab308; padding: 12px; border-radius: 8px; color: #fde047; font-size: 0.88rem; margin-bottom: 15px;">
                ⚠️ Al eliminar un Kanban, su código K se libera y se registra en la auditoría.
            </div>
            """, unsafe_allow_html=True)
            
            opciones_del_k = [
                f"{r['N° Etiquetas']} | Mat: {r['Material']} | Puesto: {r['Puesto de trabajo destino']}"
                for _, r in df_live.iterrows()
            ]
            
            k_del_fmt = st.selectbox("Seleccione Código K a eliminar:", ["-- Seleccionar --"] + opciones_del_k, key="k_del_select")
            
            if st.button("🗑️ Eliminar Definitivamente", use_container_width=True) and k_del_fmt != "-- Seleccionar --":
                k_del_sel = k_del_fmt.split(" | ")[0].strip()
                row_del = df_live[df_live['N° Etiquetas'] == k_del_sel].iloc[0]
                mat_del = str(row_del['Material'])
                puesto_del = str(row_del['Puesto de trabajo destino'])
                medio_del = str(row_del['Medio'] or "SIN MEDIO DEFINIDO")
                tipo_del = str(row_del['Tipo Etiqueta'])
                usr_act = st.session_state['usuario_email']
                
                df_nuevo_global = df_live[df_live['N° Etiquetas'] != k_del_sel]
                actualizar_base_kanbans(df_nuevo_global)
                
                registrar_log("ELIMINO", k_del_sel, mat_del, medio_del, str(row_del['Almacen Destino']), puesto_del, usr_act)
                crear_solicitud_tracker(mat_del, k_del_sel, tipo_del, puesto_del, medio_del, "BAJA / ELIMINACIÓN", "RETIRAR KB", usr_act)
                
                st.session_state['msj_mod'] = ('success', f"CÓDIGO {k_del_sel} ELIMINADO DE TABLA Z")
                st.rerun()

# ==========================================
# VISTA: PANEL KPIS & MÉTRICAS
# ==========================================
tab_kpis = obtener_tab("📈 Panel KPIs & Métricas")
if tab_kpis:
    with tab_kpis:
        st.subheader("📊 Panel Interactivo de KPIs y Analítica")
        df_logs_kpi = cargar_logs()
        df_k_live = obtener_base_kanbans()
        df_tr_kpi = cargar_tracker()
        
        # --- FILTROS DE ANÁLISIS ---
        with st.expander("🔍 Filtros de Análisis", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                if not df_logs_kpi.empty:
                    df_logs_kpi['Fecha_dt'] = pd.to_datetime(df_logs_kpi['Fecha_Hora'], errors='coerce')
                    min_d = df_logs_kpi['Fecha_dt'].dropna().min().date()
                    max_d = df_logs_kpi['Fecha_dt'].dropna().max().date()
                else:
                    min_d = max_d = datetime.now().date()
                rango_fechas_kpi = st.date_input("Rango de Fechas:", value=(min_d, max_d), key="kpi_dates")
            with f_col2:
                f_alm = st.selectbox("Almacén Destino:", ["Todos"] + list(df_k_live['Almacen Destino'].dropna().unique()), key="kpi_alm")
            with f_col3:
                f_usr = st.selectbox("Usuario Responsable:", ["Todos"] + (list(df_logs_kpi['Usuario'].dropna().unique()) if not df_logs_kpi.empty else []), key="kpi_usr")

        # Aplicar filtros a los logs
        df_logs_filtrado = df_logs_kpi.copy() if not df_logs_kpi.empty else pd.DataFrame()
        if not df_logs_filtrado.empty and isinstance(rango_fechas_kpi, tuple) and len(rango_fechas_kpi) == 2:
            fi, ff = rango_fechas_kpi
            df_logs_filtrado = df_logs_filtrado[(df_logs_filtrado['Fecha_dt'].dt.date >= fi) & (df_logs_filtrado['Fecha_dt'].dt.date <= ff)]
            if f_alm != "Todos": df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Almacén_Destino'] == f_alm]
            if f_usr != "Todos": df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Usuario'] == f_usr]

        # Métricas generales del período
        c_creados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'CREACIÓN']) if not df_logs_filtrado.empty else 0
        c_actualizados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'MODIFICACIÓN']) if not df_logs_filtrado.empty else 0
        c_eliminados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'ELIMINACIÓN']) if not df_logs_filtrado.empty else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Movimientos Período", len(df_logs_filtrado))
        m2.metric("✨ Creados", c_creados)
        m3.metric("✏️ Modificados", c_actualizados)
        m4.metric("🗑️ Eliminados", c_eliminados)
        st.markdown("---")

        # --- SECCIÓN 1: PUESTOS Y EVOLUCIÓN ---
        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("##### 🏭 Top Puestos de Trabajo Destino")
            if not df_k_live.empty and 'Puesto de trabajo destino' in df_k_live.columns:
                df_puestos = df_k_live['Puesto de trabajo destino'].value_counts().reset_index()
                df_puestos.columns = ['Puesto Destino', 'Cantidad']
                fig_puestos = px.bar(df_puestos.head(10), x='Cantidad', y='Puesto Destino', orientation='h', text='Cantidad', template="plotly_dark", color='Cantidad', color_continuous_scale='Reds')
                fig_puestos.update_layout(yaxis={'categoryorder': 'total ascending'}, height=320, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_puestos, use_container_width=True)
            else:
                st.info("Sin información de puestos de trabajo.")

        with g_col2:
            st.markdown("##### 📈 Evolución de Movimientos")
            if not df_logs_filtrado.empty:
                df_logs_filtrado['Fecha_Dia'] = df_logs_filtrado['Fecha_dt'].dt.strftime('%Y-%m-%d')
                df_evolucion = df_logs_filtrado.groupby(['Fecha_Dia', 'Acción']).size().reset_index(name='Cantidad')
                fig_evol = px.line(df_evolucion, x='Fecha_Dia', y='Cantidad', color='Acción', markers=True, template="plotly_dark", color_discrete_map={'CREACIÓN': '#10b981', 'MODIFICACIÓN': '#f59e0b', 'ELIMINACIÓN': '#ef4444'})
                fig_evol.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Fecha", yaxis_title="Operaciones")
                st.plotly_chart(fig_evol, use_container_width=True)
            else:
                st.info("Sin registros en este rango.")

        st.markdown("---")

        # --- SECCIÓN 2: TIPO DE KANBAN & SOLICITUDES NO FINALIZADAS ---
        kpi_c1, kpi_c2 = st.columns(2)

        with kpi_c1:
            st.markdown("##### 🍰 Distribución por Tipo de Kanban (Tarjeta vs Gaveta)")
            if not df_k_live.empty and 'Tipo Kanban' in df_k_live.columns:
                # Lectura explícita de la columna 'Tipo Kanban'
                series_tipo = df_k_live['Tipo Kanban'].fillna("NO DEFINIDO").replace("", "NO DEFINIDO")
                df_tipo = series_tipo.value_counts().reset_index()
                df_tipo.columns = ['Tipo Kanban', 'Cantidad']

                if not df_tipo.empty and df_tipo['Cantidad'].sum() > 0:
                    fig_pie = px.pie(
                        df_tipo, 
                        names='Tipo Kanban', 
                        values='Cantidad', 
                        hole=0.4,
                        template="plotly_dark",
                        color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b']
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(height=330, margin=dict(l=20, r=20, t=30, b=20), showlegend=True)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("No se encontraron registros en el tipo de Kanban.")
            else:
                st.info("No hay datos disponibles sobre el tipo de Kanban.")

        with kpi_c2:
            st.markdown("##### ⏳ Solicitudes Pendientes / No Finalizadas")
            if not df_tr_kpi.empty:
                df_pendientes = df_tr_kpi[df_tr_kpi['Estado_Fisico'] != 'Entregado'].copy()
                
                if not df_pendientes.empty:
                    df_est_pend = df_pendientes['Estado_Fisico'].value_counts().reset_index()
                    df_est_pend.columns = ['Estado Físico', 'Cantidad']

                    fig_pend = px.bar(
                        df_est_pend,
                        x='Estado Físico',
                        y='Cantidad',
                        text='Cantidad',
                        color='Estado Físico',
                        template="plotly_dark",
                        color_discrete_sequence=['#f59e0b', '#3b82f6', '#ef4444']
                    )
                    fig_pend.update_layout(height=330, margin=dict(l=20, r=20, t=30, b=20), showlegend=False)
                    st.plotly_chart(fig_pend, use_container_width=True)
                else:
                    st.success("🎉 ¡Todas las solicitudes en el Tracker se encuentran finalizadas!")
            else:
                st.info("No hay solicitudes registradas en el Tracker Logístico.")

        st.markdown("---")

        # --- SECCIÓN 3: MEDICIÓN DE TIEMPOS LOGÍSTICOS ---
        st.markdown("##### ⏱️ Medición de Tiempos de Respuesta (Tracker Logístico)")
        
        if not df_tr_kpi.empty:
            df_t = df_tr_kpi.copy()

            cols_fechas = ['Fecha_Solicitud', 'Fecha_Impresion', 'Fecha_Finalizacion']
            for col in cols_fechas:
                if col in df_t.columns:
                    df_t[col] = pd.to_datetime(df_t[col], errors='coerce')

            if 'Fecha_Solicitud' in df_t.columns:
                if 'Fecha_Impresion' in df_t.columns:
                    df_t['Hs_Solicitud_a_SAP_Imp'] = (df_t['Fecha_Impresion'] - df_t['Fecha_Solicitud']).dt.total_seconds() / 3600
                if 'Fecha_Finalizacion' in df_t.columns:
                    df_t['Hs_Imp_a_AccionFisica'] = (df_t['Fecha_Finalizacion'] - df_t['Fecha_Impresion']).dt.total_seconds() / 3600
                    df_t['Hs_Ciclo_Total'] = (df_t['Fecha_Finalizacion'] - df_t['Fecha_Solicitud']).dt.total_seconds() / 3600

                prom_imp = df_t['Hs_Solicitud_a_SAP_Imp'].mean() if 'Hs_Solicitud_a_SAP_Imp' in df_t.columns else None
                prom_fis = df_t['Hs_Imp_a_AccionFisica'].mean() if 'Hs_Imp_a_AccionFisica' in df_t.columns else None
                prom_tot = df_t['Hs_Ciclo_Total'].mean() if 'Hs_Ciclo_Total' in df_t.columns else None

                t1, t2, t3 = st.columns(3)
                t1.metric("⏱️ Promedio Solicitud ➔ SAP / Impresión", f"{prom_imp:.1f} hs" if pd.notnull(prom_imp) else "N/A")
                t2.metric("⏱️ Promedio Impresión ➔ Acción Física", f"{prom_fis:.1f} hs" if pd.notnull(prom_fis) else "N/A")
                t3.metric("⏱️ Promedio Ciclo Completo Total", f"{prom_tot:.1f} hs" if pd.notnull(prom_tot) else "N/A")

                df_t['Fecha_Corta'] = df_t['Fecha_Solicitud'].dt.strftime('%Y-%m-%d')
                if df_t['Fecha_Corta'].dropna().any():
                    df_prom_diario = df_t.groupby('Fecha_Corta')[['Hs_Solicitud_a_SAP_Imp', 'Hs_Imp_a_AccionFisica']].mean().reset_index()
                    df_melted = df_prom_diario.melt(
                        id_vars=['Fecha_Corta'], 
                        value_vars=['Hs_Solicitud_a_SAP_Imp', 'Hs_Imp_a_AccionFisica'], 
                        var_name='Etapa', 
                        value_name='Horas Promedio'
                    )
                    df_melted['Etapa'] = df_melted['Etapa'].map({
                        'Hs_Solicitud_a_SAP_Imp': 'Solicitud a SAP / Impresión', 
                        'Hs_Imp_a_AccionFisica': 'Impresión a Acción Física'
                    })

                    fig_tiempos = px.bar(
                        df_melted, 
                        x='Fecha_Corta', 
                        y='Horas Promedio', 
                        color='Etapa', 
                        barmode='group',
                        template="plotly_dark", 
                        title="Tiempo Promedio de Respuesta por Fecha de Solicitud (Horas)",
                        labels={'Fecha_Corta': 'Fecha de Solicitud', 'Horas Promedio': 'Horas Promedio'}
                    )
                    fig_tiempos.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_tiempos, use_container_width=True)
            else:
                st.info("Las columnas de fechas necesarias no están presentes en la base del Tracker.")
        else:
            st.info("No hay datos suficientes en el Tracker Logístico para calcular métricas de tiempo.")
# ==========================================
# VISTA: TRACKER LOGÍSTICO
# ==========================================
tab_tracker = obtener_tab("🚚 Tracker de Ejecución Logística") or obtener_tab("🚚 Estado de Solicitudes")
if tab_tracker:
    with tab_tracker:
        st.subheader("🚚 Cola de Ejecución Logística & Estado SAP / Impresión")
        df_tr = cargar_tracker()
        
        if df_tr.empty:
            st.info("No hay solicitudes de actualización pendientes en la cola.")
        else:
            filtro_est = st.radio("Filtrar Solicitudes:", ["Pendientes (Incompletas)", "Todas las Solicitudes", "Finalizadas"], horizontal=True)
            df_tr_show = df_tr.copy()
            if filtro_est == "Pendientes (Incompletas)":
                df_tr_show = df_tr_show[df_tr_show['Estado_Fisico'] != 'Entregado']
            elif filtro_est == "Finalizadas":
                df_tr_show = df_tr_show[df_tr_show['Estado_Fisico'] == 'Entregado']

            st.dataframe(df_tr_show, use_container_width=True)
            
            if rol_actual in ["Logistica", "Procesos"]:
                st.markdown("---")
                st.subheader("⚡ Actualizar Estado de Solicitud (Logística)")
                
                sol_ids = df_tr_show['ID_Solicitud'].tolist() if not df_tr_show.empty else []
                if sol_ids:
                    col_tr1, col_tr2, col_tr3 = st.columns(3)
                    with col_tr1:
                        sol_sel = st.selectbox("Seleccione ID Solicitud a actualizar:", sol_ids)
                        row_tr = df_tr[df_tr['ID_Solicitud'] == sol_sel].iloc[0]
                        st.caption(f"**Material:** {row_tr['Material']} | **Código K:** {row_tr['Código_K']} | **Acción:** {row_tr['Acción_Requerida']}")

                    with col_tr2:
                        chk_sap = st.checkbox("Cargado en SAP", value=(str(row_tr['Cargado_SAP']) == 'SI'))
                        chk_imp = st.checkbox("Impreso", value=(str(row_tr['Impreso']) == 'SI'))
                        
                    with col_tr3:
                        curr_est = str(row_tr['Estado_Fisico'])
                        idx_est = ["Pendiente", "En Proceso", "Entregado"].index(curr_est) if curr_est in ["Pendiente", "En Proceso", "Entregado"] else 0
                        est_fisico = st.selectbox("Estado Físico en Puesto:", ["Pendiente", "En Proceso", "Entregado"], index=idx_est)
                        obs_tr = st.text_input("Observaciones:", value=str(row_tr['Observación'] if row_tr['Observación'] != '-' else ''))

                    if st.button("💾 Actualizar Estado de Solicitud", type="primary"):
                        idx_tr = df_tr[df_tr['ID_Solicitud'] == sol_sel].index[0]
                        now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        df_tr = df_tr.astype(object)
                        df_tr.loc[idx_tr, 'Cargado_SAP'] = "SI" if chk_sap else "NO"
                        df_tr.loc[idx_tr, 'Impreso'] = "SI" if chk_imp else "NO"
                        if chk_imp and str(df_tr.loc[idx_tr, 'Fecha_Impresion']) in ["-", "None", "nan", ""]:
                            df_tr.loc[idx_tr, 'Fecha_Impresion'] = now_str
                            
                        df_tr.loc[idx_tr, 'Estado_Fisico'] = str(est_fisico)
                        if est_fisico == "Entregado" and str(df_tr.loc[idx_tr, 'Fecha_Finalizacion']) in ["-", "None", "nan", ""]:
                            df_tr.loc[idx_tr, 'Fecha_Finalizacion'] = now_str
                            
                        df_tr.loc[idx_tr, 'Observación'] = str(obs_tr) if obs_tr.strip() else "-"
                        guardar_tracker(df_tr)
                        st.success(f"✅ Solicitud **{sol_sel}** actualizada con éxito.")
                        st.rerun()

# ==========================================
# VISTA: DATOS DE KANBAN
# ==========================================
tab_export = obtener_tab("📊 Datos de Kanban")
if tab_export:
    with tab_export:
        st.subheader("📊 Datos de Kanban")
        df_export_live = obtener_base_kanbans()
        if not df_export_live.empty:
            # --- FILTROS DE BÚSQUEDA PARCIAL ---
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filtro_k = st.text_input("🔍 Filtro por Código Kanban (ej. 7634):", placeholder="Buscar fragmento de código K...").strip().upper()
            with col_f2:
                filtro_mat = st.text_input("🔍 Filtro por Código de Material (ej. 10939):", placeholder="Buscar fragmento de código Material...").strip().upper()

            df_filtrado_export = df_export_live.copy()
            if filtro_k:
                df_filtrado_export = df_filtrado_export[
                    df_filtrado_export['N° Etiquetas'].astype(str).str.upper().str.contains(filtro_k, na=False)
                ]
            if filtro_mat:
                df_filtrado_export = df_filtrado_export[
                    df_filtrado_export['Material'].astype(str).str.upper().str.contains(filtro_mat, na=False)
                ]

            st.dataframe(df_filtrado_export, use_container_width=True)
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado_export.to_excel(writer, sheet_name=SHEET_NAME, index=False)
            excel_bytes = output.getvalue()
            
            st.download_button(
                label="📥 Descargar Datos de Kanban (.xlsx)", 
                data=excel_bytes, 
                file_name="Datos_Kanban_Actualizada.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                type="primary"
            )
        else:
            st.warning("⚠️ No se pudieron cargar los datos de la base de Kanban.")

# ==========================================
# VISTA: HISTORIAL AUDITORÍA
# ==========================================
tab_historial = obtener_tab("📜 Historial Auditoría")
if tab_historial:
    with tab_historial:
        st.subheader("📜 Historial Completo de Modificaciones")
        df_logs_all = cargar_logs()
        if not df_logs_all.empty:
            st.dataframe(df_logs_all.sort_values(by="Fecha_Hora", ascending=False), use_container_width=True)
        else:
            st.info("No hay registros en el historial de auditoría.")
        
        usr_actual_aud = st.session_state.get('usuario_email')
        if usr_actual_aud == "jairc@crucianelli.com":
            st.markdown("---")
            with st.expander("🔒 Zona Exclusiva Administrador - Puesta a Cero (Jair)"):
                st.warning("⚠️ Esta acción eliminará los registros de Auditoría y Tracker Logístico.")
                pass_confirm = st.text_input("Confirme su contraseña para ejecutar la limpieza:", type="password", key="pass_del_hist")
                if st.button("🔴 Borrar Historiales de Prueba", type="primary"):
                    pass_real = USUARIOS_REGISTRADOS.get(usr_actual_aud, {}).get("pass")
                    if pass_confirm == pass_real:
                        limpiar_historiales_de_prueba()
                        st.success("✅ Historiales y Tracker limpiados correctamente.")
                        st.rerun()
                    else:
                        st.error("❌ Contraseña de confirmación incorrecta. Operación cancelada.")

# ==========================================
# VISTA: MI PERFIL
# ==========================================
tab_perfil = obtener_tab("👤 Mi Perfil")
if tab_perfil:
    with tab_perfil:
        st.subheader("👤 Mi Perfil de Usuario")
        usr_actual = st.session_state['usuario_email']
        
        col_p1, col_p2 = st.columns([1, 2])
        with col_p1:
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            st.markdown("#### 📄 Datos de la Cuenta")
            st.write(f"**Usuario / Correo:** {usr_actual}")
            st.write(f"**Rol Asignado:** `{rol_actual.upper()}`")
            st.write(f"**Dominio:** Crucianelli S.A.")
            st.write(f"**Último Acceso:** {obtener_fecha_hora_arg()}")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("🔑 Cambiar Contraseña Directa"):
                pass_curr = st.text_input("Contraseña Actual:", type="password", key="p_curr")
                pass_new1 = st.text_input("Nueva Contraseña:", type="password", key="p_new1")
                pass_new2 = st.text_input("Confirmar Nueva Contraseña:", type="password", key="p_new2")
                
                if st.button("💾 Actualizar Contraseña"):
                    if not pass_curr or not pass_new1 or not pass_new2:
                        st.error("❌ Complete todos los campos.")
                    elif pass_new1 != pass_new2:
                        st.error("❌ Las nuevas contraseñas no coinciden.")
                    elif USUARIOS_REGISTRADOS.get(usr_actual, {}).get("pass") != pass_curr:
                        st.error("❌ La contraseña actual es incorrecta.")
                    else:
                        USUARIOS_REGISTRADOS[usr_actual]["pass"] = pass_new1
                        guardar_usuarios(USUARIOS_REGISTRADOS)
                        st.success("✅ ¡Contraseña actualizada con éxito!")

        with col_p2:
            st.markdown("#### 📜 Mi Historial de Actividad Reciente")
            df_logs_all = cargar_logs()
            if not df_logs_all.empty:
                df_my_logs = df_logs_all[df_logs_all['Usuario'] == usr_actual].sort_values(by="Fecha_Hora", ascending=False)
                if not df_my_logs.empty:
                    st.dataframe(df_my_logs, use_container_width=True)
                else:
                    st.info("Aún no has registrado movimientos en el sistema.")
            else:
                st.info("No existen registros en el historial.")
