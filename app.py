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

LOG_COLUMNS = ["Fecha_Hora", "Acción", "Código_K", "Material", "Medio", "Almacén_Destino", "Puesto_Destino", "Usuario"]
TRACKER_COLUMNS = ["ID_Solicitud", "Fecha_Solicitud", "Material", "Código_K", "Tipo_KB", "Puesto_Destino", "Medio", "Cambio", "Acción_Requerida", "Cargado_SAP", "Impreso", "Fecha_Impresion", "Estado_Fisico", "Fecha_Finalizacion", "Observación", "Usuario_Procesos"]

ROLES_PREDEFINIDOS = {
    "jairc@crucianelli.com": "Procesos", "mmagarello@crucianelli.com": "Procesos",
    "mcabral@crucianelli.com": "Procesos", "gtuninetti@crucianelli.com": "Procesos",
    "produccion@crucianelli.com": "Procesos", "abacelli@crucianelli.com": "Procesos",
    "tabrate@crucianelli.com": "Procesos", "llatanzi@crucianelli.com": "Procesos",
    
    "mlopez@crucianelli.com": "Logistica", "recepcion3@crucianelli.com": "Logistica",
    "gpereyra@crucianelli.com": "Logistica", "jporta@crucianelli.com": "Logistica",
    "spetetta@crucianelli.com": "Logistica",
    
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

MAPEO_PUESTOS = {
    "ARM HORQ": "ARM_HORQ", "SOLDROB08": "SOLROB08", "PREBAL01": "PRENBAL1",
    "ALMACÉN": "PRINCIPAL", "LOGISTICA": "PRINCIPAL", "L010": "PRINCIPAL"
}

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

if not st.session_state['usuario_email']:
    st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")
    col_auth, _ = st.columns([1.5, 2])
    with col_auth:
        tab_login, tab_register = st.tabs(["🔐 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_login:
            email_input = st.text_input("Correo electrónico (@crucianelli.com):", key="log_email").strip().lower()
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
    st.stop()

# ==========================================
# MANEJO DE BASE DE DATOS EN TIEMPO REAL
# ==========================================
def cargar_datos_disco():
    if os.path.exists(DB_FILE):
        df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        
        # Normalizar a string
        df['Material'] = df['Material'].astype(str).str.strip().str.upper()
        df['N° Etiquetas'] = df['N° Etiquetas'].astype(str).str.strip().str.upper()

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
        return df[COLUMNS]
    return pd.DataFrame(columns=COLUMNS)

# Inicializar o recuperar dataframe vivo en sesión
if 'df_kanbans_session' not in st.session_state:
    st.session_state['df_kanbans_session'] = cargar_datos_disco()

def obtener_df_kanbans():
    return st.session_state['df_kanbans_session']

def guardar_datos_session(df):
    st.session_state['df_kanbans_session'] = df
    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

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

def registrar_log(accion, codigo_k, material, medio, alm_dest, puesto_dest, usuario):
    now = obtener_fecha_hora_arg()
    df_actual = cargar_logs()
    if pd.isna(medio) or str(medio).strip() in ["None", "nan", "N/A", ""]:
        medio = "SIN MEDIO DEFINIDO"
    
    mapeo_guardado = {'CREO': 'CREACIÓN', 'ACTUALIZO': 'MODIFICACIÓN', 'ELIMINO': 'ELIMINACIÓN'}
    accion_norm = mapeo_guardado.get(accion, accion)

    nuevo_log = pd.DataFrame([{
        "Fecha_Hora": now, "Acción": accion_norm, "Código_K": codigo_k,
        "Material": material, "Medio": str(medio), "Almacén_Destino": alm_dest,
        "Puesto_Destino": puesto_dest, "Usuario": usuario
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

def obtener_siguiente_codigo_k(df):
    if df.empty or df['N° Etiquetas'].dropna().empty:
        return "K00000001"
    numeros = [int(m.group(0)) for val in df['N° Etiquetas'].dropna() if (m := re.search(r'\d+', str(val)))]
    if not numeros:
        return "K00000001"
    set_numeros = set(numeros)
    max_num = max(numeros)
    for i in range(1, max_num + 1):
        if i not in set_numeros:
            return f"K{i:08d}"
    return f"K{max_num + 1:08d}"

df_kanbans = obtener_df_kanbans()
dict_pkg = cargar_packaging()
rol_actual = st.session_state.get('usuario_rol', 'Consulta')

# ==========================================
# CABECERA Y ROL
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

col_head_space, col_logout = st.columns([5, 1])
with col_logout:
    if st.button("Cerrar Sesión", use_container_width=True):
        st.session_state['usuario_email'] = None
        st.session_state['usuario_rol'] = None
        st.session_state.pop('df_kanbans_session', None)
        st.rerun()

total_k = len(df_kanbans)
internos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KI'])
externos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KE'])
proximo_k_val = obtener_siguiente_codigo_k(df_kanbans)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Kanbans", total_k)
kpi2.metric("Internos (KI)", internos_k)
kpi3.metric("Externos (KE)", externos_k)
kpi4.metric("Próximo Código K", proximo_k_val)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# MENÚ POR PERFILES (ROLES)
# ==========================================
if rol_actual == "Procesos":
    lista_tabs = ["📈 Panel KPIs & Métricas", "🚚 Tracker de Ejecución Logística", "➕ Crear Nuevo Kanban", "✏️ Modificar y Eliminar", "📊 Exportar Datos", "📜 Historial Auditoría"]
elif rol_actual == "Logistica":
    lista_tabs = ["🚚 Tracker de Ejecución Logística", "📈 Panel KPIs & Métricas", "📋 Consulta General", "📊 Exportar Datos para SAP", "📜 Historial Auditoría"]
else: # Consulta / Planta
    lista_tabs = ["📈 Panel KPIs & Métricas", "📋 Consulta General", "🚚 Estado de Solicitudes"]

tabs = st.tabs(lista_tabs)

def obtener_tab(nombre):
    if nombre in lista_tabs:
        return tabs[lista_tabs.index(nombre)]
    return None

# ==========================================
# VISTA: PANEL KPIS
# ==========================================
tab_kpis = obtener_tab("📈 Panel KPIs & Métricas")
if tab_kpis:
    with tab_kpis:
        st.subheader("📊 Panel Interactivo de KPIs y Analítica")
        df_logs_kpi = cargar_logs()
        df_k_live = obtener_df_kanbans()
        
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

        df_logs_filtrado = df_logs_kpi.copy() if not df_logs_kpi.empty else pd.DataFrame()
        if not df_logs_filtrado.empty and isinstance(rango_fechas_kpi, tuple) and len(rango_fechas_kpi) == 2:
            fi, ff = rango_fechas_kpi
            df_logs_filtrado = df_logs_filtrado[(df_logs_filtrado['Fecha_dt'].dt.date >= fi) & (df_logs_filtrado['Fecha_dt'].dt.date <= ff)]
            if f_alm != "Todos": df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Almacén_Destino'] == f_alm]
            if f_usr != "Todos": df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Usuario'] == f_usr]

        c_creados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'CREACIÓN']) if not df_logs_filtrado.empty else 0
        c_actualizados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'MODIFICACIÓN']) if not df_logs_filtrado.empty else 0
        c_eliminados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'ELIMINACIÓN']) if not df_logs_filtrado.empty else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Movimientos Período", len(df_logs_filtrado))
        m2.metric("✨ Creados", c_creados)
        m3.metric("✏️ Modificados", c_actualizados)
        m4.metric("🗑️ Eliminados", c_eliminados)
        st.markdown("---")

        g_col1, g_col2 = st.columns(2)
        with g_col1:
            st.markdown("##### 🏭 Top Puestos de Trabajo Destino")
            df_puestos = df_k_live['Puesto de trabajo destino'].value_counts().reset_index()
            df_puestos.columns = ['Puesto Destino', 'Cantidad']
            fig_puestos = px.bar(df_puestos.head(10), x='Cantidad', y='Puesto Destino', orientation='h', text='Cantidad', template="plotly_dark", color='Cantidad', color_continuous_scale='Reds')
            fig_puestos.update_layout(yaxis={'categoryorder': 'total ascending'}, height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_puestos, use_container_width=True)

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
# VISTA: CREAR KANBAN (SOLO PROCESOS)
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
            cant_pp = st.number_input("Cantidad Punto Pedido", value=cant_repo, disabled=True) if tipo_soporte == "GAVETA" else st.number_input("Cantidad Punto Pedido", min_value=0.0, step=1.0)
            unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
            dias_prep = st.number_input("Tiempo Preparación / Días", min_value=0, value=1)

        if st.button("💾 Guardar y Crear Kanban", type="primary"):
            if not material or puesto_destino in ["-- Seleccionar --", ""]:
                st.error("❌ Material y Puesto Destino obligatorios.")
            else:
                fecha_actual = obtener_fecha_hora_arg()
                usr_act = st.session_state['usuario_email']
                df_curr = obtener_df_kanbans()
                
                nuevo_reg = {
                    'N° Etiquetas': proximo_k_val, 'Tipo Etiqueta': tipo_etiqueta_sap,
                    'Tipo Kanban': tipo_soporte, 'Medio': medio_str, 'Material': material,
                    'Centro': centro, 'Almacén Origen': almacen_origen, 'Almacen Destino': almacen_destino,
                    'Puesto trabajo Origen': puesto_origen, 'Puesto de trabajo destino': puesto_destino,
                    'Cantidad Reposicion': cant_repo, 'Unidad Reposicion': unidad,
                    'Cantidad Punto de Pedido': cant_pp, 'Tiempo preparación abast. (en días)': dias_prep,
                    'Fecha Modificación': fecha_actual, 'Usuario Modificación': usr_act
                }
                
                # Sincronización inmediata en session state y disco
                df_updated = pd.concat([df_curr, pd.DataFrame([nuevo_reg])], ignore_index=True)
                guardar_datos_session(df_updated)
                
                registrar_log("CREO", proximo_k_val, material, medio_str, almacen_destino, puesto_destino, usr_act)
                crear_solicitud_tracker(material, proximo_k_val, tipo_etiqueta_sap, puesto_destino, medio_str, "CÓDIGO NUEVO", "ARMAR PEDIDO", usr_act)
                st.success(f"✅ ¡Kanban **{proximo_k_val}** creado! Enviado a Logística con acción: **ARMAR PEDIDO**.")
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# VISTA: MODIFICAR Y ELIMINAR (SOLO PROCESOS)
# ==========================================
tab_mod = obtener_tab("✏️ Modificar y Eliminar")
if tab_mod:
    with tab_mod:
        st.subheader("✏️ Modificar y Eliminar Kanban")
        df_live = obtener_df_kanbans()
        
        m_col_left, m_col_right = st.columns([2, 1])
        
        # --- BÚSQUEDA EN TIEMPO REAL ---
        with m_col_left:
            busqueda = st.text_input("Ingrese Código de Material a Buscar (ej: CM000044):", key="search_mod").upper().strip()
            
            if busqueda:
                # Filtrar sobre la base en memoria viva
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
                    
                    sel_k_fmt = st.selectbox("Seleccione el Código K a modificar:", opciones_k)
                    k_sel = sel_k_fmt.split(" | ")[0].strip()
                    
                    row = kanbans_encontrados[kanbans_encontrados['N° Etiquetas'] == k_sel].iloc[0]
                    
                    st.caption(f"📌 Editando **{k_sel}** - Material: **{row['Material']}**")
                    
                    m_col1, m_col2, m_col3 = st.columns(3)
                    with m_col1:
                        m_centro = st.text_input("Centro", value=str(row['Centro'] or "A110"), key="m_centro")
                        m_tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"], index=0 if "GAVETA" in str(row['Tipo Kanban']).upper() else 1, key="m_soporte")
                        m_medio_str = f"GAVETA {st.selectbox('Tamaño Gaveta', OPCIONES_GAVETA, key='m_gav')}" if m_tipo_soporte == "GAVETA" else st.selectbox("Medio Físico", OPCIONES_SOPORTE_TARJETA, key="m_tarj")

                    with m_col2:
                        m_almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index(row['Almacén Origen'] if row['Almacén Origen'] in LISTA_ALMACENES else "L010"), key="m_alm_o")
                        m_almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index(row['Almacen Destino'] if row['Almacen Destino'] in LISTA_ALMACENES else "P140"), key="m_alm_d")
                        m_puesto_destino = st.text_input("Puesto Destino", value=str(row['Puesto de trabajo destino'] or ''), key="m_p_dest").upper().strip()

                    with m_col3:
                        m_cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=float(row['Cantidad Reposicion'] or 0.0), key="m_cant_r")
                        m_cant_pp = st.number_input("Cantidad Punto Pedido", value=m_cant_repo, disabled=True, key="m_cant_p_g") if m_tipo_soporte == "GAVETA" else st.number_input("Cantidad Punto Pedido", min_value=0.0, value=float(row['Cantidad Punto de Pedido'] or 0.0), key="m_cant_p_t")

                    if st.button("💾 Guardar Cambios", type="primary"):
                        usr_act = st.session_state['usuario_email']
                        idx = df_live[df_live['N° Etiquetas'] == k_sel].index[0]
                        
                        df_live.loc[idx, 'Tipo Kanban'] = m_tipo_soporte
                        df_live.loc[idx, 'Medio'] = m_medio_str
                        df_live.loc[idx, 'Puesto de trabajo destino'] = m_puesto_destino
                        df_live.loc[idx, 'Cantidad Reposicion'] = m_cant_repo
                        df_live.loc[idx, 'Cantidad Punto de Pedido'] = m_cant_pp
                        df_live.loc[idx, 'Fecha Modificación'] = obtener_fecha_hora_arg()
                        df_live.loc[idx, 'Usuario Modificación'] = usr_act
                        
                        mat_mod = str(df_live.loc[idx, 'Material'])
                        guardar_datos_session(df_live)
                        
                        registrar_log("ACTUALIZO", k_sel, mat_mod, m_medio_str, m_almacen_destino, m_puesto_destino, usr_act)
                        crear_solicitud_tracker(mat_mod, k_sel, df_live.loc[idx, 'Tipo Etiqueta'], m_puesto_destino, m_medio_str, "ACTUALIZACIÓN", "IMPRIMIR / REEMPLAZAR", usr_act)
                        st.success(f"✅ Kanban **{k_sel}** actualizado! Acción enviada a Logística: **IMPRIMIR / REEMPLAZAR**.")
                        st.rerun()
                else:
                    st.warning(f"⚠️ No se encontraron Kanbans registrados para el material o código: **{busqueda}**")

        # --- SECCIÓN ELIMINACIÓN ---
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
                
                df_updated = df_live[df_live['N° Etiquetas'] != k_del_sel]
                guardar_datos_session(df_updated)
                
                registrar_log("ELIMINO", k_del_sel, mat_del, medio_del, str(row_del['Almacen Destino']), puesto_del, usr_act)
                crear_solicitud_tracker(mat_del, k_del_sel, tipo_del, puesto_del, medio_del, "BAJA / ELIMINACIÓN", "RETIRAR KB", usr_act)
                st.success(f"♻️ Kanban **{k_del_sel}** dado de baja. Solicitud enviada a Logística: **RETIRAR KB**.")
                st.rerun()

