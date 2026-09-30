import io
import json
import os
import re
from datetime import datetime

import pandas as pd
import plotly.express as px
import pytz
import streamlit as st

st.set_page_config(page_title="Gestor de Kanbans - Crucianelli", layout="wide")


# ==========================================
# FUNCIONES AUXILIARES Y NORMALIZACIÓN
# ==========================================
def normalizar_codigo_sap(codigo_raw: str) -> str:
  """Normaliza el código SAP al estándar: 2 a 3 letras + 6 dígitos.

  Ejemplos: 'cm16' -> 'CM000016', 'mcb610' -> 'MCB000610'
  """
  if not codigo_raw:
    return ""
  match = re.match(
      r"^([a-zA-R]{2,3})\s*(\d{1,6})$", str(codigo_raw).strip(), re.IGNORECASE
  )
  if match:
    letras, numeros = match.groups()
    return f"{letras.upper()}{numeros.zfill(6)}"
  return str(codigo_raw).strip().upper()


# ==========================================
# ESTILOS CSS PERSONALIZADOS (DARK PREMIUM)
# ==========================================
st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

ARG_TZ = pytz.timezone("America/Argentina/Buenos_Aires")


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

LOG_COLUMNS = [
    "Fecha_Hora",
    "Acción",
    "Código_K",
    "Material",
    "Medio",
    "Almacén_Destino",
    "Puesto_Destino",
    "Detalle_Cambio",
    "Usuario",
]
TRACKER_COLUMNS = [
    "ID_Solicitud",
    "Fecha_Solicitud",
    "Material",
    "Código_K",
    "Tipo_KB",
    "Puesto_Destino",
    "Medio",
    "Cambio",
    "Acción_Requerida",
    "Cargado_SAP",
    "Impreso",
    "Fecha_Impresion",
    "Estado_Fisico",
    "Fecha_Finalizacion",
    "Observación",
    "Usuario_Procesos",
]

ROLES_PREDEFINIDOS = {
    # PROCESOS
    "jairc@crucianelli.com": "Procesos",
    "mmagarello@crucianelli.com": "Procesos",
    "mcabral@crucianelli.com": "Procesos",
    "gtuninetti@crucianelli.com": "Procesos",
    "produccion@crucianelli.com": "Procesos",
    "abacelli@crucianelli.com": "Procesos",
    "tabrate@crucianelli.com": "Procesos",
    "llatanzi@crucianelli.com": "Procesos",
    # LOGÍSTICA
    "mlopez@crucianelli.com": "Logistica",
    "recepcion3@crucianelli.com": "Logistica",
    "gpereyra@crucianelli.com": "Logistica",
    "jporta@crucianelli.com": "Logistica",
    "spetetta@crucianelli.com": "Logistica",
    "gfiianchini@crucianelli.com": "Logistica",
    "ileon@crucianelli.com": "Logistica",
    # CONSULTA
    "fany@crucianelli.com": "Consulta",
    "strillini@crucianelli.com": "Consulta",
    "apicotto@crucianelli.com": "Consulta",
    "fsolis@crucianelli.com": "Consulta",
    "isola@crucianelli.com": "Consulta",
    "bfrutos@crucianelli.com": "Consulta",
    "rpaul@crucianelli.com": "Consulta",
    "mscrofono@crucianelli.com": "Consulta",
    "gigli@crucianelli.com": "Consulta",
    "ftrillini@crucianelli.com": "Consulta",
    "psantilli@crucianelli.com": "Consulta",
    "activacion@crucianelli.com": "Consulta",
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
              "rol": val.get("rol", rol_asig),
          }
    except Exception:
      pass
  return dict_users


USUARIOS_REGISTRADOS = cargar_usuarios()

COLUMNS = [
    "N° Etiquetas",
    "Tipo Etiqueta",
    "Tipo Kanban",
    "Medio",
    "Material",
    "Centro",
    "Almacén Origen",
    "Almacen Destino",
    "Puesto trabajo Origen",
    "Puesto de trabajo destino",
    "Cantidad Reposicion",
    "Unidad Reposicion",
    "Cantidad Punto de Pedido",
    "Tiempo preparación abast. (en días)",
    "Fecha Modificación",
    "Usuario Modificación",
]

ALMACENES_PUESTOS = {
    "P110": [
        "ARM_HORQ",
        "ARM_MAZ1",
        "CORTE_01",
        "MECANIZA",
        "PRENBAL1",
        "ROSC_REM",
    ],
    "P120": [
        "APUNCHAS",
        "SOLDCHA1",
        "SOLDMADR",
        "SOLDMAN1",
        "SOLDMAN2",
        "SOLDMAN3",
        "SOLDMAN4",
        "SOLDMAN5",
        "SOLDMAN6",
        "SOLDMAN7",
        "SOLDMAP1",
        "SOLDMAP2",
        "SOLDMAP3",
        "SOLROB06",
        "SOLROB08",
        "SOLROB09",
        "SOLROB10",
        "SOLROB12",
        "SOLROB13",
        "SOLROB14",
        "SOLROB15",
        "SOLROB16",
        "SOLROB17",
    ],
    "P130": ["MONTIN01", "MONTIN02", "MONTIN03", "MONTIN04", "MONTJAD1"],
    "P140": ["LAVADO01", "PINTURA1", "PINTURA2"],
    "P150": [
        "MONFIN01",
        "MONFIN02",
        "MONFIN03",
        "MONFIN04",
        "MTJBARAP",
        "MTJF01PD",
        "MTJF02PD",
        "MTJF03PD",
        "MTJPRS",
    ],
    "P160": [
        "ARCUCH01",
        "ARMBAR01",
        "ARMCUERP",
        "ARMDOSIF",
        "ARTOLVAS",
        "SUBCONJU",
        "TURBINAS",
    ],
    "P180": ["CARGAFIN", "MURFINAL"],
    "P190": ["HOSPITAL"],
    "CC01": ["POSVENTA"],
    "ID01": ["PROTOTIPO"],
    "L010": ["PRINCIPAL"],
}

LISTA_ALMACENES = list(ALMACENES_PUESTOS.keys())
OPCIONES_SOPORTE_TARJETA = [
    "SIN MEDIO DEFINIDO",
    "PALLET CHICO",
    "PALLET GRANDE",
    "CANASTO",
    "CAPACHO CHICO",
    "CAPACHO GRANDE",
    "RACK",
]
OPCIONES_GAVETA = ["S", "M", "L", "XL"]
OPCIONES_UNIDAD_MEDIDA = ["UN", "M", "KG", "L"]

if "usuario_email" not in st.session_state:
  st.session_state["usuario_email"] = None
if "usuario_rol" not in st.session_state:
  st.session_state["usuario_rol"] = None

