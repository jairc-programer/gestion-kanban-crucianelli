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

    .tracker-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def obtener_fecha_hora_arg():
    return datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")

DB_FILE = "TablaZ.xlsx"
LIVE_DB_FILE = "TablaZ_live.csv"
PKG_FILE_EXCEL = "Lotes packaing.xlsx"
PKG_FILE_ALT = "Lote packaging.xlsx"
LOG_FILE = "historial_cambios.csv"
TRACKER_FILE = "tracker_ejecucion.csv"
USERS_FILE = "usuarios.json"
SHEET_NAME = "Kanbans CRUCIANELLI"

LOG_COLUMNS = ["Fecha_Hora", "Acción", "Código_K", "Material", "Medio", "Almacén_Destino", "Puesto_Destino", "Detalle_Cambio", "Usuario"]
TRACKER_COLUMNS = ["ID_Solicitud", "Fecha_Solicitud", "Material", "Código_K", "Tipo_KB", "Puesto_Destino", "Medio", "Cambio", "Acción_Requerida", "Cargado_SAP", "Impreso", "Fecha_Impresion", "Estado_Fisico", "Fecha_Finalizacion", "Observación", "Usuario_Procesos"]

ROLES_PREDEFINIDOS = {
    # PROCESOS
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
OPCIONES_UNIDAD_MEDIDA = ["UN", "M", "KG", "L"]

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
    target_file = None
    if os.path.exists(PKG_FILE_EXCEL):
        target_file = PKG_FILE_EXCEL
    elif os.path.exists(PKG_FILE_ALT):
        target_file = PKG_FILE_ALT

    if target_file:
        try:
            df = pd.read_excel(target_file)
            df.columns = [str(c).strip() for c in df.columns]
            
            # Identificar columna de material
            col_mat = next((c for c in df.columns if c.upper() in ['MATERIAL', 'CODIGO', 'CÓDIGO', 'MATERIALES']), df.columns[0])
            df[col_mat] = df[col_mat].astype(str).str.strip().str.upper()
            
            dict_pkg = {}
            for _, r in df.iterrows():
                mat = r[col_mat]
                
                # Obtención de Medio
                medio_val = ""
                for c_med in ['Packaging', 'Packaing', 'Medio', 'Soporte', 'Envase']:
                    if c_med in df.columns and pd.notna(r[c_med]):
                        medio_val = str(r[c_med]).strip()
                        break

                # Obtención de Unidad
                unid_val = "UN"
                for c_uni in ['Unidad', 'UM', 'Unidad Reposicion', 'Unidad de Medida']:
                    if c_uni in df.columns and pd.notna(r[c_uni]):
                        unid_val = str(r[c_uni]).strip().upper()
                        break

                # Obtención de Lote
                cant_val = None
                for c_cant in ['Lote Packaging', 'Lote packaging', 'Lote Packaging ', 'Lote', 'Cantidad', 'Cantidad Reposicion', 'Cant', 'Lote de Reposicion', 'Tamaño Lote']:
                    if c_cant in df.columns and pd.notna(r[c_cant]):
                        try:
                            val_num = float(r[c_cant])
                            if not pd.isna(val_num):
                                cant_val = val_num
                                break
                        except (ValueError, TypeError):
                            pass

                dict_pkg[mat] = {
                    "medio": medio_val, 
                    "unidad": unid_val if unid_val not in ['NAN', 'NONE', ''] else 'UN',
                    "cantidad": cant_val
                }
            return dict_pkg
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
    if not numeros:
        return "K00000001"
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
                if not df_logs_kpi.empty and 'Fecha_Hora' in df_logs_kpi.columns:
                    df_logs_kpi['Fecha_dt'] = pd.to_datetime(df_logs_kpi['Fecha_Hora'], errors='coerce')
                    fechas_validas = df_logs_kpi['Fecha_dt'].dropna()
                    if not fechas_validas.empty:
                        min_d = fechas_validas.min().date()
                        max_d = fechas_validas.max().date()
                    else:
                        min_d = max_d = datetime.now().date()
                else:
                    min_d = max_d = datetime.now().date()
                rango_fechas_kpi = st.date_input("Rango de Fechas (Historial):", value=(min_d, max_d), key="kpi_dates")

            with f_col2:
                almacenes_unicos = ["Todos"]
                if not df_k_live.empty and 'Almacen Destino' in df_k_live.columns:
                    almacenes_unicos += sorted([str(x) for x in df_k_live['Almacen Destino'].dropna().unique() if str(x).strip() != ""])
                f_alm = st.selectbox("Almacén Destino:", almacenes_unicos, key="kpi_alm")

            with f_col3:
                puestos_disp = ["Todos"]
                if not df_k_live.empty and 'Puesto de trabajo destino' in df_k_live.columns:
                    if f_alm != "Todos":
                        puestos_disp += sorted([str(x) for x in df_k_live[df_k_live['Almacen Destino'] == f_alm]['Puesto de trabajo destino'].dropna().unique() if str(x).strip() != ""])
                    else:
                        puestos_disp += sorted([str(x) for x in df_k_live['Puesto de trabajo destino'].dropna().unique() if str(x).strip() != ""])
                f_puesto = st.selectbox("Puesto de Trabajo Destino:", puestos_disp, key="kpi_puesto")

        # --- FILTRADO DE DATOS VIVOS (BASE KANBANS) ---
        df_k_filtrado = df_k_live.copy() if not df_k_live.empty else pd.DataFrame()
        if not df_k_filtrado.empty:
            if f_alm != "Todos":
                df_k_filtrado = df_k_filtrado[df_k_filtrado['Almacen Destino'] == f_alm]
            if f_puesto != "Todos":
                df_k_filtrado = df_k_filtrado[df_k_filtrado['Puesto de trabajo destino'] == f_puesto]

        # --- FILTRADO DE LOGS DE AUDITORÍA ---
        df_logs_filtrado = df_logs_kpi.copy() if not df_logs_kpi.empty else pd.DataFrame()
        if not df_logs_filtrado.empty and isinstance(rango_fechas_kpi, tuple) and len(rango_fechas_kpi) == 2:
            fi, ff = rango_fechas_kpi
            if 'Fecha_dt' in df_logs_filtrado.columns:
                df_logs_filtrado = df_logs_filtrado[(df_logs_filtrado['Fecha_dt'].dt.date >= fi) & (df_logs_filtrado['Fecha_dt'].dt.date <= ff)]
            if f_alm != "Todos" and 'Almacén_Destino' in df_logs_filtrado.columns: 
                df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Almacén_Destino'] == f_alm]
            if f_puesto != "Todos" and 'Puesto_Destino' in df_logs_filtrado.columns: 
                df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Puesto_Destino'] == f_puesto]

        # --- FILTRADO DEL TRACKER LOGÍSTICO ---
        df_tr_filtrado = df_tr_kpi.copy() if not df_tr_kpi.empty else pd.DataFrame()
        if not df_tr_filtrado.empty and f_puesto != "Todos" and 'Puesto_Destino' in df_tr_filtrado.columns:
            df_tr_filtrado = df_tr_filtrado[df_tr_filtrado['Puesto_Destino'] == f_puesto]

        if not df_tr_filtrado.empty:
            pend_sap = len(df_tr_filtrado[df_tr_filtrado['Cargado_SAP'] != 'SI'])
            pend_fisico = len(df_tr_filtrado[df_tr_filtrado['Estado_Fisico'] != 'Entregado'])
        else:
            pend_sap = 0
            pend_fisico = 0

        c_creados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'CREACIÓN']) if not df_logs_filtrado.empty else 0
        c_actualizados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'MODIFICACIÓN']) if not df_logs_filtrado.empty else 0
        c_eliminados = len(df_logs_filtrado[df_logs_filtrado['Acción'] == 'ELIMINACIÓN']) if not df_logs_filtrado.empty else 0

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("KB Activos", len(df_k_filtrado))
        m2.metric("✨ Creados", c_creados)
        m3.metric("✏ Modificados", c_actualizados)
        m4.metric("🗑️ Eliminados", c_eliminados)
        m5.metric("⏳ Pendiente SAP", pend_sap, delta=f"{pend_sap} pendientes", delta_color="inverse")
        m6.metric("🚚 Pend. Físico", pend_fisico, delta=f"{pend_fisico} pendientes", delta_color="inverse")
        st.markdown("---")

        g_col1, g_col2 = st.columns(2)
        
        with g_col1:
            st.markdown("##### 📍 Kanban por Puestos de Trabajo (Puestos y sus Cambios)")
            if not df_k_filtrado.empty and 'Puesto de trabajo destino' in df_k_filtrado.columns:
                col_tipo_op = 'Tipo_Operacion' if 'Tipo_Operacion' in df_k_filtrado.columns else 'Tipo Kanban'
                df_puestos = df_k_filtrado.groupby(['Puesto de trabajo destino', col_tipo_op]).size().reset_index(name='Cantidad')
                orden_puestos = df_k_filtrado['Puesto de trabajo destino'].value_counts().index.tolist()
                
                fig_puestos = px.bar(
                    df_puestos, x='Puesto de trabajo destino', y='Cantidad', color=col_tipo_op,
                    template="plotly_dark",
                    category_orders={'Puesto de trabajo destino': orden_puestos},
                    color_discrete_map={'ACTUALIZACIÓN': '#f97316', 'CÓDIGO NUEVO': '#3b82f6', 'GAVETA': '#ef4444', 'TARJETA': '#3b82f6'}
                )
                fig_puestos.update_layout(
                    height=350, margin=dict(l=20, r=20, t=20, b=80),
                    xaxis_title="", yaxis_title="Record Count",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_puestos, use_container_width=True)
            else:
                st.info("No hay datos de Kanbans para mostrar con los filtros aplicados.")

        with g_col2:
            st.markdown("##### 🏷️ Distribución por Tipo (Gaveta vs Tarjeta)")
            if not df_k_filtrado.empty and 'Tipo Kanban' in df_k_filtrado.columns:
                df_tipos = df_k_filtrado['Tipo Kanban'].value_counts().reset_index()
                df_tipos.columns = ['Tipo', 'Cantidad']
                fig_tipos = px.pie(
                    df_tipos, names='Tipo', values='Cantidad', hole=0.4,
                    template="plotly_dark", color='Tipo',
                    color_discrete_map={'GAVETA': '#ef4444', 'TARJETA': '#3b82f6'}
                )
                fig_tipos.update_traces(textinfo='percent+label+value')
                fig_tipos.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_tipos, use_container_width=True)
            else:
                st.info("No hay datos disponibles para el gráfico de tipos.")

        st.markdown("---")

        g_col3, g_col4 = st.columns(2)

        with g_col3:
            st.markdown("##### 📈 Evolución de Movimientos (Mensual)")
            if not df_logs_filtrado.empty and 'Fecha_dt' in df_logs_filtrado.columns:
                df_logs_valid = df_logs_filtrado.dropna(subset=['Fecha_dt']).copy()
                if not df_logs_valid.empty:
                    df_logs_valid['Mes'] = df_logs_valid['Fecha_dt'].dt.strftime('%b %Y')
                    df_logs_valid['Mes_Sort'] = df_logs_valid['Fecha_dt'].dt.to_period('M')
                    
                    df_evolucion = df_logs_valid.groupby(['Mes_Sort', 'Mes']).size().reset_index(name='Record Count').sort_values('Mes_Sort')
                    
                    fig_evol = px.line(
                        df_evolucion, x='Mes', y='Record Count',
                        markers=True, template="plotly_dark", line_shape="spline"
                    )
                    fig_evol.update_traces(line_color="#38bdf8", fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.1)')
                    fig_evol.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="", yaxis_title="Record Count")
                    st.plotly_chart(fig_evol, use_container_width=True)
                else:
                    st.info("Sin registros de movimientos en el rango seleccionado.")
            else:
                st.info("Sin registros de movimientos en el rango seleccionado.")

        with g_col4:
            st.markdown("##### ⏱ Tendencia de Finalización de Tareas (Lead Time)")
            if not df_tr_filtrado.empty:
                df_tr_f = df_tr_filtrado.copy()

                df_tr_f['f_sol'] = pd.to_datetime(df_tr_f['Fecha_Solicitud'], errors='coerce')
                df_tr_f['f_imp'] = pd.to_datetime(df_tr_f['Fecha_Impresion'], errors='coerce')
                df_tr_f['f_fin'] = pd.to_datetime(df_tr_f['Fecha_Finalizacion'], errors='coerce')

                df_tr_f['Días Carga a Impresión'] = (df_tr_f['f_imp'] - df_tr_f['f_sol']).dt.days
                df_tr_f['Días Impresión a Finalización'] = (df_tr_f['f_fin'] - df_tr_f['f_imp']).dt.days
                df_tr_f['Días Totales de Resolución'] = (df_tr_f['f_fin'] - df_tr_f['f_sol']).dt.days

                df_tr_valid = df_tr_f.dropna(subset=['f_sol']).copy()
                if not df_tr_valid.empty:
                    df_tr_valid['Mes_dt'] = df_tr_valid['f_sol'].dt.to_period('M')
                    df_tr_valid['Mes'] = df_tr_valid['f_sol'].dt.strftime('%b %Y')
                    
                    df_tiempos_mes = df_tr_valid.groupby(['Mes_dt', 'Mes'])[[
                        'Días Carga a Impresión', 
                        'Días Impresión a Finalización', 
                        'Días Totales de Resolución'
                    ]].mean().reset_index().sort_values('Mes_dt')

                    if not df_tiempos_mes.empty:
                        fig_time = px.line(
                            df_tiempos_mes, x='Mes', 
                            y=['Días Totales de Resolución', 'Días Carga a Impresión', 'Días Impresión a Finalización'],
                            markers=True, template="plotly_dark", line_shape="spline",
                            labels={'value': 'Días Promedio', 'variable': 'Métrica'},
                            color_discrete_map={
                                'Días Totales de Resolución': '#3b82f6', 
                                'Días Carga a Impresión': '#f59e0b',
                                'Días Impresión a Finalización': '#a855f7'
                            }
                        )
                        fig_time.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="", yaxis_title="Días", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig_time, use_container_width=True)
                    else:
                        st.info("Aún no hay solicitudes suficientes para calcular promedios de respuesta.")
                else:
                    st.info("Aún no hay solicitudes suficientes con fechas válidas.")
            else:
                st.info("El Tracker de Ejecución Logística no contiene registros.")