# ==========================================
# VISTAS GENERALES: CONSULTA / EXPORTAR / LOGS
# ==========================================
tab_consulta = obtener_tab("📋 Consulta General")
if tab_consulta:
    with tab_consulta:
        st.subheader("📋 Consulta General de Kanbans")
        st.dataframe(obtener_df_kanbans(), use_container_width=True)

tab_export = obtener_tab("📊 Exportar Datos") or obtener_tab("📊 Exportar Datos para SAP")
if tab_export:
    with tab_export:
        st.subheader("📊 Exportar Tabla Z Completa para SAP")
        df_export_live = obtener_df_kanbans()
        st.dataframe(df_export_live, use_container_width=True)
        
        # Generar archivo Excel en memoria instantáneamente
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export_live.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        excel_bytes = output.getvalue()
        
        st.download_button(
            label="📥 Descargar Tabla Z en Excel (.xlsx)", 
            data=excel_bytes, 
            file_name="TablaZ_Kanbans.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            type="primary"
        )

tab_historial = obtener_tab("📜 Historial Auditoría")
if tab_historial:
    with tab_historial:
        st.subheader("📜 Historial Completo de Modificaciones")
        st.dataframe(cargar_logs().sort_values(by="Fecha_Hora", ascending=False), use_container_width=True)