# ==========================================
# PANTALLA DE AUTENTICACIÓN
# ==========================================
if not st.session_state["usuario_email"]:
  st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")
  col_auth, _ = st.columns([1.5, 2])
  with col_auth:
    st.markdown('<div class="card-container">', unsafe_allow_html=True)
    st.subheader("🔐 Acceso al Sistema")

    email_google = (
        st.text_input(
            "Correo Google Workspace (@crucianelli.com):",
            key="g_mail_input",
            placeholder="ejemplo@crucianelli.com",
        )
        .strip()
        .lower()
    )
    if st.button(
        "🌐 Iniciar Sesión con Google (@crucianelli.com)",
        use_container_width=True,
        key="btn_g_login",
    ):
      if not email_google:
        st.error("❌ Por favor ingrese su correo corporativo de Google.")
      elif not email_google.endswith("@crucianelli.com"):
        st.error(
            "❌ El correo debe pertenecer obligatoriamente a @crucianelli.com."
        )
      else:
        rol_asig = ROLES_PREDEFINIDOS.get(email_google, "Consulta")
        if email_google not in USUARIOS_REGISTRADOS:
          USUARIOS_REGISTRADOS[email_google] = {
              "pass": "google_oauth",
              "rol": rol_asig,
          }
          guardar_usuarios(USUARIOS_REGISTRADOS)

        st.session_state["usuario_email"] = email_google
        st.session_state["usuario_rol"] = rol_asig
        st.success(f"Bienvenido/a {email_google}")
        st.rerun()

    st.markdown(
        "<p style='text-align:center; color:#888; margin-top: 15px;'>— o acceso"
        " directo con contraseña —</p>",
        unsafe_allow_html=True,
    )

    tab_login, tab_register = st.tabs(
        ["🔑 Iniciar Sesión Directo", "📝 Registrarse"]
    )

    with tab_login:
      email_input = (
          st.text_input("Correo corporativo (@crucianelli.com):", key="log_email")
          .strip()
          .lower()
      )
      password_input = st.text_input(
          "Contraseña:", type="password", key="log_pass"
      )

      if st.button("Ingresar", type="primary", use_container_width=True):
        if not email_input or not password_input:
          st.error("❌ Complete correo y contraseña.")
        elif not email_input.endswith("@crucianelli.com"):
          st.error("❌ El correo debe ser del dominio @crucianelli.com.")
        elif (
            email_input in USUARIOS_REGISTRADOS
            and USUARIOS_REGISTRADOS[email_input]["pass"] == password_input
        ):
          st.session_state["usuario_email"] = email_input
          st.session_state["usuario_rol"] = USUARIOS_REGISTRADOS[email_input][
              "rol"
          ]
          st.success(f"Bienvenido/a {email_input}")
          st.rerun()
        else:
          st.error("❌ Credenciales incorrectas o usuario no registrado.")

    with tab_register:
      reg_email = (
          st.text_input("Correo corporativo (@crucianelli.com):", key="reg_email")
          .strip()
          .lower()
      )
      reg_pass1 = st.text_input(
          "Cree su contraseña:", type="password", key="reg_pass1"
      )
      reg_pass2 = st.text_input(
          "Confirme su contraseña:", type="password", key="reg_pass2"
      )

      if st.button("Crear Cuenta", use_container_width=True):
        if not reg_email or not reg_pass1 or not reg_pass2:
          st.error("❌ Complete todos los campos.")
        elif not reg_email.endswith("@crucianelli.com"):
          st.error(
              "❌ El correo debe ser obligatoriamente @crucianelli.com."
          )
        elif reg_pass1 != reg_pass2:
          st.error("❌ Las contraseñas no coinciden.")
        elif reg_email in USUARIOS_REGISTRADOS:
          st.warning(
              "⚠️ Este usuario ya se encuentra registrado. Inicie sesión"
              " directamente."
          )
        else:
          rol_asignado = ROLES_PREDEFINIDOS.get(reg_email, "Consulta")
          USUARIOS_REGISTRADOS[reg_email] = {
              "pass": reg_pass1,
              "rol": rol_asignado,
          }
          guardar_usuarios(USUARIOS_REGISTRADOS)
          st.success(
              f"✅ ¡Cuenta creada exitosamente para {reg_email}! (Rol"
              f" asignado: {rol_asignado}). Ya puede iniciar sesión."
          )
    st.markdown("</div>", unsafe_allow_html=True)
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
      df["Material"] = (
          df["Material"].fillna("").astype(str).apply(normalizar_codigo_sap)
      )
      df["N° Etiquetas"] = (
          df["N° Etiquetas"]
          .fillna("")
          .astype(str)
          .str.strip()
          .str.upper()
      )
      return df[COLUMNS].reset_index(drop=True)
    except Exception:
      pass

  if os.path.exists(DB_FILE):
    try:
      df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME, dtype=str)
      for col in COLUMNS:
        if col not in df.columns:
          df[col] = None

      df["Material"] = (
          df["Material"].fillna("").astype(str).apply(normalizar_codigo_sap)
      )
      df["N° Etiquetas"] = (
          df["N° Etiquetas"]
          .fillna("")
          .astype(str)
          .str.strip()
          .str.upper()
      )

      def determinar_tipo_kanban(row):
        cant_repo = row.get("Cantidad Reposicion")
        cant_pp = row.get("Cantidad Punto de Pedido")
        try:
          if pd.notna(cant_repo) and pd.notna(cant_pp):
            return (
                "GAVETA"
                if float(cant_repo) == float(cant_pp)
                else "TARJETA"
            )
        except (ValueError, TypeError):
          pass
        return "TARJETA"

      df["Tipo Kanban"] = df.apply(determinar_tipo_kanban, axis=1)
      df = df[COLUMNS].reset_index(drop=True)
      df.to_csv(LIVE_DB_FILE, index=False)
      return df
    except Exception:
      return pd.DataFrame(columns=COLUMNS)
  return pd.DataFrame(columns=COLUMNS)


def obtener_base_kanbans(forzar=False):
  if "df_kanbans_global" not in st.session_state or forzar:
    st.session_state["df_kanbans_global"] = cargar_base_desde_disco()
  return st.session_state["df_kanbans_global"]


def actualizar_base_kanbans(nuevo_df):
  df_limpio = nuevo_df.astype(str).reset_index(drop=True)
  st.session_state["df_kanbans_global"] = df_limpio

  try:
    df_limpio.to_csv(LIVE_DB_FILE, index=False)
  except Exception as e:
    st.error(f"⚠️ Error en persistencia CSV viva: {e}")

  try:
    with pd.ExcelWriter(DB_FILE, engine="openpyxl") as writer:
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

      col_mat = next(
          (
              c
              for c in df.columns
              if c.upper() in ["MATERIAL", "CODIGO", "CÓDIGO", "MATERIALES"]
          ),
          df.columns[0],
      )

      dict_pkg = {}
      for _, r in df.iterrows():
        mat = normalizar_codigo_sap(r[col_mat])

        medio_val = ""
        for c_med in ["Packaging", "Packaing", "Medio", "Soporte", "Envase"]:
          if c_med in df.columns and pd.notna(r[c_med]):
            medio_val = str(r[c_med]).strip()
            break

        unid_val = "UN"
        for c_uni in [
            "Unidad",
            "UM",
            "Unidad Reposicion",
            "Unidad de Medida",
        ]:
          if c_uni in df.columns and pd.notna(r[c_uni]):
            unid_val = str(r[c_uni]).strip().upper()
            break

        cant_val = None
        for c_cant in [
            "Lote Packaging",
            "Lote packaging",
            "Lote Packaging ",
            "Lote",
            "Cantidad",
            "Cantidad Reposicion",
            "Cant",
            "Lote de Reposicion",
            "Tamaño Lote",
        ]:
          if c_cant in df.columns and pd.notna(r[c_cant]):
            try:
              val_num = float(r[c_cant])
              if not pd.isna(val_num) and val_num > 0:
                cant_val = val_num
                break
            except (ValueError, TypeError):
              pass

        dict_pkg[mat] = {
            "medio": medio_val,
            "unidad": (
                unid_val if unid_val not in ["NAN", "NONE", ""] else "UN"
            ),
            "cantidad": cant_val,
        }
      return dict_pkg
    except Exception:
      return {}
  return {}


def cargar_logs():
  if os.path.exists(LOG_FILE):
    try:
      df_logs = pd.read_csv(LOG_FILE, on_bad_lines="skip", dtype=str)
      for col in LOG_COLUMNS:
        if col not in df_logs.columns:
          df_logs[col] = "-"
      mapeo_acciones = {
          "CREAR": "CREACIÓN",
          "CREO": "CREACIÓN",
          "CREACION": "CREACIÓN",
          "MODIFICAR": "MODIFICACIÓN",
          "ACTUALIZO": "MODIFICACIÓN",
          "MODIFICACION": "MODIFICACIÓN",
          "ELIMINAR": "ELIMINACIÓN",
          "ELIMINO": "ELIMINACIÓN",
          "ELIMINACION": "ELIMINACIÓN",
      }
      df_logs["Acción"] = (
          df_logs["Acción"]
          .astype(str)
          .str.upper()
          .map(lambda x: mapeo_acciones.get(x, x))
      )
      return df_logs[LOG_COLUMNS].fillna("-")
    except Exception:
      return pd.DataFrame(columns=LOG_COLUMNS)
  return pd.DataFrame(columns=LOG_COLUMNS)


def registrar_log(
    accion,
    codigo_k,
    material,
    medio,
    alm_dest,
    puesto_dest,
    detalle_cambio,
    usuario,
):
  now = obtener_fecha_hora_arg()
  df_actual = cargar_logs()
  if pd.isna(medio) or str(medio).strip() in ["None", "nan", "N/A", ""]:
    medio = "SIN MEDIO DEFINIDO"

  mapeo_guardado = {
      "CREO": "CREACIÓN",
      "ACTUALIZO": "MODIFICACIÓN",
      "ELIMINO": "ELIMINACIÓN",
  }
  accion_norm = mapeo_guardado.get(accion, accion)

  nuevo_log = pd.DataFrame([{
      "Fecha_Hora": now,
      "Acción": accion_norm,
      "Código_K": str(codigo_k),
      "Material": str(material),
      "Medio": str(medio),
      "Almacén_Destino": str(alm_dest),
      "Puesto_Destino": str(puesto_dest),
      "Detalle_Cambio": str(detalle_cambio),
      "Usuario": str(usuario),
  }])
  df_final = pd.concat([df_actual, nuevo_log], ignore_index=True)
  df_final.to_csv(LOG_FILE, index=False)


def cargar_tracker():
  if os.path.exists(TRACKER_FILE):
    try:
      df_tr = pd.read_csv(TRACKER_FILE, on_bad_lines="skip", dtype=str)
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


def crear_solicitud_tracker(
    material, codigo_k, tipo_kb, puesto_dest, medio, cambio, accion_req, usuario
):
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
      "Usuario_Procesos": str(usuario),
  }])
  df_final = pd.concat([df_tr, nueva_fila], ignore_index=True)
  guardar_tracker(df_final)


