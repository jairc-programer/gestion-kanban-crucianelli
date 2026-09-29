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
LIVE_DB_FILE = "TablaZ_live.csv"
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
    
    # LOGÍSTICA
    "mlopez@crucianelli.com": "Logistica", "recepcion3@crucianelli.com": "Logistica",
    "gpereyra@crucianelli.com": "Logistica", "jporta@crucianelli.com": "Logistica",
    "spetetta@crucianelli.com": "Logistica", "gfiianchini@crucianelli.com": "Logistica",
    "ileon@crucianelli.com": "Logistica",
    
    # CONSULTA
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
# MANEJO CENTRALIZADO CON PERSISTENCIA VIVA
# ==========================================
def cargar_base_desde_disco():
    if os.path.exists(LIVE_DB_FILE):
        try:
            df = pd.read_csv(LIVE_DB_FILE, dtype=str)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = None
            df['Material'] = df['Material'].fillna('').astype(str).str.strip().str.upper()
            df['N° Etiquetas'] = df['N° Etiquetas'].fillna('').astype(str).str.strip().str.upper()
            return df[COLUMNS].reset_index(drop=True)
        except Exception:
            pass

    if os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME, dtype=str)
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
            df = df[COLUMNS].reset_index(drop=True)
            df.to_csv(LIVE_DB_FILE, index=False)
            return df
        except Exception:
            return pd.DataFrame(columns=COLUMNS)
    return pd.DataFrame(columns=COLUMNS)

def obtener_base_kanbans(forzar=False):
    if 'df_kanbans_global' not in st.session_state or forzar:
        st.session_state['df_kanbans_global'] = cargar_base_desde_disco()
    return st.session_state['df_kanbans_global']

def actualizar_base_kanbans(nuevo_df):
    df_limpio = nuevo_df.astype(str).reset_index(drop=True)
    st.session_state['df_kanbans_global'] = df_limpio
    
    try:
        df_limpio.to_csv(LIVE_DB_FILE, index=False)
    except Exception as e:
        st.error(f"⚠️ Error en persistencia CSV viva: {e}")

    try:
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_limpio.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    except Exception:
        pass

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
            df_logs = pd.read_csv(LOG_FILE, on_bad_lines='skip', dtype=str)
            for col in LOG_COLUMNS:
                if col not in df_logs.columns:
                    df_logs[col] = "-"
            mapeo_acciones = {
                'CREAR': 'CREACIÓN', 'CREO': 'CREACIÓN', 'CREACION': 'CREACIÓN',
                'MODIFICAR': 'MODIFICACIÓN', 'ACTUALIZO': 'MODIFICACIÓN', 'MODIFICACION': 'MODIFICACIÓN',
                'ELIMINAR': 'ELIMINACIÓN', 'ELIMINO': 'ELIMINACIÓN', 'ELIMINACION': 'ELIMINACIÓN'
            }
            df_logs['Acción'] = df_logs['Acción'].astype(str).str.upper().map(lambda x: mapeo_acciones.get(x, x))
            return df_logs[LOG_COLUMNS].fillna("-")
        except Exception:
            return pd.DataFrame(columns=LOG_COLUMNS)
    return pd.DataFrame(columns=LOG_COLUMNS)

