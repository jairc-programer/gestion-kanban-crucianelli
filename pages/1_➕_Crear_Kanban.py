import streamlit as st
import pandas as pd
import re, os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    ARG_TZ = ZoneInfo('America/Argentina/Buenos_Aires')
except ImportError:
    import pytz
    ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def obtener_fecha_hora_actual():
    return datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")

def registrar_auditoria(fecha_hora, usuario, accion, codigo_k, material, detalle):
    auditoria_file = "historial_auditoria.csv"
    nuevo_registro = {
        "Fecha y Hora": fecha_hora,
        "Usuario": usuario,
        "Acción": accion,
        "Código K": codigo_k,
        "Material": material,
        "Detalle de Cambios": detalle
    }
    if os.path.exists(auditoria_file):
        df = pd.read_csv(auditoria_file)
        df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
    else:
        df = pd.DataFrame([nuevo_registro])
    df.to_csv(auditoria_file, index=False)

def registrar_tracker_logistica(fecha_hora, usuario, tipo_accion, codigo_k, material, origen, destino, detalle):
    tracker_file = "tracker_ejecucion.csv"
    nuevo_registro = {
        "Fecha Solicitud": fecha_hora,
        "Usuario Solicitante": usuario,
        "Tipo de Acción": tipo_accion,
        "Código K": codigo_k,
        "Material": material,
        "Almacén Origen": origen,
        "Puesto Destino": destino,
        "Detalle": detalle,
        "Estado Logístico": "PENDIENTE",
        "Estado SAP": "PENDIENTE",
        "Fecha SAP": "-",
        "Usuario SAP": "-",
        "Estado Impresion": "PENDIENTE",
        "Fecha Impresion": "-",
        "Usuario Impresion": "-",
        "Estado Puesto": "PENDIENTE",
        "Fecha Puesto": "-",
        "Usuario Puesto": "-",
        "Fecha Ejecución Logística": "-",
        "Usuario Logística": "-"
    }
    if os.path.exists(tracker_file):
        df = pd.read_csv(tracker_file)
        df = pd.concat([df, pd.DataFrame([nuevo_registro])], ignore_index=True)
    else:
        df = pd.DataFrame([nuevo_registro])
    df.to_csv(tracker_file, index=False)

from utils.style import aplicar_estilo_enterprise

# Aplicar estilo visual Enterprise
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

DB_FILE, PKG_FILE = "TablaZ.xlsx", "Lote packaging.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

ALMACENES_PUESTOS = {
    "P110": ["ARM_HORQ", "ARM_MAZ1", "CORTE_01", "MECANIZA", "PRENBAL1", "ROSC_REM"],
    "P120": ["APUNCHAS", "SOLDCHA1", "SOLDMADR", "SOLDMAN1", "SOLDMAN2", "SOLDMAN3", "SOLDMAN4", "SOLDMAN5", "SOLDMAN6", "SOLDMAN7", "SOLDMAP1", "SOLDMAP2", "SOLDMAP3", "SOLROB06", "SOLROB08", "SOLROB09", "SOLROB10", "SOLROB12", "SOLROB13", "SOLROB14", "SOLROB15", "SOLROB16", "SOLROB17"],
    "P130": ["MONTIN01", "MONTIN02", "MONTIN03", "MONTIN04", "MONTJAD1"],
    "P140": ["LAVADO01", "PINTURA1", "PINTURA2"],
    "P150": ["MONFIN01", "MONFIN02", "MONFIN03", "MONFIN04", "MTJBARAP", "MTJF01PD", "MTJF02PD", "MTJF03PD", "MTJPRS"],
    "P160": ["ARCUCH01", "ARMBAR01", "ARMCUERP", "ARMDOSIF", "ARTOLVAS", "SUBCONJU", "TURBINAS"],
    "P180": ["CARGAFIN", "MURFINAL"], "P190": ["HOSPITAL"], "CC01": ["POSVENTA"], "ID01": ["PROTOTIPO"], "L010": ["PRINCIPAL"]
}
LISTA_ALMACENES = list(ALMACENES_PUESTOS.keys())

def obtener_siguiente_codigo_k(df):
    if df.empty or 'N° Etiquetas' not in df.columns or df['N° Etiquetas'].dropna().empty: 
        return "K00000001"
    numeros = [int(m.group(0)) for val in df['N° Etiquetas'].dropna() if (m := re.search(r'\d+', str(val)))]
    if not numeros:
        return "K00000001"
    set_num = set(numeros)
    i = 1
    while i in set_num: 
        i += 1
    return f"K{i:08d}"

def obtener_lote_packaging(mat_codigo):
    if os.path.exists(PKG_FILE):
        try:
            df_pkg = pd.read_excel(PKG_FILE)
            col_mat = [c for c in df_pkg.columns if 'material' in str(c).lower() or 'código' in str(c).lower()]
            col_lote = [c for c in df_pkg.columns if 'lote' in str(c).lower() or 'cant' in str(c).lower() or 'pack' in str(c).lower()]
            
            c_m = col_mat[0] if col_mat else df_pkg.columns[0]
            c_l = col_lote[0] if col_lote else df_pkg.columns[1]
            
            match = df_pkg[df_pkg[c_m].fillna('').astype(str).str.strip().str.upper() == mat_codigo.strip().upper()]
            if not match.empty:
                val = float(match.iloc[0][c_l])
                return val if val > 0 else None
        except Exception:
            return None
    return None

st.subheader("➕ Alta de Nuevo Kanban")

if 'msg_crear_exito' in st.session_state:
    st.success(st.session_state['msg_crear_exito'])
    del st.session_state['msg_crear_exito']