def limpiar_historiales_de_prueba():
  df_empty_log = pd.DataFrame(columns=LOG_COLUMNS)
  df_empty_log.to_csv(LOG_FILE, index=False)

  df_empty_tracker = pd.DataFrame(columns=TRACKER_COLUMNS)
  df_empty_tracker.to_csv(TRACKER_FILE, index=False)


def obtener_siguiente_codigo_k(df):
  if df.empty or df["N° Etiquetas"].dropna().empty:
    return "K00000001"

  numeros = [
      int(m.group(0))
      for val in df["N° Etiquetas"].dropna()
      if (m := re.search(r"\d+", str(val)))
  ]
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
rol_actual = st.session_state.get("usuario_rol", "Consulta")

# ==========================================
# CABECERA Y BOTONES DE CONTROL GLOBAL
# ==========================================
st.markdown(
    f"""
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
""",
    unsafe_allow_html=True,
)

_, col_ref, col_logout = st.columns([4, 1.2, 1])

with col_ref:
  if st.button(
      "🔄 Actualizar Datos",
      use_container_width=True,
      help="Refresca los datos en tiempo real sin cerrar sesión",
  ):
    obtener_base_kanbans(forzar=True)
    st.success("⚡ ¡Datos sincronizados!")
    st.rerun()

with col_logout:
  if st.button("Cerrar Sesión", use_container_width=True):
    st.session_state["usuario_email"] = None
    st.session_state["usuario_rol"] = None
    st.session_state.pop("df_kanbans_global", None)
    st.rerun()

df_kanbans = obtener_base_kanbans()
total_k = len(df_kanbans)
internos_k = len(df_kanbans[df_kanbans["Tipo Etiqueta"] == "KI"])
externos_k = len(df_kanbans[df_kanbans["Tipo Etiqueta"] == "KE"])
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
  lista_tabs = [
      "📈 Panel KPIs & Métricas",
      "🚚 Tracker de Ejecución Logística",
      "➕ Crear Nuevo Kanban",
      "✏️ Modificar y Eliminar",
      "📊 Consulta y Exportar Tabla Z (SAP)",
      "📜 Historial Auditoría",
      "👤 Mi Perfil",
  ]
elif rol_actual == "Logistica":
  lista_tabs = [
      "🚚 Tracker de Ejecución Logística",
      "📈 Panel KPIs & Métricas",
      "📊 Consulta y Exportar Tabla Z (SAP)",
      "📜 Historial Auditoría",
      "👤 Mi Perfil",
  ]
else:
  lista_tabs = [
      "📈 Panel KPIs & Métricas",
      "🚚 Estado de Solicitudes",
      "📊 Consulta y Exportar Tabla Z (SAP)",
      "👤 Mi Perfil",
  ]

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

    with st.expander("🔍 Filtros de Análisis", expanded=True):
      f_col1, f_col2, f_col3 = st.columns(3)

      with f_col1:
        if not df_logs_kpi.empty and "Fecha_Hora" in df_logs_kpi.columns:
          df_logs_kpi["Fecha_dt"] = pd.to_datetime(
              df_logs_kpi["Fecha_Hora"], errors="coerce"
          )
          fechas_validas = df_logs_kpi["Fecha_dt"].dropna()
          if not fechas_validas.empty:
            min_d = fechas_validas.min().date()
            max_d = fechas_validas.max().date()
          else:
            min_d = max_d = datetime.now().date()
        else:
          min_d = max_d = datetime.now().date()
        rango_fechas_kpi = st.date_input(
            "Rango de Fechas (Historial):", value=(min_d, max_d), key="kpi_dates"
        )

      with f_col2:
        almacenes_unicos = ["Todos"]
        if not df_k_live.empty and "Almacen Destino" in df_k_live.columns:
          almacenes_unicos += sorted([
              str(x)
              for x in df_k_live["Almacen Destino"].dropna().unique()
              if str(x).strip() != ""
          ])
        f_alm = st.selectbox(
            "Almacén Destino:", almacenes_unicos, key="kpi_alm"
        )

      with f_col3:
        puestos_disp = ["Todos"]
        if (
            not df_k_live.empty
            and "Puesto de trabajo destino" in df_k_live.columns
        ):
          if f_alm != "Todos":
            puestos_disp += sorted([
                str(x)
                for x in df_k_live[df_k_live["Almacen Destino"] == f_alm][
                    "Puesto de trabajo destino"
                ]
                .dropna()
                .unique()
                if str(x).strip() != ""
            ])
          else:
            puestos_disp += sorted([
                str(x)
                for x in df_k_live["Puesto de trabajo destino"]
                .dropna()
                .unique()
                if str(x).strip() != ""
            ])
        f_puesto = st.selectbox(
            "Puesto de Trabajo Destino:", puestos_disp, key="kpi_puesto"
        )

    df_k_filtrado = df_k_live.copy() if not df_k_live.empty else pd.DataFrame()
    if not df_k_filtrado.empty:
      if f_alm != "Todos":
        df_k_filtrado = df_k_filtrado[df_k_filtrado["Almacen Destino"] == f_alm]
      if f_puesto != "Todos":
        df_k_filtrado = df_k_filtrado[
            df_k_filtrado["Puesto de trabajo destino"] == f_puesto
        ]

    df_logs_filtrado = (
        df_logs_kpi.copy() if not df_logs_kpi.empty else pd.DataFrame()
    )
    if (
        not df_logs_filtrado.empty
        and isinstance(rango_fechas_kpi, tuple)
        and len(rango_fechas_kpi) == 2
    ):
      fi, ff = rango_fechas_kpi
      if "Fecha_dt" in df_logs_filtrado.columns:
        df_logs_filtrado = df_logs_filtrado[
            (df_logs_filtrado["Fecha_dt"].dt.date >= fi)
            & (df_logs_filtrado["Fecha_dt"].dt.date <= ff)
        ]
      if f_alm != "Todos" and "Almacén_Destino" in df_logs_filtrado.columns:
        df_logs_filtrado = df_logs_filtrado[
            df_logs_filtrado["Almacén_Destino"] == f_alm
        ]
      if f_puesto != "Todos" and "Puesto_Destino" in df_logs_filtrado.columns:
        df_logs_filtrado = df_logs_filtrado[
            df_logs_filtrado["Puesto_Destino"] == f_puesto
        ]

    df_tr_filtrado = df_tr_kpi.copy() if not df_tr_kpi.empty else pd.DataFrame()
    if (
        not df_tr_filtrado.empty
        and f_puesto != "Todos"
        and "Puesto_Destino" in df_tr_filtrado.columns
    ):
      df_tr_filtrado = df_tr_filtrado[
          df_tr_filtrado["Puesto_Destino"] == f_puesto
      ]

    if not df_tr_filtrado.empty:
      pend_sap = len(df_tr_filtrado[df_tr_filtrado["Cargado_SAP"] != "SI"])
      pend_fisico = len(
          df_tr_filtrado[df_tr_filtrado["Estado_Fisico"] != "Entregado"]
      )
    else:
      pend_sap = 0
      pend_fisico = 0

    c_creados = (
        len(df_logs_filtrado[df_logs_filtrado["Acción"] == "CREACIÓN"])
        if not df_logs_filtrado.empty
        else 0
    )
    c_actualizados = (
        len(df_logs_filtrado[df_logs_filtrado["Acción"] == "MODIFICACIÓN"])
        if not df_logs_filtrado.empty
        else 0
    )
    c_eliminados = (
        len(df_logs_filtrado[df_logs_filtrado["Acción"] == "ELIMINACIÓN"])
        if not df_logs_filtrado.empty
        else 0
    )

    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("KB Activos", len(df_k_filtrado))
    m2.metric("✨ Creados", c_creados)
    m3.metric("✏ Modificados", c_actualizados)
    m4.metric("🗑️ Eliminados", c_eliminados)
    m5.metric(
        "⏳ Pendiente SAP",
        pend_sap,
        delta=f"{pend_sap} pendientes",
        delta_color="inverse",
    )
    m6.metric(
        "🚚 Pend. Físico",
        pend_fisico,
        delta=f"{pend_fisico} pendientes",
        delta_color="inverse",
    )
    st.markdown("---")

    g_col1, g_col2 = st.columns(2)

    with g_col1:
      st.markdown(
          "##### 📍 Kanban por Puestos de Trabajo (Puestos y sus Cambios)"
      )
      if (
          not df_k_filtrado.empty
          and "Puesto de trabajo destino" in df_k_filtrado.columns
      ):
        col_tipo_op = (
            "Tipo_Operacion"
            if "Tipo_Operacion" in df_k_filtrado.columns
            else "Tipo Kanban"
        )
        df_puestos = (
            df_k_filtrado.groupby(["Puesto de trabajo destino", col_tipo_op])
            .size()
            .reset_index(name="Cantidad")
        )
        orden_puestos = (
            df_k_filtrado["Puesto de trabajo destino"]
            .value_counts()
            .index.tolist()
        )

        fig_puestos = px.bar(
            df_puestos,
            x="Puesto de trabajo destino",
            y="Cantidad",
            color=col_tipo_op,
            template="plotly_dark",
            category_orders={"Puesto de trabajo destino": orden_puestos},
            color_discrete_map={
                "ACTUALIZACIÓN": "#f97316",
                "CÓDIGO NUEVO": "#3b82f6",
                "GAVETA": "#ef4444",
                "TARJETA": "#3b82f6",
            },
        )
        fig_puestos.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=80),
            xaxis_title="",
            yaxis_title="Record Count",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )
        st.plotly_chart(fig_puestos, use_container_width=True)
      else:
        st.info(
            "No hay datos de Kanbans para mostrar con los filtros aplicados."
        )

    with g_col2:
      st.markdown("##### 🏷️️ Distribución por Tipo (Gaveta vs Tarjeta)")
      if not df_k_filtrado.empty and "Tipo Kanban" in df_k_filtrado.columns:
        df_tipos = df_k_filtrado["Tipo Kanban"].value_counts().reset_index()
        df_tipos.columns = ["Tipo", "Cantidad"]
        fig_tipos = px.pie(
            df_tipos,
            names="Tipo",
            values="Cantidad",
            hole=0.4,
            template="plotly_dark",
            color="Tipo",
            color_discrete_map={"GAVETA": "#ef4444", "TARJETA": "#3b82f6"},
        )
        fig_tipos.update_traces(textinfo="percent+label+value")
        fig_tipos.update_layout(
            height=350, margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_tipos, use_container_width=True)
      else:
        st.info("No hay datos disponibles para el gráfico de tipos.")

    st.markdown("---")

    g_col3, g_col4 = st.columns(2)

    with g_col3:
      st.markdown("##### 📈 Evolución de Movimientos (Mensual)")
      if not df_logs_filtrado.empty and "Fecha_dt" in df_logs_filtrado.columns:
        df_logs_valid = df_logs_filtrado.dropna(subset=["Fecha_dt"]).copy()
        if not df_logs_valid.empty:
          df_logs_valid["Mes"] = df_logs_valid["Fecha_dt"].dt.strftime("%b %Y")
          df_logs_valid["Mes_Sort"] = df_logs_valid["Fecha_dt"].dt.to_period("M")

          df_evol = (
              df_logs_valid.groupby(["Mes_Sort", "Mes", "Acción"])
              .size()
              .reset_index(name="Cantidad")
          )
          df_evol = df_evol.sort_values("Mes_Sort")

          fig_evol = px.line(
              df_evol,
              x="Mes",
              y="Cantidad",
              color="Acción",
              markers=True,
              template="plotly_dark",
              color_discrete_map={
                  "CREACIÓN": "#22c55e",
                  "MODIFICACIÓN": "#eab308",
                  "ELIMINACIÓN": "#ef4444",
              },
          )
          fig_evol.update_layout(
              height=350,
              margin=dict(l=20, r=20, t=20, b=40),
              xaxis_title="",
              yaxis_title="Operaciones",
          )
          st.plotly_chart(fig_evol, use_container_width=True)
        else:
          st.info(
              "No hay fechas válidas de movimientos en el período"
              " seleccionado."
          )
      else:
        st.info("Sin registros de auditoría para el período.")

    with g_col4:
      st.markdown("##### 👤 Modificaciones por Usuario")
      if not df_logs_filtrado.empty and "Usuario" in df_logs_filtrado.columns:
        df_user_acc = (
            df_logs_filtrado.groupby(["Usuario", "Acción"])
            .size()
            .reset_index(name="Cantidad")
        )
        fig_users = px.bar(
            df_user_acc,
            x="Usuario",
            y="Cantidad",
            color="Acción",
            template="plotly_dark",
            color_discrete_map={
                "CREACIÓN": "#22c55e",
                "MODIFICACIÓN": "#eab308",
                "ELIMINACIÓN": "#ef4444",
            },
        )
        fig_users.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=80),
            xaxis_title="",
            yaxis_title="Acciones",
        )
        st.plotly_chart(fig_users, use_container_width=True)
      else:
        st.info("Sin registros de usuarios para el período.")