def registrar_log(accion, codigo_k, material, medio, alm_dest, puesto_dest, detalle_cambio, usuario):
    now = obtener_fecha_hora_arg()
    df_actual = cargar_logs()
    if pd.isna(medio) or str(medio).strip() in ["None", "nan", "N/A", ""]:
        medio = "SIN MEDIO DEFINIDO"
    
    mapeo_guardado = {'CREO': 'CREACIÓN', 'ACTUALIZO': 'MODIFICACIÓN', 'ELIMINO': 'ELIMINACIÓN'}
    accion_norm = mapeo_guardado.get(accion, accion)

    nuevo_log = pd.DataFrame([{
        "Fecha_Hora": now, "Acción": accion_norm, "Código_K": str(codigo_k),
        "Material": str(material), "Medio": str(medio), "Almacén_Destino": str(alm_dest),
        "Puesto_Destino": str(puesto_dest), "Detalle_Cambio": str(detalle_cambio), "Usuario": str(usuario)
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
    now_date = datetime.now(ARG_TZ).strftime("%Y-%m-%d")
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

df_kanbans = obtener_base_kanbans(forzar=True)
dict_pkg = cargar_packaging()
rol_actual = st.session_state.get('usuario_rol', 'Consulta')

# ==========================================
# CABECERA Y BOTONES DE CONTROL GLOBAL
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

_, col_ref, col_logout = st.columns([4, 1.2, 1])

with col_ref:
    if st.button("🔄 Actualizar Datos", use_container_width=True, help="Refresca los datos en tiempo real sin cerrar sesión"):
        obtener_base_kanbans(forzar=True)
        st.success("⚡ ¡Datos sincronizados!")
        st.rerun()

with col_logout:
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['usuario_email'] = None
        st.session_state['usuario_rol'] = None
        st.session_state.pop('df_kanbans_global', None)
        st.rerun()

df_kanbans = obtener_base_kanbans()
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
    lista_tabs = ["📈 Panel KPIs & Métricas", "🚚 Tracker de Ejecución Logística", "➕ Crear Nuevo Kanban", "✏️ Modificar y Eliminar", "📊 Consulta y Exportar Tabla Z (SAP)", "📜 Historial Auditoría", "👤 Mi Perfil"]
elif rol_actual == "Logistica":
    lista_tabs = ["🚚 Tracker de Ejecución Logística", "📈 Panel KPIs & Métricas", "📊 Consulta y Exportar Tabla Z (SAP)", "📜 Historial Auditoría", "👤 Mi Perfil"]
else:
    lista_tabs = ["📈 Panel KPIs & Métricas", "🚚 Estado de Solicitudes", "📊 Consulta y Exportar Tabla Z (SAP)", "👤 Mi Perfil"]

tabs = st.tabs(lista_tabs)

def obtener_tab(nombre):
    if nombre in lista_tabs:
        return tabs[lista_tabs.index(nombre)]
    return None

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
        
        # --- FILTROS GLOBALES DE KPIS ---
        with st.expander("🔍 Filtros de Análisis", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            
            with f_col1:
                if not df_logs_kpi.empty:
                    df_logs_kpi['Fecha_dt'] = pd.to_datetime(df_logs_kpi['Fecha_Hora'], errors='coerce')
                    min_d = df_logs_kpi['Fecha_dt'].dropna().min().date()
                    max_d = df_logs_kpi['Fecha_dt'].dropna().max().date()
                else:
                    min_d = max_d = datetime.now().date()
                rango_fechas_kpi = st.date_input("Rango de Fechas (Historial):", value=(min_d, max_d), key="kpi_dates")

            with f_col2:
                almacenes_unicos = ["Todos"] + sorted([str(x) for x in df_k_live['Almacen Destino'].dropna().unique() if str(x).strip() != ""])
                f_alm = st.selectbox("Almacén Destino:", almacenes_unicos, key="kpi_alm")

            with f_col3:
                if f_alm != "Todos":
                    puestos_disp = ["Todos"] + sorted([str(x) for x in df_k_live[df_k_live['Almacen Destino'] == f_alm]['Puesto de trabajo destino'].dropna().unique() if str(x).strip() != ""])
                else:
                    puestos_disp = ["Todos"] + sorted([str(x) for x in df_k_live['Puesto de trabajo destino'].dropna().unique() if str(x).strip() != ""])
                f_puesto = st.selectbox("Puesto de Trabajo Destino:", puestos_disp, key="kpi_puesto")

        # --- FILTRADO DE DATOS VIVOS (BASE KANBANS) ---
        df_k_filtrado = df_k_live.copy()
        if f_alm != "Todos":
            df_k_filtrado = df_k_filtrado[df_k_filtrado['Almacen Destino'] == f_alm]
        if f_puesto != "Todos":
            df_k_filtrado = df_k_filtrado[df_k_filtrado['Puesto de trabajo destino'] == f_puesto]

        # --- FILTRADO DE LOGS DE AUDITORÍA ---
        df_logs_filtrado = df_logs_kpi.copy() if not df_logs_kpi.empty else pd.DataFrame()
        if not df_logs_filtrado.empty and isinstance(rango_fechas_kpi, tuple) and len(rango_fechas_kpi) == 2:
            fi, ff = rango_fechas_kpi
            df_logs_filtrado = df_logs_filtrado[(df_logs_filtrado['Fecha_dt'].dt.date >= fi) & (df_logs_filtrado['Fecha_dt'].dt.date <= ff)]
            if f_alm != "Todos": 
                df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Almacén_Destino'] == f_alm]
            if f_puesto != "Todos": 
                df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Puesto_Destino'] == f_puesto]

        # --- FILTRADO DEL TRACKER ---
        df_tr_filtrado = df_tr_kpi.copy() if not df_tr_kpi.empty else pd.DataFrame()
        if not df_tr_filtrado.empty and f_puesto != "Todos":
            df_tr_filtrado = df_tr_filtrado[df_tr_filtrado['Puesto_Destino'] == f_puesto]

        # CÁLCULOS PENDIENTES DEL TRACKER
        if not df_tr_filtrado.empty:
            pend_sap = len(df_tr_filtrado[df_tr_filtrado['Cargado_SAP'] != 'SI'])
            pend_fisico = len(df_tr_filtrado[df_tr_filtrado['Estado_Fisico'] != 'Entregado'])
        else:
            pend_sap = 0
            pend_fisico = 0

        # --- MÉTRICAS SUPERIORES (TARJETAS) ---
        c_creados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'CREACIÓN']) if not df_logs_filtrado.empty else 0
        c_actualizados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'MODIFICACIÓN']) if not df_logs_filtrado.empty else 0
        c_eliminados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'ELIMINACIÓN']) if not df_logs_filtrado.empty else 0

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("KB Activos", len(df_k_filtrado))
        m2.metric("✨ Creados", c_creados)
        m3.metric("✏️ Modificados", c_actualizados)
        m4.metric("🗑️ Eliminados", c_eliminados)
        m5.metric("⏳ Pendiente SAP", pend_sap, delta=f"{pend_sap} requeridos", delta_color="inverse")
        m6.metric("🚚 Pend. Físico", pend_fisico, delta=f"{pend_fisico} requeridos", delta_color="inverse")
        st.markdown("---")

        # --- FILA 1 DE GRÁFICOS ---
        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            st.markdown("##### 📍 Kanban por Puestos de Trabajo")
            if not df_k_filtrado.empty:
                df_puestos = df_k_filtrado['Puesto de trabajo destino'].value_counts().reset_index()
                df_puestos.columns = ['Puesto Destino', 'Cantidad']
                fig_puestos = px.bar(
                    df_puestos.head(10), x='Cantidad', y='Puesto Destino', 
                    orientation='h', text='Cantidad', template="plotly_dark", 
                    color='Cantidad', color_continuous_scale='Reds'
                )
                fig_puestos.update_layout(yaxis={'categoryorder': 'total ascending'}, height=320, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_puestos, use_container_width=True)
            else:
                st.info("No hay datos de Kanbans para mostrar con los filtros aplicados.")

        with g_col2:
            st.markdown("##### 🏷️ Distribución por Tipo (Gaveta vs Tarjeta)")
            if not df_k_filtrado.empty:
                df_tipos = df_k_filtrado['Tipo Kanban'].value_counts().reset_index()
                df_tipos.columns = ['Tipo', 'Cantidad']
                fig_tipos = px.pie(
                    df_tipos, names='Tipo', values='Cantidad', hole=0.4,
                    template="plotly_dark", color='Tipo',
                    color_discrete_map={'GAVETA': '#ef4444', 'TARJETA': '#3b82f6'}
                )
                fig_tipos.update_traces(textinfo='percent+label+value')
                fig_tipos.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_tipos, use_container_width=True)
            else:
                st.info("No hay datos disponibles para el gráfico de tipos.")

        st.markdown("---")

        # --- FILA 2 DE GRÁFICOS ---
        g_col3, g_col4 = st.columns(2)

        with g_col3:
            st.markdown("##### 📈 Evolución de Movimientos")
            if not df_logs_filtrado.empty:
                df_logs_filtrado['Fecha_Dia'] = df_logs_filtrado['Fecha_dt'].dt.strftime('%Y-%m-%d')
                df_evolucion = df_logs_filtrado.groupby(['Fecha_Dia', 'Acción']).size().reset_index(name='Cantidad')
                fig_evol = px.line(
                    df_evolucion, x='Fecha_Dia', y='Cantidad', color='Acción', 
                    markers=True, template="plotly_dark", 
                    color_discrete_map={'CREACIÓN': '#10b981', 'MODIFICACIÓN': '#f59e0b', 'ELIMINACIÓN': '#ef4444'}
                )
                fig_evol.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Fecha", yaxis_title="Operaciones")
                st.plotly_chart(fig_evol, use_container_width=True)
            else:
                st.info("Sin registros de movimientos en el rango seleccionado.")

        with g_col4:
            st.markdown("##### ⏱️ Tiempos de Respuesta Logística (Lead Time Tracker)")
            if not df_tr_filtrado.empty:
                df_tr_f = df_tr_filtrado.copy()

                df_tr_f['f_sol'] = pd.to_datetime(df_tr_f['Fecha_Solicitud'], errors='coerce')
                df_tr_f['f_imp'] = pd.to_datetime(df_tr_f['Fecha_Impresion'], errors='coerce')
                df_tr_f['f_fin'] = pd.to_datetime(df_tr_f['Fecha_Finalizacion'], errors='coerce')

                # Calcular días de demora
                df_tr_f['Días Impresión'] = (df_tr_f['f_imp'] - df_tr_f['f_sol']).dt.days
                df_tr_f['Días Entrega Final'] = (df_tr_f['f_fin'] - df_tr_f['f_sol']).dt.days

                df_tiempos = df_tr_f.dropna(subset=['f_sol']).sort_values('f_sol')

                if not df_tiempos.empty and (df_tiempos['Días Impresión'].notna().any() or df_tiempos['Días Entrega Final'].notna().any()):
                    fig_time = px.line(
                        df_tiempos, x='Fecha_Solicitud', 
                        y=['Días Impresión', 'Días Entrega Final'],
                        markers=True, template="plotly_dark",
                        labels={'value': 'Días Transcurridos', 'variable': 'Hito Logístico'},
                        color_discrete_map={'Días Impresión': '#3b82f6', 'Días Entrega Final': '#10b981'}
                    )
                    fig_time.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Fecha Solicitud", yaxis_title="Días de Demora")
                    st.plotly_chart(fig_time, use_container_width=True)
                else:
                    st.info("Aún no hay solicitudes finalizadas/impresas para calcular tiempos de respuesta.")
            else:
                st.info("El Tracker de Ejecución Logística no contiene registros.")

        # --- FILA 3: ESTADO DE CUMPLIMIENTO / BACKLOG PENDIENTE ---
        st.markdown("---")
        st.markdown("##### 📌 Resumen de Carga y Ejecución Pendiente en Logística")
        
        if not df_tr_filtrado.empty:
            df_backlog = pd.DataFrame([
                {"Tarea Logística": "Pendiente Carga en SAP", "Cantidad": pend_sap},
                {"Tarea Logística": "Pendiente Entrega Físicamente", "Cantidad": pend_fisico}
            ])
            
            fig_backlog = px.bar(
                df_backlog, x='Cantidad', y='Tarea Logística', orientation='h',
                text='Cantidad', template="plotly_dark",
                color='Tarea Logística',
                color_discrete_map={
                    "Pendiente Carga en SAP": "#f59e0b",
                    "Pendiente Entrega Físicamente": "#ef4444"
                }
            )
            fig_backlog.update_layout(height=220, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            st.plotly_chart(fig_backlog, use_container_width=True)
        else:
            st.info("No hay backlog pendiente acumulado.")
# ==========================================
# VISTA: TRACKER DE EJECUCIÓN LOGÍSTICA
# ==========================================
tab_tracker = obtener_tab("🚚 Tracker de Ejecución Logística") or obtener_tab("🚚 Estado de Solicitudes")
if tab_tracker:
    with tab_tracker:
        st.subheader("🚚 Cola de Ejecución Logística & Estado SAP / Impresión")
        st.write("Gestiona la confirmación de carga en SAP, impresión física y entrega en puesto de trabajo.")
        
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
                        st.caption(f"**Material:** {row_tr['Material']} | **Código K:** {row_tr['Código_K']} | **Cambio:** {row_tr['Cambio']}")

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
                        now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d")
                        
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
# VISTA: CREAR KANBAN (CONTROLES BLINDADOS)
# ==========================================
tab_crear = obtener_tab("➕ Crear Nuevo Kanban")
if tab_crear:
    with tab_crear:
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.subheader("Alta de Nuevo Kanban")
        col1, col2, col3 = st.columns(3)
        with col1:
            centro = st.text_input("Centro", value="A110")
            material = st.text_input("Código de Material (ej. PB005075)", max_chars=9).upper().strip()
            pkg_sugerido = dict_pkg.get(material, None)
            if pkg_sugerido: st.info(f"📦 Lote Packaging: {pkg_sugerido} UN")
            tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"])
            medio_str = f"GAVETA {st.selectbox('Tamaño Gaveta', OPCIONES_GAVETA)}" if tipo_soporte == "GAVETA" else st.selectbox("Medio Físico", OPCIONES_SOPORTE_TARJETA)

        with col2:
            almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index("L010"))
            almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index("P140"))
            es_interno = (almacen_origen != "L010")
            tipo_etiqueta_sap = "KI" if es_interno else "KE"
            puesto_origen = st.selectbox("Puesto Origen", ["-- Opcional --"] + ALMACENES_PUESTOS.get(almacen_origen, [])) if es_interno else None
            puesto_destino = st.selectbox("Puesto Destino", ["-- Seleccionar --"] + ALMACENES_PUESTOS.get(almacen_destino, []))

        with col3:
            cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=float(pkg_sugerido or 0.0), step=1.0)
            
            if tipo_soporte == "GAVETA":
                cant_pp = st.number_input("Cantidad Punto Pedido", value=cant_repo, disabled=True)
            else:
                cant_pp = st.number_input("Cantidad Punto Pedido", min_value=0.0, step=1.0)

            unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
            dias_prep = st.number_input("Tiempo Preparación / Días", min_value=0, value=1)

        if st.button("💾 Guardar y Crear Kanban", type="primary"):
            df_curr = obtener_base_kanbans(forzar=True)
            
            if not material or puesto_destino in ["-- Seleccionar --", ""]:
                st.error("❌ Error: Código de Material y Puesto Destino son campos obligatorios.")
            elif tipo_soporte == "TARJETA" and float(cant_pp) >= float(cant_repo):
                st.error(f"🚫 ACCIÓN BLOQUEADA: En Kanbans tipo TARJETA, el Punto de Pedido ({cant_pp}) DEBE SER ESTRICTAMENTE MENOR a la Cantidad de Reposición ({cant_repo}).")
            elif not df_curr.empty and len(
                df_curr[
                    (df_curr['Material'].astype(str).str.strip().str.upper() == material) & 
                    (df_curr['Puesto de trabajo destino'].astype(str).str.strip().str.upper() == puesto_destino.upper())
                ]
            ) > 0:
                kb_existente = df_curr[
                    (df_curr['Material'].astype(str).str.strip().str.upper() == material) & 
                    (df_curr['Puesto de trabajo destino'].astype(str).str.strip().str.upper() == puesto_destino.upper())
                ].iloc[0]['N° Etiquetas']
                
                st.error(f"🚫 REGISTRO DUPLICADO PROHIBIDO: Ya existe un Kanban activo (**{kb_existente}**) para el Material **{material}** en el Puesto **{puesto_destino}**.")
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
                    'Puesto trabajo Origen': str(puesto_origen) if puesto_origen else "-", 
                    'Puesto de trabajo destino': str(puesto_destino),
                    'Cantidad Reposicion': str(cant_repo), 
                    'Unidad Reposicion': str(unidad),
                    'Cantidad Punto de Pedido': str(cant_pp), 
                    'Tiempo preparación abast. (en días)': str(dias_prep),
                    'Fecha Modificación': str(fecha_actual), 
                    'Usuario Modificación': str(usr_act)
                }
                
                df_actualizado = pd.concat([df_curr, pd.DataFrame([nuevo_reg])], ignore_index=True)
                actualizar_base_kanbans(df_actualizado)
                
                detalle = f"Alta de Kanban ({tipo_soporte} - {medio_str} | Rep: {cant_repo} | PP: {cant_pp})"
                registrar_log("CREO", codigo_k_nuevo, material, medio_str, almacen_destino, puesto_destino, detalle, usr_act)
                crear_solicitud_tracker(material, codigo_k_nuevo, tipo_etiqueta_sap, puesto_destino, medio_str, detalle, "ARMAR PEDIDO", usr_act)
                st.success(f"✅ ¡Kanban **{codigo_k_nuevo}** asignado y creado exitosamente en tiempo real!")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# VISTA: MODIFICAR Y ELIMINAR (CON DETECCIÓN DE CAMBIOS)