df_curr = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME) if os.path.exists(DB_FILE) else pd.DataFrame()
proximo_k_val = obtener_siguiente_codigo_k(df_curr)

st.info(f"Próximo Código K asignado automáticamente: **{proximo_k_val}**")

col1, col2, col3 = st.columns(3)
with col1:
    centro = st.text_input("Centro", value="A110")
    material = st.text_input("Código de Material (ej. PB005075)", max_chars=12).upper().strip()
    
    lote_pkg_std = obtener_lote_packaging(material) if material else None
    if lote_pkg_std:
        st.success(f"📦 Lote Packaging registrado para `{material}`: **{lote_pkg_std:.0f} UN**")
    elif material:
        st.caption("ℹ️ Sin lote de packaging prefijado en catálogo.")

    tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"])
    medio_str = f"GAVETA {st.selectbox('Tamaño Gaveta', ['S', 'M', 'L', 'XL'])}" if tipo_soporte == "GAVETA" else st.selectbox("Medio Físico", ["SIN MEDIO DEFINIDO", "PALLET CHICO", "PALLET GRANDE", "CANASTO", "CAPACHO CHICO", "CAPACHO GRANDE", "RACK"])

with col2:
    almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index("L010"))
    almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index("P140"))
    es_interno = (almacen_origen != "L010")
    puesto_origen = st.selectbox("Puesto de Trabajo Origen", ["-- Seleccionar --"] + ALMACENES_PUESTOS.get(almacen_origen, [])) if es_interno else "-"
    opts_p_dest = ALMACENES_PUESTOS.get(almacen_destino, [])
    puesto_destino_final = st.selectbox("Puesto de Trabajo Destino", opts_p_dest) if opts_p_dest else st.text_input("Puesto Destino").upper().strip()

with col3:
    val_default_repo = float(lote_pkg_std) if lote_pkg_std else 0.0
    cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=val_default_repo, step=1.0)
    cant_pp = cant_repo if tipo_soporte == "GAVETA" else st.number_input("Cantidad Punto de Pedido", min_value=0.0, step=1.0)
    unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
    dias_prep = st.number_input("Días Abastecimiento", min_value=0, value=1)

if st.button("💾 Guardar y Crear Kanban", type="primary"):
    es_valido = True
    
    if not material or not puesto_destino_final:
        st.error("❌ NO SE PUDO CREAR: El Código de Material y el Puesto Destino son campos obligatorios.")
        es_valido = False
    elif tipo_soporte == "TARJETA" and float(cant_pp) >= float(cant_repo):
        st.error(f"❌ NO SE PUDO CREAR: En Tipo TARJETA, el Punto de Pedido ({cant_pp}) debe ser menor a la Reposición ({cant_repo}).")
        es_valido = False

    if es_valido and not df_curr.empty:
        duplicado = df_curr[
            (df_curr['Material'].fillna('').astype(str).str.strip().str.upper() == material) &
            (df_curr['Puesto de trabajo destino'].fillna('').astype(str).str.strip().str.upper() == puesto_destino_final)
        ]
        if not duplicado.empty:
            k_existente = duplicado.iloc[0].get('N° Etiquetas', 'N/A')
            st.error(f"⛔ NO SE PUDO CREAR: Ya existe un Kanban ({k_existente}) asignado para el Material **{material}** en el Puesto Destino **{puesto_destino_final}**.")
            es_valido = False

    if es_valido and lote_pkg_std:
        if cant_repo < lote_pkg_std:
            st.error(f"⛔ NO SE PUDO CREAR: La Cantidad de Reposición ({cant_repo:.0f}) no puede ser menor al Lote de Packaging estándar ({lote_pkg_std:.0f}).")
            es_valido = False
        elif (cant_repo % lote_pkg_std) != 0:
            st.error(f"⛔ NO SE PUDO CREAR: La Cantidad de Reposición ({cant_repo:.0f}) debe ser múltiplo del Lote de Packaging ({lote_pkg_std:.0f}).")
            es_valido = False

    if es_valido:
        now = obtener_fecha_hora_actual()
        usr = st.session_state['usuario']['email']
        tipo_etiqueta_val = "KI" if es_interno else "KE"
        
        nuevo_reg = {
            'N° Etiquetas': proximo_k_val, 
            'Tipo Etiqueta': tipo_etiqueta_val,
            'Tipo Kanban': tipo_soporte, 
            'Medio': medio_str, 
            'Material': material, 
            'Centro': centro,
            'Almacén Origen': almacen_origen, 
            'Almacen Destino': almacen_destino,
            'Puesto trabajo Origen': puesto_origen, 
            'Puesto de trabajo destino': puesto_destino_final,
            'Cantidad Reposicion': cant_repo, 
            'Unidad Reposicion': unidad,
            'Cantidad Punto de Pedido': cant_pp, 
            'Tiempo preparación abast. (en días)': dias_prep,
            'Fecha Modificación': now, 
            'Usuario Modificación': usr
        }
        
        df_act = pd.concat([df_curr, pd.DataFrame([nuevo_reg])], ignore_index=True)
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_act.to_excel(writer, sheet_name=SHEET_NAME, index=False)
            
        registrar_auditoria(now, usr, "ALTA KANBAN", proximo_k_val, material, "CREACIÓN")
        registrar_tracker_logistica(now, usr, "CREAR / IMPRIMIR ETIQUETA", proximo_k_val, material, almacen_origen, puesto_destino_final, "CREACIÓN")
        
        st.session_state['msg_crear_exito'] = f"✅ ¡Kanban {proximo_k_val} creado exitosamente!"
        st.toast(f"✅ ¡Kanban {proximo_k_val} creado!", icon="🎉")
        st.rerun()