# ==========================================
# VISTA: TRACKER DE EJECUCIÓN LOGÍSTICA
# ==========================================
tab_tracker = obtener_tab("🚚 Tracker de Ejecución Logística")
if tab_tracker:
  with tab_tracker:
    st.subheader("🚚 Tracker de Control y Ejecución Logística")
    st.write(
        "Gestiona la carga a SAP, impresión de tarjetas y entrega física de"
        " los Kanbans solicitados."
    )

    df_tracker_live = cargar_tracker()

    if df_tracker_live.empty:
      st.info("💡 No existen solicitudes pendientes en el tracker.")
    else:
      t_col1, t_col2, t_col3 = st.columns(3)
      with t_col1:
        filtro_est_sap = st.selectbox(
            "Estado SAP:",
            ["Todos", "Pendientes (NO)", "Cargados (SI)"],
            key="tr_f_sap",
        )
      with t_col2:
        filtro_est_fisico = st.selectbox(
            "Estado Físico:",
            ["Todos", "Pendiente", "En Proceso", "Entregado"],
            key="tr_f_fisico",
        )
      with t_col3:
        busq_tr = (
            st.text_input("🔍 Buscar por Código K o Material:", key="tr_f_busq")
            .strip()
            .upper()
        )

      df_tr_ver = df_tracker_live.copy()

      if filtro_est_sap == "Pendientes (NO)":
        df_tr_ver = df_tr_ver[df_tr_ver["Cargado_SAP"] != "SI"]
      elif filtro_est_sap == "Cargados (SI)":
        df_tr_ver = df_tr_ver[df_tr_ver["Cargado_SAP"] == "SI"]

      if filtro_est_fisico != "Todos":
        df_tr_ver = df_tr_ver[df_tr_ver["Estado_Fisico"] == filtro_est_fisico]

      if busq_tr:
        df_tr_ver = df_tr_ver[
            df_tr_ver["Código_K"].str.contains(busq_tr, case=False, na=False)
            | df_tr_ver["Material"].str.contains(busq_tr, case=False, na=False)
        ]

      st.markdown(
          f"**Mostrando {len(df_tr_ver)} registros de {len(df_tracker_live)}**"
      )

      for idx, row in df_tr_ver.iterrows():
        id_sol = row["ID_Solicitud"]

        with st.expander(
            f"📌 {id_sol} | KB: {row['Código_K']} | Mat: {row['Material']} |"
            f" Puesto: {row['Puesto_Destino']} | Estado: {row['Estado_Fisico']}"
        ):
          st.markdown('<div class="tracker-card">', unsafe_allow_html=True)
          c1, c2, c3, c4 = st.columns(4)

          c1.write(f"**Fecha Solicitud:** {row['Fecha_Solicitud']}")
          c1.write(f"**Solicitado por:** {row['Usuario_Procesos']}")

          c2.write(f"**Tipo Kanban:** {row['Tipo_KB']}")
          c2.write(f"**Medio / Soporte:** {row['Medio']}")

          c3.write(f"**Operación:** {row['Cambio']}")
          c3.write(f"**Acción Requerida:** {row['Acción_Requerida']}")

          c4.write(
              f"**Impreso:** {row['Impreso']} ({row['Fecha_Impresion']})"
          )
          c4.write(f"**Finalización:** {row['Fecha_Finalizacion']}")
          st.markdown("</div>", unsafe_allow_html=True)

          if rol_actual in ["Procesos", "Logistica"]:
            st.markdown("##### ⚙️ Actualizar Estado de Solicitud")
            with st.form(f"form_tr_{id_sol}"):
              col_f1, col_f2, col_f3 = st.columns(3)

              with col_f1:
                nuevo_sap = st.selectbox(
                    "Cargado en SAP:",
                    ["NO", "SI"],
                    index=0 if row["Cargado_SAP"] != "SI" else 1,
                    key=f"sap_{id_sol}",
                )

              with col_f2:
                nuevo_imp = st.selectbox(
                    "Impreso:",
                    ["NO", "SI"],
                    index=0 if row["Impreso"] != "SI" else 1,
                    key=f"imp_{id_sol}",
                )

              with col_f3:
                opts_fisico = ["Pendiente", "En Proceso", "Entregado"]
                idx_fis = (
                    opts_fisico.index(row["Estado_Fisico"])
                    if row["Estado_Fisico"] in opts_fisico
                    else 0
                )
                nuevo_fisico = st.selectbox(
                    "Estado Físico / Entrega:",
                    opts_fisico,
                    index=idx_fis,
                    key=f"fis_{id_sol}",
                )

              nueva_obs = st.text_input(
                  "Observaciones / Comentarios:",
                  value="" if row["Observación"] == "-" else row["Observación"],
                  key=f"obs_{id_sol}",
              )

              if st.form_submit_button("💾 Guardar Cambios"):
                df_full = cargar_tracker()
                mask = df_full["ID_Solicitud"] == id_sol

                df_full.loc[mask, "Cargado_SAP"] = nuevo_sap
                df_full.loc[mask, "Impreso"] = nuevo_imp
                df_full.loc[mask, "Estado_Fisico"] = nuevo_fisico
                df_full.loc[mask, "Observación"] = (
                    nueva_obs if nueva_obs.strip() != "" else "-"
                )

                if nuevo_imp == "SI" and row["Impreso"] != "SI":
                  df_full.loc[mask, "Fecha_Impresion"] = datetime.now(
                      ARG_TZ
                  ).strftime("%Y-%m-%d")

                if nuevo_fisico == "Entregado" and row["Estado_Fisico"] != "Entregado":
                  df_full.loc[mask, "Fecha_Finalizacion"] = datetime.now(
                      ARG_TZ
                  ).strftime("%Y-%m-%d")

                guardar_tracker(df_full)
                st.success(f"✅ ¡Solicitud {id_sol} actualizada correctamente!")
                st.rerun()