# ==========================================
tab_mod = obtener_tab("✏️ Modificar y Eliminar")
if tab_mod:
    with tab_mod:
        st.subheader("✏️ Modificar y Eliminar Kanban")
        df_live = obtener_base_kanbans(forzar=True)
        
        if 'msg_exito_mod' in st.session_state:
            st.success(st.session_state.pop('msg_exito_mod'))
        if 'msg_exito_del' in st.session_state:
            st.success(st.session_state.pop('msg_exito_del'))

        m_col_left, m_col_right = st.columns([2.2, 1])
        
        with m_col_left:
            busqueda = st.text_input("Ingrese Código de Material o Código K a buscar:", key="search_mod").upper().strip()
            
            if busqueda:
                kanbans_encontrados = df_live[
                    (df_live['Material'].astype(str).str.strip().str.upper() == busqueda) |
                    (df_live['Material'].astype(str).str.contains(busqueda, na=False, regex=False)) |
                    (df_live['N° Etiquetas'].astype(str).str.strip().str.upper() == busqueda)
                ]
                
                if not kanbans_encontrados.empty:
                    opciones_k = [
                        f"{r['N° Etiquetas']} | Puesto: {r['Puesto de trabajo destino']}" 
                        for _, r in kanbans_encontrados.iterrows()
                    ]
                    
                    sel_k_fmt = st.selectbox("Seleccione el Código K a modificar:", opciones_k, key="m_select_k_combo")
                    k_sel = sel_k_fmt.split(" | ")[0].strip()
                    
                    row = kanbans_encontrados[kanbans_encontrados['N° Etiquetas'] == k_sel].iloc[0]
                    
                    st.caption(f"📌 Editando **{k_sel}** — Material: **{row['Material']}**")
                    
                    # --- PRECARGA DE DATOS EXISTENTES ---
                    val_centro = str(row['Centro']) if pd.notna(row['Centro']) else "A110"
                    tipo_k_curr = str(row['Tipo Kanban']).upper() if pd.notna(row['Tipo Kanban']) else "TARJETA"
                    idx_tipo_k = 0 if "GAVETA" in tipo_k_curr else 1
                    
                    medio_curr = str(row['Medio']).strip() if pd.notna(row['Medio']) and str(row['Medio']).strip() not in ["nan", "None", ""] else "SIN MEDIO DEFINIDO"
                    
                    alm_o_curr = str(row['Almacén Origen']) if pd.notna(row['Almacén Origen']) and str(row['Almacén Origen']) in LISTA_ALMACENES else "L010"
                    alm_d_curr = str(row['Almacen Destino']) if pd.notna(row['Almacen Destino']) and str(row['Almacen Destino']) in LISTA_ALMACENES else "P140"
                    puesto_d_curr = str(row['Puesto de trabajo destino']) if pd.notna(row['Puesto de trabajo destino']) else ""
                    
                    try: val_repo = float(row['Cantidad Reposicion'])
                    except (ValueError, TypeError): val_repo = 0.0
                    
                    try: val_pp = float(row['Cantidad Punto de Pedido'])
                    except (ValueError, TypeError): val_pp = 0.0
                    
                    unidades_validas = ["UN", "M", "L", "KG"]
                    un_curr = str(row['Unidad Reposicion']).upper() if pd.notna(row['Unidad Reposicion']) and str(row['Unidad Reposicion']).upper() in unidades_validas else "UN"
                    idx_un = unidades_validas.index(un_curr)
                    
                    try: val_dias = int(float(row['Tiempo preparación abast. (en días)']))
                    except (ValueError, TypeError): val_dias = 1

                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        m_centro = st.text_input("Centro", value=val_centro, key=f"m_c_{k_sel}")
                        m_tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"], index=idx_tipo_k, key=f"m_ts_{k_sel}")
                        
                        # --- SELECCIÓN DINÁMICA DEL MEDIO ---
                        if m_tipo_soporte == "GAVETA":
                            tam_gav_curr = medio_curr.replace("GAVETA", "").strip()
                            idx_gav = OPCIONES_GAVETA.index(tam_gav_curr) if tam_gav_curr in OPCIONES_GAVETA else 1
                            m_medio_str = f"GAVETA {st.selectbox('Tamaño Gaveta', OPCIONES_GAVETA, index=idx_gav, key=f'm_gav_{k_sel}')}"
                        else:
                            idx_med = OPCIONES_SOPORTE_TARJETA.index(medio_curr) if medio_curr in OPCIONES_SOPORTE_TARJETA else 0
                            m_medio_str = st.selectbox("Medio Físico", OPCIONES_SOPORTE_TARJETA, index=idx_med, key=f"m_med_{k_sel}")

                    with m_col2:
                        m_almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index(alm_o_curr), key=f"m_ao_{k_sel}")
                        m_almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index(alm_d_curr), key=f"m_ad_{k_sel}")
                        m_puesto_destino = st.text_input("Puesto Destino", value=puesto_d_curr, key=f"m_pd_{k_sel}").upper().strip()

                    with m_col3:
                        m_cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=val_repo, step=1.0, key=f"m_cr_{k_sel}")
                        
                        # --- HABILITACIÓN DINÁMICA DEL PUNTO DE PEDIDO ---
                        if m_tipo_soporte == "GAVETA":
                            m_cant_pp = st.number_input("Cantidad Punto Pedido", value=m_cant_repo, disabled=True, key=f"m_pp_g_{k_sel}")
                        else:
                            m_cant_pp = st.number_input("Cantidad Punto Pedido", min_value=0.0, value=val_pp, disabled=False, step=1.0, key=f"m_pp_t_{k_sel}")
                            
                        m_unidad = st.selectbox("Unidad Base", unidades_validas, index=idx_un, key=f"m_un_{k_sel}")
                        m_dias_prep = st.number_input("Tiempo Preparación / Días", min_value=0, value=val_dias, key=f"m_dias_{k_sel}")

                    if st.button("💾 Guardar Cambios de Kanban", type="primary", key=f"btn_save_{k_sel}"):
                        if not m_puesto_destino:
                            st.error("❌ Error: El Puesto Destino no puede estar vacío.")
                        elif m_tipo_soporte == "TARJETA" and float(m_cant_pp) >= float(m_cant_repo):
                            st.error(f"🚫 ACCIÓN BLOQUEADA: En Kanbans tipo TARJETA, el Punto de Pedido ({m_cant_pp}) DEBE SER ESTRICTAMENTE MENOR a la Cantidad de Reposición ({m_cant_repo}). No se aplicaron cambios.")
                        else:
                            # --- DETECCIÓN DE CAMBIOS (DIFF) ---
                            cambios_detectados = []
                            if str(m_centro) != str(val_centro): cambios_detectados.append(f"Centro: {val_centro} ➔ {m_centro}")
                            if str(m_tipo_soporte) != str(tipo_k_curr): cambios_detectados.append(f"Tipo: {tipo_k_curr} ➔ {m_tipo_soporte}")
                            if str(m_medio_str) != str(medio_curr): cambios_detectados.append(f"Medio: {medio_curr} ➔ {m_medio_str}")
                            if str(m_almacen_origen) != str(alm_o_curr): cambios_detectados.append(f"Alm. Orig: {alm_o_curr} ➔ {m_almacen_origen}")
                            if str(m_almacen_destino) != str(alm_d_curr): cambios_detectados.append(f"Alm. Dest: {alm_d_curr} ➔ {m_almacen_destino}")
                            if str(m_puesto_destino) != str(puesto_d_curr): cambios_detectados.append(f"Puesto Dest: {puesto_d_curr} ➔ {m_puesto_destino}")
                            if float(m_cant_repo) != float(val_repo): cambios_detectados.append(f"Cant. Repo: {val_repo} ➔ {m_cant_repo}")
                            if float(m_cant_pp) != float(val_pp): cambios_detectados.append(f"Cant. PP: {val_pp} ➔ {m_cant_pp}")
                            if str(m_unidad) != str(un_curr): cambios_detectados.append(f"Unidad: {un_curr} ➔ {m_unidad}")
                            if int(m_dias_prep) != int(val_dias): cambios_detectados.append(f"Días Prep: {val_dias} ➔ {m_dias_prep}")

                            if not cambios_detectados:
                                st.info("ℹ️ No se detectaron modificaciones respecto a los datos actuales.")
                            else:
                                detalle_cambios_str = " | ".join(cambios_detectados)
                                usr_act = st.session_state['usuario_email']
                                idx = df_live[df_live['N° Etiquetas'] == k_sel].index[0]
                                
                                df_live.loc[idx, 'Centro'] = str(m_centro)
                                df_live.loc[idx, 'Tipo Kanban'] = str(m_tipo_soporte)
                                df_live.loc[idx, 'Medio'] = str(m_medio_str)
                                df_live.loc[idx, 'Almacén Origen'] = str(m_almacen_origen)
                                df_live.loc[idx, 'Almacen Destino'] = str(m_almacen_destino)
                                df_live.loc[idx, 'Puesto de trabajo destino'] = str(m_puesto_destino)
                                df_live.loc[idx, 'Cantidad Reposicion'] = str(m_cant_repo)
                                df_live.loc[idx, 'Cantidad Punto de Pedido'] = str(m_cant_pp)
                                df_live.loc[idx, 'Unidad Reposicion'] = str(m_unidad)
                                df_live.loc[idx, 'Tiempo preparación abast. (en días)'] = str(m_dias_prep)
                                df_live.loc[idx, 'Fecha Modificación'] = str(obtener_fecha_hora_arg())
                                df_live.loc[idx, 'Usuario Modificación'] = str(usr_act)
                                
                                mat_mod = str(df_live.loc[idx, 'Material'])
                                actualizar_base_kanbans(df_live)
                                
                                registrar_log("ACTUALIZO", k_sel, mat_mod, m_medio_str, m_almacen_destino, m_puesto_destino, detalle_cambios_str, usr_act)
                                crear_solicitud_tracker(mat_mod, k_sel, df_live.loc[idx, 'Tipo Etiqueta'], m_puesto_destino, m_medio_str, detalle_cambios_str, "IMPRIMIR / REEMPLAZAR", usr_act)
                                
                                st.session_state['msg_exito_mod'] = f"✅ ¡Kanban **{k_sel}** modificado con éxito! Cambios registrados: {detalle_cambios_str}"
                                st.rerun()
                else:
                    st.warning(f"⚠️ No se encontraron Kanbans registrados para la búsqueda: **{busqueda}**")

        with m_col_right:
            st.markdown("#### 🗑️ Dar de Baja Kanban")
            opciones_del_k = [
                f"{r['N° Etiquetas']} | Mat: {r['Material']} | Puesto: {r['Puesto de trabajo destino']}"
                for _, r in df_live.iterrows()
            ]
            
            k_del_fmt = st.selectbox("Seleccionar Código K a eliminar:", ["-- Seleccionar --"] + opciones_del_k, key="k_del_select")
            
            if st.button("🗑️ Eliminar y Solicitar Retiro", use_container_width=True) and k_del_fmt != "-- Seleccionar --":
                k_del_sel = k_del_fmt.split(" | ")[0].strip()
                row_del = df_live[df_live['N° Etiquetas'] == k_del_sel].iloc[0]
                mat_del = str(row_del['Material'])
                puesto_del = str(row_del['Puesto de trabajo destino'])
                medio_del = str(row_del['Medio'] or "SIN MEDIO DEFINIDO")
                tipo_del = str(row_del['Tipo Etiqueta'])
                usr_act = st.session_state['usuario_email']
                
                df_nuevo_global = df_live[df_live['N° Etiquetas'] != k_del_sel]
                actualizar_base_kanbans(df_nuevo_global)
                
                detalle_baja = f"Baja de Kanban (Puesto: {puesto_del} | Medio: {medio_del})"
                registrar_log("ELIMINO", k_del_sel, mat_del, medio_del, str(row_del['Almacen Destino']), puesto_del, detalle_baja, usr_act)
                crear_solicitud_tracker(mat_del, k_del_sel, tipo_del, puesto_del, medio_del, detalle_baja, "RETIRAR KB", usr_act)
                
                st.session_state['msg_exito_del'] = f"♻️️ Kanban **{k_del_sel}** eliminado correctamente. El código quedó liberado para ser reciclado."
                st.rerun()