# ==========================================
# VISTA: TRACKER DE EJECUCIÓN LOGÍSTICA
# ==========================================
tab_tracker = obtener_tab("🚚 Tracker de Ejecución Logística") or obtener_tab("🚚 Estado de Solicitudes")
if tab_tracker:
    with tab_tracker:
        st.subheader("🚚 Tracker de Ejecución Logística")
        
        es_logistica = (rol_actual == "Logistica")
        
        if es_logistica:
            st.write("Gestiona la carga en SAP, impresión y entrega física de tarjetas mediante botones de flujo directo.")
        else:
            st.info("🔒 **Modo Consulta (Solo Lectura):** Esta sección es gestionada operativamente por el grupo de **Logística**. Puedes visualizar el estado en tiempo real de cada solicitud.")

        df_tr = cargar_tracker()
        
        if df_tr.empty:
            st.info("No hay solicitudes registradas aún en el tracker.")
        else:
            with st.expander("🔍 Filtros de Búsqueda", expanded=True):
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    filtro_id = st.text_input("Filtrar por ID Solicitud / Código K / Material:", key="tr_f_id").strip().upper()
                with col2:
                    filtro_puesto = st.text_input("Filtrar por Puesto Destino:", key="tr_f_puesto").strip().upper()
                with col3:
                    filtro_sap = st.selectbox("Estado SAP:", ["Todos", "SI", "NO"], key="tr_f_sap")
                with col4:
                    filtro_fisico = st.selectbox("Estado Físico:", ["Todos", "Pendiente", "En Proceso", "Impreso", "Entregado"], key="tr_f_fisico")

            df_filtrado_tr = df_tr.copy()
            if filtro_id:
                df_filtrado_tr = df_filtrado_tr[
                    df_filtrado_tr['ID_Solicitud'].str.contains(filtro_id, case=False, na=False) |
                    df_filtrado_tr['Código_K'].str.contains(filtro_id, case=False, na=False) |
                    df_filtrado_tr['Material'].str.contains(filtro_id, case=False, na=False)
                ]
            if filtro_puesto:
                df_filtrado_tr = df_filtrado_tr[df_filtrado_tr['Puesto_Destino'].str.contains(filtro_puesto, case=False, na=False)]
            if filtro_sap != "Todos":
                df_filtrado_tr = df_filtrado_tr[df_filtrado_tr['Cargado_SAP'] == filtro_sap]
            if filtro_fisico != "Todos":
                df_filtrado_tr = df_filtrado_tr[df_filtrado_tr['Estado_Fisico'] == filtro_fisico]

            st.write(f"Mostrando **{len(df_filtrado_tr)}** de **{len(df_tr)}** solicitudes.")
            st.markdown("---")

            for idx, row in df_filtrado_tr.iterrows():
                sol_id = row['ID_Solicitud']
                
                with st.container():
                    st.markdown(f"""
                    <div class="tracker-card">
                        <h4>📋 Solicitud: {sol_id} | KB: <span style="color:#38bdf8;">{row['Código_K']}</span> | Material: <span style="color:#f59e0b;">{row['Material']}</span></h4>
                        <p style="margin:2px 0;"><b>Puesto Destino:</b> {row['Puesto_Destino']} | <b>Medio:</b> {row['Medio']} | <b>Cambio:</b> {row['Cambio']} | <b>Acción Requerida:</b> {row['Acción_Requerida']}</p>
                        <p style="margin:2px 0; font-size:0.85rem; color:#888;">Creado por: {row['Usuario_Procesos']} el {row['Fecha_Solicitud']}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    c_sap, c_imp, c_estado, c_obs = st.columns([1.5, 1.5, 2, 2.5])

                    with c_sap:
                        st.markdown("**1. Carga SAP**")
                        cargado_sap = row['Cargado_SAP'] == 'SI'
                        if cargado_sap:
                            st.success("✅ Cargado en SAP")
                        else:
                            st.warning("⏳ Pendiente SAP")
                            if es_logistica:
                                if st.button("Marcar Cargado en SAP", key=f"btn_sap_{sol_id}"):
                                    df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Cargado_SAP'] = 'SI'
                                    guardar_tracker(df_tr)
                                    st.success("Carga en SAP registrada.")
                                    st.rerun()

                    with c_imp:
                        st.markdown("**2. Impresión**")
                        impreso = row['Impreso'] == 'SI'
                        if impreso:
                            st.success(f"🖨️ Impreso ({row['Fecha_Impresion']})")
                        else:
                            st.warning("⏳ Pendiente Impresión")
                            if es_logistica:
                                if st.button("Marcar como Impreso", key=f"btn_imp_{sol_id}"):
                                    now_date = datetime.now(ARG_TZ).strftime("%Y-%m-%d")
                                    df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Impreso'] = 'SI'
                                    df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Fecha_Impresion'] = now_date
                                    if df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Estado_Fisico'].values[0] == 'Pendiente':
                                        df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Estado_Fisico'] = 'En Proceso'
                                    guardar_tracker(df_tr)
                                    st.success("Impresión registrada.")
                                    st.rerun()

                    with c_estado:
                        st.markdown("**3. Estado Físico**")
                        estado_actual = row['Estado_Fisico']
                        st.info(f"Estado Actual: **{estado_actual}**")
                        
                        if es_logistica:
                            col_b1, col_b2 = st.columns(2)
                            with col_b1:
                                if estado_actual != "En Proceso" and estado_actual != "Entregado":
                                    if st.button("▶ En Proceso", key=f"btn_proc_{sol_id}"):
                                        df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Estado_Fisico'] = 'En Proceso'
                                        guardar_tracker(df_tr)
                                        st.rerun()
                            with col_b2:
                                if estado_actual != "Entregado":
                                    if st.button("✅ Finalizar", key=f"btn_fin_{sol_id}"):
                                        now_date = datetime.now(ARG_TZ).strftime("%Y-%m-%d")
                                        df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Estado_Fisico'] = 'Entregado'
                                        df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Fecha_Finalizacion'] = now_date
                                        guardar_tracker(df_tr)
                                        st.success("Solicitud Finalizada.")
                                        st.rerun()

                    with c_obs:
                        st.markdown("**4. Observaciones**")
                        obs_val = "" if row['Observación'] == "-" else row['Observación']
                        
                        if es_logistica:
                            nueva_obs = st.text_input("Observación:", value=obs_val, key=f"txt_obs_{sol_id}")
                            if st.button("💾 Guardar Obs", key=f"btn_obs_{sol_id}"):
                                val_save = nueva_obs.strip() if nueva_obs.strip() else "-"
                                df_tr.loc[df_tr['ID_Solicitud'] == sol_id, 'Observación'] = val_save
                                guardar_tracker(df_tr)
                                st.success("Observación guardada.")
                                st.rerun()
                        else:
                            st.text_input("Observación:", value=obs_val, key=f"txt_obs_read_{sol_id}", disabled=True)

                    st.markdown("---")

# ==========================================
# VISTA: CREAR NUEVO KANBAN (PROCESOS)
# ==========================================
tab_crear = obtener_tab("➕ Crear Nuevo Kanban")
if tab_crear:
    with tab_crear:
        st.subheader("➕ Alta de Nuevo Kanban")
        
        col1, col2 = st.columns(2)
        
        with col1:
            tipo_etiqueta = st.selectbox("Tipo de Etiqueta:", ["KI", "KE"], key="c_tipo_etiq")
            material_input = st.text_input("Material (Código SAP):", key="c_mat_input").strip().upper()
            
            # Búsqueda automática en Lote Packaging
            info_pkg = dict_pkg.get(material_input, {})
            um_sugerida = info_pkg.get('unidad', 'UN')
            medio_pkg_sugerido = info_pkg.get('medio', '')
            cant_pkg_sugerida = info_pkg.get('cantidad', None)
            
            # Mensaje informativo si existe lote en Packaging
            if material_input:
                if info_pkg:
                    if cant_pkg_sugerida is not None:
                        cant_fmt = int(cant_pkg_sugerida) if cant_pkg_sugerida == int(cant_pkg_sugerida) else cant_pkg_sugerida
                        st.info(f"📦 El código **{material_input}** tiene **{cant_fmt}** de Lote de Packaging.")
                    else:
                        st.caption(f"ℹ️️ Material encontrado en packaging sin lote definido: **UM Base:** {um_sugerida}")
                else:
                    st.caption("ℹ️ El código de material no se encuentra en el archivo de Packaging. Se usarán valores por defecto.")

            centro = st.text_input("Centro:", value="A110", disabled=True, help="El centro de producción es fijo: A110")
            alm_origen = st.selectbox("Almacén Origen:", LISTA_ALMACENES, index=0, key="c_alm_orig")
            puesto_origen = st.text_input("Puesto trabajo Origen:", key="c_puesto_orig").strip().upper()
            
        with col2:
            alm_destino = st.selectbox("Almacén Destino:", LISTA_ALMACENES, index=1, key="c_alm_dest")
            puestos_posibles = ALMACENES_PUESTOS.get(alm_destino, [])
            puesto_destino = st.selectbox("Puesto de trabajo Destino:", puestos_posibles, key="c_puesto_dest") if puestos_posibles else st.text_input("Puesto de trabajo Destino:", key="c_puesto_dest_txt").strip().upper()
            
            tipo_kanban = st.radio("Tipo de Kanban:", ["GAVETA", "TARJETA"], horizontal=True, key="c_tipo_kb")
            
            # Selección dinámica de Medio según tipo de Kanban
            if tipo_kanban == "GAVETA":
                lista_medios = OPCIONES_GAVETA
                idx_default = 0
                if medio_pkg_sugerido in lista_medios:
                    idx_default = lista_medios.index(medio_pkg_sugerido)
                medio = st.selectbox("Medio / Tamaño Gaveta:", lista_medios, index=idx_default, key=f"c_medio_gav_{material_input}")
            else:
                lista_medios = OPCIONES_SOPORTE_TARJETA
                idx_default = 0
                if medio_pkg_sugerido in lista_medios:
                    idx_default = lista_medios.index(medio_pkg_sugerido)
                medio = st.selectbox("Medio / Soporte Tarjeta:", lista_medios, index=idx_default, key=f"c_medio_tarj_{material_input}")
                
        st.markdown("---")
        col_cant1, col_cant2, col_cant3 = st.columns(3)
        
        # Determinar Lote y Unidad precargada
        val_cant_repo_init = float(cant_pkg_sugerida) if cant_pkg_sugerida is not None else 10.0
        
        idx_um_default = 0
        if um_sugerida in OPCIONES_UNIDAD_MEDIDA:
            idx_um_default = OPCIONES_UNIDAD_MEDIDA.index(um_sugerida)

        with col_cant1:
            cant_repo = st.number_input(
                "Cantidad Reposición:", 
                min_value=1.0, 
                step=1.0, 
                value=val_cant_repo_init, 
                key=f"c_cant_repo_{material_input}"
            )
        with col_cant2:
            unid_repo = st.selectbox(
                "Unidad Reposición:", 
                OPCIONES_UNIDAD_MEDIDA, 
                index=idx_um_default, 
                key=f"c_unid_repo_{material_input}"
            )
        with col_cant3:
            if tipo_kanban == "GAVETA":
                cant_pp = st.number_input("Cantidad Punto de Pedido:", value=cant_repo, disabled=True, help="En GAVETA, la Cantidad Punto de Pedido es idéntica a la Cantidad Reposición.", key=f"c_cant_pp_gav_{material_input}")
            else:
                val_pp_default = min(cant_repo - 1.0, 5.0) if cant_repo > 1 else 1.0
                cant_pp = st.number_input("Cantidad Punto de Pedido:", min_value=1.0, step=1.0, value=val_pp_default, key=f"c_cant_pp_tarj_{material_input}")

        tiempo_abast = st.number_input("Tiempo preparación abast. (en días):", min_value=0, value=1, key="c_tiempo_abast")
        
        if st.button("✨ Crear Kanban", type="primary", use_container_width=True, key="c_btn_submit"):
            if not material_input:
                st.error("❌ El código de Material es obligatorio.")
            elif tipo_kanban == "TARJETA" and cant_pp >= cant_repo:
                st.error(f"❌ Para tipo TARJETA, la Cantidad Punto de Pedido ({cant_pp}) debe ser ESTRICTAMENTE MENOR a la Cantidad Reposición ({cant_repo}).")
            else:
                nuevo_k = obtener_siguiente_codigo_k(df_kanbans)
                now_str = obtener_fecha_hora_arg()
                user_actual = st.session_state['usuario_email']
                
                nueva_fila = pd.DataFrame([{
                    'N° Etiquetas': nuevo_k,
                    'Tipo Etiqueta': tipo_etiqueta,
                    'Tipo Kanban': tipo_kanban,
                    'Medio': medio,
                    'Material': material_input,
                    'Centro': "A110",
                    'Almacén Origen': alm_origen,
                    'Almacen Destino': alm_destino,
                    'Puesto trabajo Origen': puesto_origen,
                    'Puesto de trabajo destino': puesto_destino,
                    'Cantidad Reposicion': str(cant_repo),
                    'Unidad Reposicion': unid_repo,
                    'Cantidad Punto de Pedido': str(cant_pp),
                    'Tiempo preparación abast. (en días)': str(tiempo_abast),
                    'Fecha Modificación': now_str,
                    'Usuario Modificación': user_actual
                }])
                
                df_actualizado = pd.concat([df_kanbans, nueva_fila], ignore_index=True)
                actualizar_base_kanbans(df_actualizado)
                
                registrar_log("CREACIÓN", nuevo_k, material_input, medio, alm_destino, puesto_destino, f"Creación inicial del Kanban {nuevo_k}", user_actual)
                crear_solicitud_tracker(material_input, nuevo_k, tipo_kanban, puesto_destino, medio, "Alta de Kanban", "Creación e Impresión", user_actual)
                
                st.success(f"✅ ¡Kanban {nuevo_k} creado exitosamente y registrado en la cola del Tracker!")
                st.rerun()

# ==========================================
# VISTA: MODIFICAR Y ELIMINAR (PROCESOS)
# ==========================================
tab_mod = obtener_tab("✏️ Modificar y Eliminar")
if tab_mod:
    with tab_mod:
        st.subheader("✏️ Modificación y Eliminación de Kanbans")
        
        if df_kanbans.empty:
            st.info("ℹ️️ No hay Kanbans registrados en la base de datos.")
        else:
            busqueda = st.text_input("🔍 Buscar por Código K o Material (deja en blanco para ver todos):", key="mod_search").strip().upper()
            
            # Filtrado por búsqueda
            if busqueda:
                df_res = df_kanbans[
                    df_kanbans['N° Etiquetas'].astype(str).str.contains(busqueda, na=False) | 
                    df_kanbans['Material'].astype(str).str.contains(busqueda, na=False)
                ]
            else:
                df_res = df_kanbans.copy()
            
            if df_res.empty:
                st.warning("No se encontraron registros coincidentes con la búsqueda.")
            else:
                # Opciones para el desplegable mostrando Código K y Material exactos
                opciones_dict = {
                    f"{r['N° Etiquetas']} — {r['Material']} ({r['Puesto de trabajo destino']})": str(r['N° Etiquetas']) 
                    for _, r in df_res.iterrows()
                }
                
                k_label_sel = st.selectbox("Seleccione el Kanban a gestionar:", list(opciones_dict.keys()), key="mod_k_select")
                k_seleccionado = opciones_dict[k_label_sel]
                
                # Extraer la fila correspondiente al Kanban seleccionado
                fila_k = df_kanbans[df_kanbans['N° Etiquetas'].astype(str) == k_seleccionado].iloc[0]
                
                # --- EXTRACCIÓN Y LIMPIEZA DE DATOS PRECARGADOS ---
                val_material = str(fila_k['Material']).strip() if pd.notna(fila_k['Material']) else ""
                val_tipo_etiq = str(fila_k['Tipo Etiqueta']).strip().upper() if pd.notna(fila_k['Tipo Etiqueta']) else "KI"
                val_alm_orig = str(fila_k['Almacén Origen']).strip() if pd.notna(fila_k['Almacén Origen']) else "L010"
                val_puesto_orig = str(fila_k['Puesto trabajo Origen']).strip() if pd.notna(fila_k['Puesto trabajo Origen']) else ""
                
                # Regla de Negocio L010 / Limpieza de nan
                if val_alm_orig == "L010" or val_puesto_orig.lower() in ["nan", "", "none"]:
                    val_puesto_orig = "PRINCIPAL"

                val_alm_dest = str(fila_k['Almacen Destino']).strip() if pd.notna(fila_k['Almacen Destino']) else ""
                val_puesto_dest = str(fila_k['Puesto de trabajo destino']).strip() if pd.notna(fila_k['Puesto de trabajo destino']) else ""
                val_tipo_kb = str(fila_k['Tipo Kanban']).strip().upper() if pd.notna(fila_k['Tipo Kanban']) else "GAVETA"
                val_medio = str(fila_k['Medio']).strip() if pd.notna(fila_k['Medio']) else ""
                
                # --- PESTAÑAS DE ACCIÓN ---
                tab_m1, tab_m2 = st.tabs(["✏️ Modificar Datos", "🗑 Eliminar Kanban"])
                
                with tab_m1:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Tipo Etiqueta
                        idx_tipo_e = 0 if val_tipo_etiq == "KI" else 1
                        m_tipo_etiqueta = st.selectbox("Tipo Etiqueta:", ["KI", "KE"], index=idx_tipo_e, key=f"m_te_{k_seleccionado}")
                        
                        # Material y Centro
                        m_material = st.text_input("Material:", value=val_material, key=f"m_mat_{k_seleccionado}").strip().upper()
                        m_centro = st.text_input("Centro:", value="A110", disabled=True, key=f"m_cen_{k_seleccionado}")
                        
                        # Almacén Origen
                        idx_origen = LISTA_ALMACENES.index(val_alm_orig) if val_alm_orig in LISTA_ALMACENES else 0
                        m_alm_origen = st.selectbox("Almacén Origen:", LISTA_ALMACENES, index=idx_origen, key=f"m_ao_{k_seleccionado}")
                        
                        # Regla L010 para Puesto Origen
                        if m_alm_origen == "L010":
                            m_puesto_origen = st.text_input("Puesto trabajo Origen:", value="PRINCIPAL", disabled=True, key=f"m_po_dis_{k_seleccionado}")
                        else:
                            m_puesto_origen = st.text_input("Puesto trabajo Origen:", value=val_puesto_orig, key=f"m_po_txt_{k_seleccionado}").strip().upper()
                        
                    with col2:
                        # Almacén Destino
                        idx_dest = LISTA_ALMACENES.index(val_alm_dest) if val_alm_dest in LISTA_ALMACENES else 0
                        m_alm_destino = st.selectbox("Almacén Destino:", LISTA_ALMACENES, index=idx_dest, key=f"m_ad_{k_seleccionado}")
                        
                        # Puesto Destino según Almacén Destino
                        puestos_pos = ALMACENES_PUESTOS.get(m_alm_destino, [])
                        if puestos_pos:
                            idx_puesto = puestos_pos.index(val_puesto_dest) if val_puesto_dest in puestos_pos else 0
                            m_puesto_destino = st.selectbox("Puesto de trabajo Destino:", puestos_pos, index=idx_puesto, key=f"m_pd_sel_{k_seleccionado}")
                        else:
                            m_puesto_destino = st.text_input("Puesto de trabajo Destino:", value=val_puesto_dest, key=f"m_pd_txt_{k_seleccionado}").strip().upper()
                        
                        # Tipo Kanban
                        idx_radio_k = 0 if val_tipo_kb == "GAVETA" else 1
                        m_tipo_kanban = st.radio("Tipo de Kanban:", ["GAVETA", "TARJETA"], index=idx_radio_k, horizontal=True, key=f"m_tk_{k_seleccionado}")
                        
                        # Medio
                        if m_tipo_kanban == "GAVETA":
                            idx_med = OPCIONES_GAVETA.index(val_medio) if val_medio in OPCIONES_GAVETA else 0
                            m_medio = st.selectbox("Medio / Tamaño Gaveta:", OPCIONES_GAVETA, index=idx_med, key=f"m_med_g_{k_seleccionado}")
                        else:
                            idx_med = OPCIONES_SOPORTE_TARJETA.index(val_medio) if val_medio in OPCIONES_SOPORTE_TARJETA else 0
                            m_medio = st.selectbox("Medio / Soporte Tarjeta:", OPCIONES_SOPORTE_TARJETA, index=idx_med, key=f"m_med_t_{k_seleccionado}")
                            
                    st.markdown("---")
                    col_m_c1, col_m_c2, col_m_c3 = st.columns(3)
                    
                    with col_m_c1:
                        try:
                            val_cant_repo = float(fila_k['Cantidad Reposicion'])
                        except (ValueError, TypeError):
                            val_cant_repo = 10.0
                        m_cant_repo = st.number_input("Cantidad Reposición:", value=val_cant_repo, key=f"m_cr_{k_seleccionado}")
                        
                    with col_m_c2:
                        val_um_actual = str(fila_k['Unidad Reposicion']).strip().upper() if pd.notna(fila_k['Unidad Reposicion']) else "UN"
                        idx_um_mod = OPCIONES_UNIDAD_MEDIDA.index(val_um_actual) if val_um_actual in OPCIONES_UNIDAD_MEDIDA else 0
                        m_unid_repo = st.selectbox("Unidad Reposición:", OPCIONES_UNIDAD_MEDIDA, index=idx_um_mod, key=f"m_ur_{k_seleccionado}")
                        
                    with col_m_c3:
                        if m_tipo_kanban == "GAVETA":
                            m_cant_pp = st.number_input("Cantidad Punto Pedido:", value=m_cant_repo, disabled=True, key=f"m_cpp_g_{k_seleccionado}")
                        else:
                            try:
                                val_pp_init = float(fila_k['Cantidad Punto de Pedido'])
                            except (ValueError, TypeError):
                                val_pp_init = 5.0
                            m_cant_pp = st.number_input("Cantidad Punto Pedido:", value=val_pp_init, key=f"m_cpp_t_{k_seleccionado}")

                    try:
                        val_tiempo_init = int(float(fila_k['Tiempo preparación abast. (en días)']))
                    except (ValueError, TypeError):
                        val_tiempo_init = 1
                    m_tiempo_abast = st.number_input("Tiempo preparación abast. (en días):", value=val_tiempo_init, key=f"m_ta_{k_seleccionado}")
                    
                    if st.button("💾 Guardar Cambios", type="primary", use_container_width=True, key=f"btn_save_{k_seleccionado}"):
                        if m_tipo_kanban == "TARJETA" and m_cant_pp >= m_cant_repo:
                            st.error(f"❌ Para tipo TARJETA, la Cantidad Punto de Pedido ({m_cant_pp}) debe ser ESTRICTAMENTE MENOR a la Cantidad Reposición ({m_cant_repo}).")
                        else:
                            now_str = obtener_fecha_hora_arg()
                            user_act = st.session_state['usuario_email']
                            
                            idx_global = df_kanbans[df_kanbans['N° Etiquetas'].astype(str) == k_seleccionado].index[0]
                            
                            df_kanbans.loc[idx_global, 'Tipo Etiqueta'] = m_tipo_etiqueta
                            df_kanbans.loc[idx_global, 'Tipo Kanban'] = m_tipo_kanban
                            df_kanbans.loc[idx_global, 'Medio'] = m_medio
                            df_kanbans.loc[idx_global, 'Material'] = m_material
                            df_kanbans.loc[idx_global, 'Centro'] = "A110"
                            df_kanbans.loc[idx_global, 'Almacén Origen'] = m_alm_origen
                            df_kanbans.loc[idx_global, 'Almacen Destino'] = m_alm_destino
                            df_kanbans.loc[idx_global, 'Puesto trabajo Origen'] = m_puesto_origen
                            df_kanbans.loc[idx_global, 'Puesto de trabajo destino'] = m_puesto_destino
                            df_kanbans.loc[idx_global, 'Cantidad Reposicion'] = str(m_cant_repo)
                            df_kanbans.loc[idx_global, 'Unidad Reposicion'] = m_unid_repo
                            df_kanbans.loc[idx_global, 'Cantidad Punto de Pedido'] = str(m_cant_pp)
                            df_kanbans.loc[idx_global, 'Tiempo preparación abast. (en días)'] = str(m_tiempo_abast)
                            df_kanbans.loc[idx_global, 'Fecha Modificación'] = now_str
                            df_kanbans.loc[idx_global, 'Usuario Modificación'] = user_act
                            
                            actualizar_base_kanbans(df_kanbans)
                            registrar_log("MODIFICACIÓN", k_seleccionado, m_material, m_medio, m_alm_destino, m_puesto_destino, f"Modificación de datos del Kanban {k_seleccionado}", user_act)
                            crear_solicitud_tracker(m_material, k_seleccionado, m_tipo_kanban, m_puesto_destino, m_medio, "Modificación de Datos", "Actualización e Reimpresión", user_act)
                            
                            st.success(f"✅ ¡Kanban {k_seleccionado} actualizado correctamente!")
                            st.rerun()

                with tab_m2:
                    st.warning(f"⚠️ ¿Está seguro que desea eliminar permanentemente el Kanban **{k_seleccionado}**?")
                    if st.button("🔥 Confirmar Eliminación", type="primary", key=f"btn_del_{k_seleccionado}"):
                        user_act = st.session_state['usuario_email']
                        df_nuevo = df_kanbans[df_kanbans['N° Etiquetas'].astype(str) != k_seleccionado]
                        actualizar_base_kanbans(df_nuevo)
                        
                        registrar_log("ELIMINACIÓN", k_seleccionado, val_material, val_medio, val_alm_dest, val_puesto_dest, f"Eliminación de Kanban {k_seleccionado}", user_act)
                        crear_solicitud_tracker(val_material, k_seleccionado, val_tipo_kb, val_puesto_dest, val_medio, "Baja de Kanban", "Retiro de Tarjeta/Gaveta", user_act)
                        
                        st.success(f"🗑 Kanban {k_seleccionado} eliminado correctamente.")
                        st.rerun()
# ==========================================
# VISTA: CONSULTA Y EXPORTAR TABLA Z (SAP)
# ==========================================
tab_consulta = obtener_tab("📊 Consulta y Exportar Tabla Z (SAP)")
if tab_consulta:
    with tab_consulta:
        st.subheader("📊 Tabla Z de Kanbans (Estructura SAP)")
        st.write("Vista general de datos registrados con opción de exportación a Excel y filtros avanzados.")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_k = st.text_input("Filtrar por Código K o Material:", key="cons_k").strip().upper()
        with col_f2:
            filtro_alm_dest = st.selectbox("Filtrar por Almacén Destino:", ["Todos"] + LISTA_ALMACENES, key="cons_alm")
        with col_f3:
            filtro_tipo = st.selectbox("Filtrar por Tipo Kanban:", ["Todos", "GAVETA", "TARJETA"], key="cons_tipo")
            
        df_ver = df_kanbans.copy()
        
        if filtro_k:
            df_ver = df_ver[
                df_ver['N° Etiquetas'].str.contains(filtro_k, na=False) |
                df_ver['Material'].str.contains(filtro_k, na=False)
            ]
        if filtro_alm_dest != "Todos":
            df_ver = df_ver[df_ver['Almacen Destino'] == filtro_alm_dest]
        if filtro_tipo != "Todos":
            df_ver = df_ver[df_ver['Tipo Kanban'] == filtro_tipo]
            
        st.write(f"Mostrando **{len(df_ver)}** registros.")
        st.dataframe(df_ver, use_container_width=True, hide_index=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_ver.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        buffer.seek(0)
        
        st.download_button(
            label="📥 Exportar Tabla Z a Excel",
            data=buffer,
            file_name=f"TablaZ_Kanbans_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

# ==========================================
# VISTA: HISTORIAL DE AUDITORÍA
# ==========================================
tab_hist = obtener_tab("📜 Historial Auditoría")
if tab_hist:
    with tab_hist:
        st.subheader("📜 Historial de Cambios y Auditoría")
        st.write("Registro detallado de acciones realizadas sobre los Kanbans.")
        
        df_logs_ver = cargar_logs()
        
        if df_logs_ver.empty:
            st.info("No hay registros en el historial de auditoría.")
        else:
            st.dataframe(df_logs_ver, use_container_width=True, hide_index=True)
            
            buf_log = io.BytesIO()
            with pd.ExcelWriter(buf_log, engine='openpyxl') as writer:
                df_logs_ver.to_excel(writer, sheet_name="Auditoria", index=False)
            buf_log.seek(0)
            
            st.download_button(
                label="📥 Exportar Auditoría a Excel",
                data=buf_log,
                file_name=f"Historial_Auditoria_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# ==========================================
# VISTA: MI PERFIL Y HERRAMIENTAS
# ==========================================
tab_perfil = obtener_tab("👤 Mi Perfil")
if tab_perfil:
    with tab_perfil:
        st.subheader("👤 Configuración de Usuario y Herramientas")
        
        user_actual = st.session_state['usuario_email']
        rol_actual_val = st.session_state['usuario_rol']
        
        st.write(f"**Usuario:** {user_actual}")
        st.write(f"**Rol Asignado:** {rol_actual_val}")
        
        st.markdown("---")
        st.subheader("🔒 Cambiar Contraseña")
        with st.form("form_change_pass"):
            pass_curr = st.text_input("Contraseña Actual:", type="password")
            pass_new1 = st.text_input("Nueva Contraseña:", type="password")
            pass_new2 = st.text_input("Confirmar Nueva Contraseña:", type="password")
            
            if st.form_submit_button("Actualizar Contraseña"):
                if user_actual in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[user_actual]["pass"] == pass_curr:
                    if pass_new1 == pass_new2 and pass_new1 != "":
                        USUARIOS_REGISTRADOS[user_actual]["pass"] = pass_new1
                        guardar_usuarios(USUARIOS_REGISTRADOS)
                        st.success("✅ Contraseña actualizada con éxito.")
                    else:
                        st.error("❌ Las nuevas contraseñas no coinciden o están vacías.")
                else:
                    st.error("❌ La contraseña actual es incorrecta.")

        if rol_actual_val == "Procesos":
            st.markdown("---")
            st.subheader("🧹 Mantenimiento de Sistema (Solo Procesos)")
            with st.expander("⚠ Zona de Limpieza de Historiales"):
                st.write("Esta acción borrará el historial de auditoría y los registros del tracker de ejecución. **No afectará a la base de Kanbans activos (Tabla Z).**")
                if st.button("🚨 Resetear Historiales y Tracker de Prueba"):
                    limpiar_historiales_de_prueba()
                    st.success("✅ Historiales y Tracker reseteados correctamente.")
                    st.rerun()