# ==========================================
# VISTA: ESTADO DE SOLICITUDES (CONSULTA)
# ==========================================
tab_estado_sol = obtener_tab("🚚 Estado de Solicitudes")
if tab_estado_sol:
  with tab_estado_sol:
    st.subheader("📋 Estado y Seguimiento de Solicitudes Logísticas")
    st.write(
        "Consulta el estado en tiempo real de las cargas a SAP, impresiones y"
        " entregas de Kanbans."
    )

    df_tracker_view = cargar_tracker()

    if df_tracker_view.empty:
      st.info("No hay solicitudes registradas actualmente.")
    else:
      c_busq, c_est = st.columns([2, 1])
      with c_busq:
        q_sol = (
            st.text_input(
                "🔍 Buscar por Material o Código K:", key="q_sol_user"
            )
            .strip()
            .upper()
        )
      with c_est:
        f_est = st.selectbox(
            "Filtrar Estado Físico:",
            ["Todos", "Pendiente", "En Proceso", "Entregado"],
            key="f_est_user",
        )

      df_filtrado_sol = df_tracker_view.copy()
      if q_sol:
        df_filtrado_sol = df_filtrado_sol[
            df_filtrado_sol["Material"].str.contains(
                q_sol, case=False, na=False
            )
            | df_filtrado_sol["Código_K"].str.contains(
                q_sol, case=False, na=False
            )
        ]
      if f_est != "Todos":
        df_filtrado_sol = df_filtrado_sol[
            df_filtrado_sol["Estado_Fisico"] == f_est
        ]

      st.dataframe(df_filtrado_sol, use_container_width=True, hide_index=True)

# ==========================================
# VISTA: CREAR NUEVO KANBAN (TAB_CREAR)
# ==========================================
tab_crear = obtener_tab("➕ Crear Nuevo Kanban")
if tab_crear:
  with tab_crear:
    st.subheader("➕ Alta y Registro de Nuevo Kanban")

    df_live_c = obtener_base_kanbans()
    proximo_k_def = obtener_siguiente_codigo_k(df_live_c)

    # --- REQUERIMIENTO 1: Lote packaging dinámico fuera del form con Regex ---
    material_in_raw = normalizar_codigo_sap(
        st.text_input(
            "Material / Código SAP:",
            placeholder="Ej: CM000016",
            key="c_mat_input",
        )
    )

    info_pkg = dict_pkg.get(material_in_raw, {})
    lote_min_pkg = info_pkg.get("cantidad")
    medio_pkg_sug = info_pkg.get("medio", "")
    unid_pkg_sug = info_pkg.get("unidad", "UN")

    if lote_min_pkg is not None:
      st.info(
          "ℹ️ **Material encontrado en Lote Packaging:** Lote base ="
          f" **{lote_min_pkg}**. La cantidad de reposición debe ser múltiplo de"
          f" **{lote_min_pkg}**."
      )
    elif material_in_raw != "":
      st.caption(
          "⚠️ Material no registrado en la planilla 'Lote packaging'. Se asume"
          " valor mínimo predeterminado 1.0."
      )

    # --- REQUERIMIENTOS 2 y 3: Lógica condicional de Almacén Origen vs Tipo Etiqueta ---
    c_reglas1, c_reglas2 = st.columns(2)
    with c_reglas1:
      # Requerimiento 2: 'L010' por defecto
      idx_alm_def = (
          LISTA_ALMACENES.index("L010") if "L010" in LISTA_ALMACENES else 0
      )
      alm_origen_in = st.selectbox(
          "Almacén Origen:",
          LISTA_ALMACENES,
          index=idx_alm_def,
          key="c_alm_o_input",
      )

    with c_reglas2:
      # Requerimiento 3: Si Almacén Origen == 'L010', la ÚNICA opción debe ser 'KE'
      if alm_origen_in == "L010":
        opts_tipo_etq_crear = ["KE"]
        st.caption("🔒 Almacén Origen es L010: Tipo de Etiqueta forzado a KE.")
      else:
        opts_tipo_etq_crear = ["KE", "KI"]

      tipo_etiqueta_in = st.selectbox(
          "Tipo Etiqueta:", opts_tipo_etq_crear, index=0, key="c_tipo_etq_input"
      )

    # Requerimiento 3 (inverso): Si el usuario seleccionó KI, Almacén Origen NUNCA puede ser 'L010'
    if tipo_etiqueta_in == "KI" and alm_origen_in == "L010":
      st.error(
          "❌ Conflicto: Si Tipo Etiqueta es 'KI', Almacén Origen no puede ser"
          " 'L010'. Seleccione un Almacén Origen diferente."
      )

    with st.form("form_crear_kanban", clear_on_submit=False):
      c_sec1, c_sec2 = st.columns(2)

      with c_sec1:
        st.markdown("##### 📍 Identificación y Material")

        codigo_k_in = (
            st.text_input(
                "N° Etiquetas / Código K:",
                value=proximo_k_def,
                help=(
                    "Autogenerado con el próximo código libre en la secuencia K"
                ),
            )
            .strip()
            .upper()
        )
        st.text_input(
            "Material Confirmado:", value=material_in_raw, disabled=True
        )
        st.text_input(
            "Tipo Etiqueta Confirmado:", value=tipo_etiqueta_in, disabled=True
        )

        tipo_kanban_in = st.selectbox("Tipo Kanban:", ["TARJETA", "GAVETA"])

        if tipo_kanban_in == "TARJETA":
          idx_m = (
              OPCIONES_SOPORTE_TARJETA.index(medio_pkg_sug)
              if medio_pkg_sug in OPCIONES_SOPORTE_TARJETA
              else 0
          )
          medio_in = st.selectbox(
              "Medio / Soporte Tarjeta:",
              OPCIONES_SOPORTE_TARJETA,
              index=idx_m,
          )
        else:
          gaveta_sel = st.selectbox("Tamaño Gaveta:", OPCIONES_GAVETA)
          medio_in = f"GAVETA {gaveta_sel}"

        # Requerimiento 2: Centro 'A110' por defecto
        centro_in = st.text_input("Centro:", value="A110").strip().upper()

      with c_sec2:
        st.markdown("##### 🏭 Ubicación y Cantidades")

        puestos_origen_disp = ALMACENES_PUESTOS.get(alm_origen_in, [])
        puesto_origen_in = st.selectbox(
            "Puesto Trabajo Origen:",
            puestos_origen_disp if puestos_origen_disp else ["N/A"],
        )

        alm_destino_in = st.selectbox(
            "Almacén Destino:",
            LISTA_ALMACENES,
            index=min(1, len(LISTA_ALMACENES) - 1),
        )
        puestos_dest_disp = ALMACENES_PUESTOS.get(alm_destino_in, [])
        puesto_destino_in = st.selectbox(
            "Puesto Trabajo Destino:",
            puestos_dest_disp if puestos_dest_disp else ["N/A"],
        )

        # Requerimiento 1: Lote packaging como valor mínimo posible
        val_min_repo = (
            float(lote_min_pkg)
            if (lote_min_pkg is not None and lote_min_pkg > 0)
            else 1.0
        )

        c_q1, c_q2 = st.columns(2)
        with c_q1:
          cant_repo_in = st.number_input(
              "Cantidad Reposición:",
              min_value=val_min_repo,
              value=val_min_repo,
              step=val_min_repo,
          )
          cant_pp_in = st.number_input(
              "Cantidad Punto Pedido:",
              min_value=1.0,
              value=val_min_repo,
              step=1.0,
          )
        with c_q2:
          idx_u = (
              OPCIONES_UNIDAD_MEDIDA.index(unid_pkg_sug)
              if unid_pkg_sug in OPCIONES_UNIDAD_MEDIDA
              else 0
          )
          unidad_repo_in = st.selectbox(
              "Unidad Reposición:", OPCIONES_UNIDAD_MEDIDA, index=idx_u
          )
          tiempo_prep_in = st.number_input(
              "Tiempo Prep. (Días):", min_value=1, value=1, step=1
          )

      st.markdown("---")
      btn_crear = st.form_submit_button(
          "🚀 Registrar Kanban", type="primary", use_container_width=True
      )

    if btn_crear:
      if not material_in_raw or not codigo_k_in:
        st.error("❌ Los campos 'Material' y 'N° Etiquetas' son obligatorios.")
      elif tipo_etiqueta_in == "KI" and alm_origen_in == "L010":
        st.error(
            "❌ Imposible guardar: Con Tipo Etiqueta 'KI' el Almacén Origen NO"
            " puede ser 'L010'."
        )
      elif alm_origen_in == "L010" and tipo_etiqueta_in != "KE":
        st.error(
            "❌ Imposible guardar: Cuando el Almacén Origen es 'L010', el Tipo"
            " Etiqueta debe ser únicamente 'KE'."
        )
      elif lote_min_pkg is not None and (cant_repo_in % lote_min_pkg != 0):
        st.error(
            f"❌ La Cantidad de Reposición ({cant_repo_in}) debe ser múltiplo"
            f" exacto del Lote Packaging ({lote_min_pkg})."
        )
      else:
        df_verif = obtener_base_kanbans()
        if codigo_k_in in df_verif["N° Etiquetas"].values:
          st.error(
              f"❌ El código {codigo_k_in} ya existe en la base. Utilice un"
              " código diferente."
          )
        else:
          fecha_actual = obtener_fecha_hora_arg()
          usr_actual = st.session_state["usuario_email"]

          nueva_fila = pd.DataFrame([{
              "N° Etiquetas": codigo_k_in,
              "Tipo Etiqueta": tipo_etiqueta_in,
              "Tipo Kanban": tipo_kanban_in,
              "Medio": medio_in,
              "Material": material_in_raw,
              "Centro": centro_in,
              "Almacén Origen": alm_origen_in,
              "Almacen Destino": alm_destino_in,
              "Puesto trabajo Origen": puesto_origen_in,
              "Puesto de trabajo destino": puesto_destino_in,
              "Cantidad Reposicion": str(cant_repo_in),
              "Unidad Reposicion": unidad_repo_in,
              "Cantidad Punto de Pedido": str(cant_pp_in),
              "Tiempo preparación abast. (en días)": str(tiempo_prep_in),
              "Fecha Modificación": fecha_actual,
              "Usuario Modificación": usr_actual,
          }])

          df_nuevo = pd.concat([df_verif, nueva_fila], ignore_index=True)
          actualizar_base_kanbans(df_nuevo)

          detalle_log = (
              f"Alta de Kanban {codigo_k_in} para Material {material_in_raw} en"
              f" Puesto {puesto_destino_in}"
          )
          registrar_log(
              "CREACIÓN",
              codigo_k_in,
              material_in_raw,
              medio_in,
              alm_destino_in,
              puesto_destino_in,
              detalle_log,
              usr_actual,
          )

          crear_solicitud_tracker(
              material=material_in_raw,
              codigo_k=codigo_k_in,
              tipo_kb=tipo_kanban_in,
              puesto_dest=puesto_destino_in,
              medio=medio_in,
              cambio="ALTA DE KANBAN",
              accion_req="IMPRIMIR Y ENTREGAR TARJETA",
              usuario=usr_actual,
          )

          st.success(
              f"✅ ¡Kanban {codigo_k_in} registrado exitosamente y solicitud"
              " enviada al Tracker Logístico!"
          )
          st.rerun()