# ==========================================
# VISTA UNIFICADA: CONSULTA Y EXPORTAR TABLA Z (SAP)
# ==========================================
tab_export = obtener_tab("📊 Consulta y Exportar Tabla Z (SAP)")
if tab_export:
    with tab_export:
        st.subheader("📊 Consulta y Exportación de Tabla Z (SAP)")
        df_export_live = obtener_base_kanbans(forzar=True)
        
        with st.expander("🔍 Filtros de Búsqueda de Tabla Z", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                q_txt = st.text_input("Buscar por Material o Código K:", placeholder="Ej. PB005075 o K00000001", key="tz_search").upper().strip()
            with f_col2:
                q_alm = st.selectbox("Filtrar por Almacén Destino:", ["Todos"] + list(df_export_live['Almacen Destino'].dropna().unique()), key="tz_alm")
            with f_col3:
                q_tipo = st.selectbox("Filtrar por Tipo Kanban:", ["Todos", "GAVETA", "TARJETA"], key="tz_tipo")

        df_tz_filtered = df_export_live.copy()
        if q_txt:
            df_tz_filtered = df_tz_filtered[
                (df_tz_filtered['Material'].astype(str).str.contains(q_txt, na=False)) |
                (df_tz_filtered['N° Etiquetas'].astype(str).str.contains(q_txt, na=False))
            ]
        if q_alm != "Todos":
            df_tz_filtered = df_tz_filtered[df_tz_filtered['Almacen Destino'] == q_alm]
        if q_tipo != "Todos":
            df_tz_filtered = df_tz_filtered[df_tz_filtered['Tipo Kanban'] == q_tipo]

        st.caption(f"⚡ Mostrando **{len(df_tz_filtered)}** registros de un total de **{len(df_export_live)}** activos.")
        st.dataframe(df_tz_filtered, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export_live.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        excel_bytes = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Tabla Z Completa (.xlsx)", 
            data=excel_bytes, 
            file_name="TablaZ_Kanbans_Actualizada.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            type="primary"
        )

# ==========================================
# HISTORIAL Y PERFIL
# ==========================================
tab_historial = obtener_tab("📜 Historial Auditoría")
if tab_historial:
    with tab_historial:
        st.subheader("📜 Historial Completo de Modificaciones")
        st.dataframe(cargar_logs().sort_values(by="Fecha_Hora", ascending=False), use_container_width=True)
        
        if rol_actual == "Procesos":
            st.markdown("---")
            with st.expander("⚠️ Zona de Mantenimiento / Puesta a Cero (Producción)"):
                st.warning("Esta acción eliminará todos los registros de prueba de Auditoría y Tracker Logístico para el arranque oficial.")
                if st.button("🔴 Borrar Historiales de Prueba", type="primary"):
                    limpiar_historiales_de_prueba()
                    st.success("✅ Historiales y Tracker limpiados correctamente. ¡El sistema está listo para el arranque!")
                    st.rerun()

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
                    st.info("Aún no has registrado movimientos (creaciones, modificaciones o bajas) en el sistema.")
            else:
                st.info("No existen registros en el historial.")