# ==========================================
# VISTA: MODIFICAR Y ELIMINAR
# ==========================================
tab_mod_elim = obtener_tab("✏️ Modificar y Eliminar")
if tab_mod_elim:
  with tab_mod_elim:
    st.subheader("✏️ Modificación y Eliminación de Kanbans")

    df_mod = obtener_base_kanbans()

    if df_mod.empty:
      st.info("No hay Kanbans registrados en el sistema.")
    else:
      col_search1, col_search2 = st.columns(2)
      with col_search1:
        search_term = (
            st.text_input(
                "🔍 Buscar por Código K o Material:", key="mod_search"
            )
            .strip()
            .upper()
        )

      df_filtered_mod = df_mod.copy()
      if search_term:
        df_filtered_mod = df_filtered_mod[
            df_filtered_mod["N° Etiquetas"].str.contains(
                search_term, case=False, na=False
            )
            | df_filtered_mod["Material"].str.contains(
                search_term, case=False, na=False
            )
        ]

      lista_k_mod = (
          df_filtered_mod["N° Etiquetas"].unique().tolist()
          if not df_filtered_mod.empty
          else []
      )

      if not lista_k_mod:
        st.warning("⚠️ No se encontraron coincidencias para la búsqueda.")
      else:
        k_seleccionado = st.selectbox(
            "Seleccionar Código K a Modificar / Eliminar:", sorted(lista_k_mod)
        )
        row_sel = df_mod[df_mod["N° Etiquetas"] == k_seleccionado].iloc[0]

        subtab_mod, subtab_elim = st.tabs(
            ["✏️ Modificar Registro", "🗑️ Eliminar Registro"]
        )

        with subtab_mod:
          # --- REQUERIMIENTO 1 EN MODIFICACIÓN: Normalización de Regex y Lote Packaging ---
          mod_material_init = (
              str(row_sel["Material"]) if pd.notna(row_sel["Material"]) else ""
          )
          mod_material = normalizar_codigo_sap(
              st.text_input(
                  "Material:",
                  value=mod_material_init,
                  key=f"mod_mat_{k_seleccionado}",
              )
          )

          info_pkg_mod = dict_pkg.get(mod_material, {})
          lote_min_mod = info_pkg_mod.get("cantidad")

          if lote_min_mod is not None:
            st.info(
                "ℹ️ **Material en Lote Packaging:** Lote base ="
                f" **{lote_min_mod}**. La cantidad de reposición debe ser"
                f" múltiplo de **{lote_min_mod}**."
            )

          # --- REQUERIMIENTO 3 EN MODIFICACIÓN: Mismas limitaciones cruzadas Almacén Origen vs Tipo Etiqueta ---
          c_m_reg1, c_m_reg2 = st.columns(2)

          alm_orig_val = (
              str(row_sel["Almacén Origen"])
              if pd.notna(row_sel["Almacén Origen"])
              else LISTA_ALMACENES[0]
          )
          idx_alm_o = (
              LISTA_ALMACENES.index(alm_orig_val)
              if alm_orig_val in LISTA_ALMACENES
              else 0
          )

          with c_m_reg1:
            mod_alm_orig = st.selectbox(
                "Almacén Origen:",
                LISTA_ALMACENES,
                index=idx_alm_o,
                key=f"m_alm_o_{k_seleccionado}",
            )

          with c_m_reg2:
            if mod_alm_orig == "L010":
              opts_tipo_etq_mod = ["KE"]
              st.caption(
                  "🔒 Almacén Origen es L010: Tipo de Etiqueta forzado a KE."
              )
            else:
              opts_tipo_etq_mod = ["KI", "KE"]

            etq_init = (
                row_sel["Tipo Etiqueta"]
                if row_sel["Tipo Etiqueta"] in opts_tipo_etq_mod
                else opts_tipo_etq_mod[0]
            )
            idx_etq = opts_tipo_etq_mod.index(etq_init)
            mod_tipo_etq = st.selectbox(
                "Tipo Etiqueta:",
                opts_tipo_etq_mod,
                index=idx_etq,
                key=f"m_etq_{k_seleccionado}",
            )

          if mod_tipo_etq == "KI" and mod_alm_orig == "L010":
            st.error(
                "❌ Conflicto: Si Tipo Etiqueta es 'KI', Almacén Origen no"
                " puede ser 'L010'."
            )

          with st.form(f"form_mod_{k_seleccionado}"):
            m_col1, m_col2 = st.columns(2)

            with m_col1:
              st.markdown("##### 📍 Datos de Identificación")
              st.text_input(
                  "Material Confirmado:", value=mod_material, disabled=True
              )
              st.text_input(
                  "Almacén Origen Confirmado:",
                  value=mod_alm_orig,
                  disabled=True,
              )
              st.text_input(
                  "Tipo Etiqueta Confirmado:",
                  value=mod_tipo_etq,
                  disabled=True,
              )

              opts_tipo_kb = ["TARJETA", "GAVETA"]
              idx_kb = (
                  opts_tipo_kb.index(row_sel["Tipo Kanban"])
                  if row_sel["Tipo Kanban"] in opts_tipo_kb
                  else 0
              )
              mod_tipo_kb = st.selectbox(
                  "Tipo Kanban:", opts_tipo_kb, index=idx_kb
              )

              mod_medio = (
                  st.text_input(
                      "Medio / Soporte:",
                      value=(
                          str(row_sel["Medio"])
                          if pd.notna(row_sel["Medio"])
                          else ""
                      ),
                  )
                  .strip()
                  .upper()
              )
              mod_centro = (
                  st.text_input(
                      "Centro:",
                      value=(
                          str(row_sel["Centro"])
                          if pd.notna(row_sel["Centro"])
                          else "A110"
                      ),
                  )
                  .strip()
                  .upper()
              )

            with m_col2:
              st.markdown("##### 🏭 Ubicación y Cantidades")

              puestos_o_disp = ALMACENES_PUESTOS.get(mod_alm_orig, [])
              puesto_orig_val = (
                  str(row_sel["Puesto trabajo Origen"])
                  if pd.notna(row_sel["Puesto trabajo Origen"])
                  else ""
              )
              idx_p_o = (
                  puestos_o_disp.index(puesto_orig_val)
                  if puesto_orig_val in puestos_o_disp
                  else 0
              )
              mod_puesto_orig = st.selectbox(
                  "Puesto Trabajo Origen:",
                  puestos_o_disp if puestos_o_disp else ["N/A"],
                  index=idx_p_o if puestos_o_disp else 0,
                  key=f"m_p_o_{k_seleccionado}",
              )

              alm_dest_val = (
                  str(row_sel["Almacen Destino"])
                  if pd.notna(row_sel["Almacen Destino"])
                  else LISTA_ALMACENES[0]
              )
              idx_alm_d = (
                  LISTA_ALMACENES.index(alm_dest_val)
                  if alm_dest_val in LISTA_ALMACENES
                  else 0
              )
              mod_alm_dest = st.selectbox(
                  "Almacén Destino:",
                  LISTA_ALMACENES,
                  index=idx_alm_d,
                  key=f"m_alm_d_{k_seleccionado}",
              )

              puestos_d_disp = ALMACENES_PUESTOS.get(mod_alm_dest, [])
              puesto_dest_val = (
                  str(row_sel["Puesto de trabajo destino"])
                  if pd.notna(row_sel["Puesto de trabajo destino"])
                  else ""
              )
              idx_p_d = (
                  puestos_d_disp.index(puesto_dest_val)
                  if puesto_dest_val in puestos_d_disp
                  else 0
              )
              mod_puesto_dest = st.selectbox(
                  "Puesto Trabajo Destino:",
                  puestos_d_disp if puestos_d_disp else ["N/A"],
                  index=idx_p_d if puestos_d_disp else 0,
                  key=f"m_p_d_{k_seleccionado}",
              )

              val_min_mod = (
                  float(lote_min_mod)
                  if (lote_min_mod is not None and lote_min_mod > 0)
                  else 1.0
              )

              try:
                c_repo_val = (
                    float(row_sel["Cantidad Reposicion"])
                    if pd.notna(row_sel["Cantidad Reposicion"])
                    else val_min_mod
                )
              except (ValueError, TypeError):
                c_repo_val = val_min_mod

              if c_repo_val < val_min_mod:
                c_repo_val = val_min_mod

              try:
                c_pp_val = (
                    float(row_sel["Cantidad Punto de Pedido"])
                    if pd.notna(row_sel["Cantidad Punto de Pedido"])
                    else 1.0
                )
              except (ValueError, TypeError):
                c_pp_val = 1.0

              m_q1, m_q2 = st.columns(2)
              with m_q1:
                mod_cant_repo = st.number_input(
                    "Cantidad Reposición:",
                    min_value=val_min_mod,
                    value=c_repo_val,
                    step=val_min_mod,
                )
                mod_cant_pp = st.number_input(
                    "Cantidad Punto Pedido:",
                    min_value=1.0,
                    value=c_pp_val,
                    step=1.0,
                )
              with m_q2:
                u_med_val = (
                    str(row_sel["Unidad Reposicion"])
                    if pd.notna(row_sel["Unidad Reposicion"])
                    else "UN"
                )
                idx_u = (
                    OPCIONES_UNIDAD_MEDIDA.index(u_med_val)
                    if u_med_val in OPCIONES_UNIDAD_MEDIDA
                    else 0
                )
                mod_unid = st.selectbox(
                    "Unidad Reposición:", OPCIONES_UNIDAD_MEDIDA, index=idx_u
                )

                try:
                  t_prep_val = (
                      int(row_sel["Tiempo preparación abast. (en días)"])
                      if pd.notna(row_sel["Tiempo preparación abast. (en días)"])
                      else 1
                  )
                except (ValueError, TypeError):
                  t_prep_val = 1
                mod_t_prep = st.number_input(
                    "Tiempo Prep. (Días):", min_value=1, value=t_prep_val, step=1
                )

            st.markdown("---")
            btn_guardar_mod = st.form_submit_button(
                "💾 Guardar Modificaciones",
                type="primary",
                use_container_width=True,
            )

          if btn_guardar_mod:
            if mod_tipo_etq == "KI" and mod_alm_orig == "L010":
              st.error(
                  "❌ Conflicto: Si Tipo Etiqueta es 'KI', Almacén Origen no"
                  " puede ser 'L010'."
              )
            elif mod_alm_orig == "L010" and mod_tipo_etq != "KE":
              st.error(
                  "❌ Conflicto: Si Almacén Origen es 'L010', Tipo Etiqueta debe"
                  " ser 'KE'."
              )
            elif lote_min_mod is not None and (mod_cant_repo % lote_min_mod != 0):
              st.error(
                  f"❌ La Cantidad de Reposición ({mod_cant_repo}) debe ser"
                  f" múltiplo exacto del Lote Packaging ({lote_min_mod})."
              )
            else:
              fecha_mod = obtener_fecha_hora_arg()
              usr_mod = st.session_state["usuario_email"]

              df_all = obtener_base_kanbans()
              mask_sel = df_all["N° Etiquetas"] == k_seleccionado

              df_all.loc[mask_sel, "Material"] = mod_material
              df_all.loc[mask_sel, "Tipo Etiqueta"] = mod_tipo_etq
              df_all.loc[mask_sel, "Tipo Kanban"] = mod_tipo_kb
              df_all.loc[mask_sel, "Medio"] = mod_medio
              df_all.loc[mask_sel, "Centro"] = mod_centro
              df_all.loc[mask_sel, "Almacén Origen"] = mod_alm_orig
              df_all.loc[mask_sel, "Puesto trabajo Origen"] = mod_puesto_orig
              df_all.loc[mask_sel, "Almacen Destino"] = mod_alm_dest
              df_all.loc[mask_sel, "Puesto de trabajo destino"] = (
                  mod_puesto_dest
              )
              df_all.loc[mask_sel, "Cantidad Reposicion"] = str(mod_cant_repo)
              df_all.loc[mask_sel, "Unidad Reposicion"] = mod_unid
              df_all.loc[mask_sel, "Cantidad Punto de Pedido"] = str(mod_cant_pp)
              df_all.loc[mask_sel, "Tiempo preparación abast. (en días)"] = (
                  str(mod_t_prep)
              )
              df_all.loc[mask_sel, "Fecha Modificación"] = fecha_mod
              df_all.loc[mask_sel, "Usuario Modificación"] = usr_mod

              actualizar_base_kanbans(df_all)

              det_cambio = (
                  f"Modificación de datos del Kanban {k_seleccionado} (Material"
                  f" {mod_material})"
              )
              registrar_log(
                  "MODIFICACIÓN",
                  k_seleccionado,
                  mod_material,
                  mod_medio,
                  mod_alm_dest,
                  mod_puesto_dest,
                  det_cambio,
                  usr_mod,
              )

              crear_solicitud_tracker(
                  material=mod_material,
                  codigo_k=k_seleccionado,
                  tipo_kb=mod_tipo_kb,
                  puesto_dest=mod_puesto_dest,
                  medio=mod_medio,
                  cambio="MODIFICACIÓN DE DATOS",
                  accion_req="REIMPRIMIR / REVISAR TARJETA",
                  usuario=usr_mod,
              )

              st.success(
                  f"✅ ¡Kanban {k_seleccionado} modificado con éxito!"
              )
              st.rerun()

        with subtab_elim:
          st.warning(
              f"⚠️ ¿Está seguro que desea eliminar el Kanban **{k_seleccionado}**"
              f" (Material: {row_sel['Material']})?"
          )

          with st.form(f"form_elim_{k_seleccionado}"):
            motivo_elim = st.text_input(
                "Motivo de la eliminación:",
                placeholder="Ej: Obsoleto, Duplicado, Baja de Puesto",
            ).strip()
            btn_confirm_elim = st.form_submit_button(
                "🚨 Confirmar Eliminación", type="primary"
            )

          if btn_confirm_elim:
            if not motivo_elim:
              st.error(
                  "❌ Debe ingresar un motivo para proceder con la eliminación."
              )
            else:
              usr_elim = st.session_state["usuario_email"]
              mat_elim = str(row_sel["Material"])
              med_elim = str(row_sel["Medio"])
              alm_d_elim = str(row_sel["Almacen Destino"])
              pst_d_elim = str(row_sel["Puesto de trabajo destino"])
              tkb_elim = str(row_sel["Tipo Kanban"])

              df_all = obtener_base_kanbans()
              df_nuevo_elim = df_all[
                  df_all["N° Etiquetas"] != k_seleccionado
              ].copy()
              actualizar_base_kanbans(df_nuevo_elim)

              det_elim = (
                  f"Eliminación de Kanban {k_seleccionado}. Motivo:"
                  f" {motivo_elim}"
              )
              registrar_log(
                  "ELIMINACIÓN",
                  k_seleccionado,
                  mat_elim,
                  med_elim,
                  alm_d_elim,
                  pst_d_elim,
                  det_elim,
                  usr_elim,
              )

              crear_solicitud_tracker(
                  material=mat_elim,
                  codigo_k=k_seleccionado,
                  tipo_kb=tkb_elim,
                  puesto_dest=pst_d_elim,
                  medio=med_elim,
                  cambio="BAJA DE KANBAN",
                  accion_req="RETIRAR TARJETA DE PLANTA",
                  usuario=usr_elim,
              )

              st.success(
                  f"✅ ¡Kanban {k_seleccionado} eliminado correctamente!"
              )
              st.rerun()

# ==========================================
# VISTA: CONSULTA Y EXPORTAR TABLA Z (SAP)
# ==========================================
tab_consulta = obtener_tab("📊 Consulta y Exportar Tabla Z (SAP)")
if tab_consulta:
  with tab_consulta:
    st.subheader("📊 Consulta General y Exportación - Tabla Z (SAP)")

    df_z = obtener_base_kanbans()

    if df_z.empty:
      st.info("La Tabla Z se encuentra vacía.")
    else:
      c_f1, c_f2, c_f3 = st.columns(3)
      with c_f1:
        f_z_alm = st.selectbox(
            "Filtrar por Almacén Destino:",
            ["Todos"]
            + sorted([
                str(x)
                for x in df_z["Almacen Destino"].dropna().unique()
                if str(x).strip() != ""
            ]),
            key="z_alm",
        )
      with c_f2:
        f_z_puesto = st.selectbox(
            "Filtrar por Puesto Destino:",
            ["Todos"]
            + sorted([
                str(x)
                for x in df_z["Puesto de trabajo destino"].dropna().unique()
                if str(x).strip() != ""
            ]),
            key="z_puesto",
        )
      with c_f3:
        q_z = (
            st.text_input(
                "🔍 Búsqueda rápida (Material / Código K):", key="z_busq"
            )
            .strip()
            .upper()
        )

      df_z_disp = df_z.copy()
      if f_z_alm != "Todos":
        df_z_disp = df_z_disp[df_z_disp["Almacen Destino"] == f_z_alm]
      if f_z_puesto != "Todos":
        df_z_disp = df_z_disp[
            df_z_disp["Puesto de trabajo destino"] == f_z_puesto
        ]
      if q_z:
        df_z_disp = df_z_disp[
            df_z_disp["Material"].str.contains(q_z, case=False, na=False)
            | df_z_disp["N° Etiquetas"].str.contains(q_z, case=False, na=False)
        ]

      st.markdown(f"**Registros mostrados: {len(df_z_disp)} de {len(df_z)}**")
      st.dataframe(df_z_disp, use_container_width=True, hide_index=True)

      st.markdown("---")
      st.subheader("📥 Exportación de Archivos")

      exp_col1, exp_col2 = st.columns(2)

      with exp_col1:
        output_excel = io.BytesIO()
        with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
          df_z_disp.to_excel(writer, sheet_name="Tabla Z", index=False)
        output_excel.seek(0)

        st.download_button(
            label="📊 Exportar Vista Filtrada a Excel (.xlsx)",
            data=output_excel,
            file_name="Tabla_Z_Filtrada.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

      with exp_col2:
        csv_bytes = df_z_disp.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Exportar Vista Filtrada a CSV (.csv)",
            data=csv_bytes,
            file_name="Tabla_Z_Filtrada.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ==========================================
# VISTA: HISTORIAL AUDITORÍA
# ==========================================
tab_historial = obtener_tab("📜 Historial Auditoría")
if tab_historial:
  with tab_historial:
    st.subheader("📜 Historial de Cambios y Auditoría del Sistema")

    df_log_aud = cargar_logs()

    if df_log_aud.empty:
      st.info("No existen registros de auditoría almacenados.")
    else:
      h_c1, h_c2, h_c3 = st.columns(3)
      with h_c1:
        f_acc = st.selectbox(
            "Filtrar Acción:",
            ["Todas", "CREACIÓN", "MODIFICACIÓN", "ELIMINACIÓN"],
            key="h_acc",
        )
      with h_c2:
        f_usr = st.selectbox(
            "Filtrar Usuario:",
            ["Todos"]
            + sorted([
                str(x)
                for x in df_log_aud["Usuario"].dropna().unique()
                if str(x).strip() != ""
            ]),
            key="h_usr",
        )
      with h_c3:
        q_hist = (
            st.text_input("🔍 Buscar por Código K o Material:", key="h_busq")
            .strip()
            .upper()
        )

      df_hist_disp = df_log_aud.copy()
      if f_acc != "Todas":
        df_hist_disp = df_hist_disp[df_hist_disp["Acción"] == f_acc]
      if f_usr != "Todos":
        df_hist_disp = df_hist_disp[df_hist_disp["Usuario"] == f_usr]
      if q_hist:
        df_hist_disp = df_hist_disp[
            df_hist_disp["Código_K"].str.contains(q_hist, case=False, na=False)
            | df_hist_disp["Material"].str.contains(q_hist, case=False, na=False)
        ]

      st.dataframe(
          df_hist_disp.iloc[::-1], use_container_width=True, hide_index=True
      )

# ==========================================
# VISTA: MI PERFIL Y HERRAMIENTAS
# ==========================================
tab_perfil = obtener_tab("👤 Mi Perfil")
if tab_perfil:
  with tab_perfil:
    st.subheader("👤 Configuración de Usuario y Herramientas")

    user_actual = st.session_state["usuario_email"]
    rol_actual_val = st.session_state["usuario_rol"]

    st.write(f"**Usuario:** {user_actual}")
    st.write(f"**Rol Asignado:** {rol_actual_val}")

    st.markdown("---")
    st.subheader("🔒 Cambiar Contraseña")
    with st.form("form_change_pass"):
      pass_curr = st.text_input("Contraseña Actual:", type="password")
      pass_new1 = st.text_input("Nueva Contraseña:", type="password")
      pass_new2 = st.text_input("Confirmar Nueva Contraseña:", type="password")

      if st.form_submit_button("Actualizar Contraseña"):
        if (
            user_actual in USUARIOS_REGISTRADOS
            and USUARIOS_REGISTRADOS[user_actual]["pass"] == pass_curr
        ):
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
      st.subheader("⚙ Administración de Usuarios (Solo Procesos)")

      st.markdown("##### 👥 Gestionar Rol de Usuario")
      lista_usuarios = sorted(list(USUARIOS_REGISTRADOS.keys()))
      if lista_usuarios:
        usr_sel = st.selectbox(
            "Seleccione Usuario a modificar:",
            lista_usuarios,
            key="adm_usr_sel",
        )
        rol_actual_target = USUARIOS_REGISTRADOS[usr_sel].get("rol", "Consulta")

        opciones_roles = ["Procesos", "Logistica", "Consulta"]
        idx_rol_def = (
            opciones_roles.index(rol_actual_target)
            if rol_actual_target in opciones_roles
            else 2
        )

        nuevo_rol_sel = st.selectbox(
            "Asignar Nuevo Rol:",
            opciones_roles,
            index=idx_rol_def,
            key="adm_rol_sel",
        )

        if st.button("💾 Actualizar Rol de Usuario", type="primary"):
          USUARIOS_REGISTRADOS[usr_sel]["rol"] = nuevo_rol_sel
          guardar_usuarios(USUARIOS_REGISTRADOS)

          if usr_sel == user_actual:
            st.session_state["usuario_rol"] = nuevo_rol_sel

          st.success(
              f"✅ ¡Rol de {usr_sel} actualizado correctamente a"
              f" '{nuevo_rol_sel}'!"
          )
          st.rerun()

      st.markdown("<br>", unsafe_allow_html=True)

      st.markdown("##### 📥 Exportar Base de Usuarios")
      json_data = json.dumps(
          USUARIOS_REGISTRADOS, indent=4, ensure_ascii=False
      )
      st.download_button(
          label="📥 Exportar usuarios.json",
          data=json_data,
          file_name="usuarios.json",
          mime="application/json",
          type="secondary",
      )

      st.markdown("---")
      st.subheader("🧹 Mantenimiento de Sistema (Solo Procesos)")
      with st.expander("⚠ Zona de Limpieza de Historiales"):
        st.write(
            "Esta acción borrará el historial de auditoría y los registros del"
            " tracker de ejecución. **No afectará a la base de Kanbans activos"
            " (Tabla Z).**"
        )
        if st.button("🚨 Resetear Historiales y Tracker de Prueba"):
          limpiar_historiales_de_prueba()
          st.success("✅ Historiales y Tracker reseteados correctamente.")
          st.rerun()
