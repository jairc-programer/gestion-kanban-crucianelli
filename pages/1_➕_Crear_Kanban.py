import streamlit as st
import pandas as pd
import re, os
from datetime import datetime
import pytz

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')
DB_FILE, PKG_FILE, LOG_FILE, TRACKER_FILE = "TablaZ.xlsx", "Lote packaging.xlsx", "historial_cambios.csv", "tracker_ejecucion.csv"
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
    if df.empty or df['N° Etiquetas'].dropna().empty: return "K00000001"
    numeros = [int(m.group(0)) for val in df['N° Etiquetas'].dropna() if (m := re.search(r'\d+', str(val)))]
    set_num = set(numeros)
    i = 1
    while i in set_num: i += 1
    return f"K{i:08d}"

st.subheader("➕ Alta de Nuevo Kanban")

df_curr = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME) if os.path.exists(DB_FILE) else pd.DataFrame()
proximo_k_val = obtener_siguiente_codigo_k(df_curr)

st.info(f"Próximo Código K asignado automáticamente: **{proximo_k_val}**")

col1, col2, col3 = st.columns(3)
with col1:
    centro = st.text_input("Centro", value="A110")
    material = st.text_input("Código de Material (ej. PB005075)", max_chars=12).upper().strip()
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
    cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, step=1.0)
    cant_pp = cant_repo if tipo_soporte == "GAVETA" else st.number_input("Cantidad Punto de Pedido", min_value=0.0, step=1.0)
    unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
    dias_prep = st.number_input("Días Abastecimiento", min_value=0, value=1)

if st.button("💾 Guardar y Crear Kanban", type="primary"):
    if not material or not puesto_destino_final:
        st.error("Material y Puesto Destino son obligatorios.")
    else:
        now = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
        usr = st.session_state['usuario']['email']
        nuevo_reg = {
            'N° Etiquetas': proximo_k_val, 'Tipo Etiqueta': "KI" if es_interno else "KE",
            'Tipo Kanban': tipo_soporte, 'Medio': medio_str, 'Material': material, 'Centro': centro,
            'Almacén Origen': almacen_origen, 'Almacen Destino': almacen_destino,
            'Puesto trabajo Origen': puesto_origen, 'Puesto de trabajo destino': puesto_destino_final,
            'Cantidad Reposicion': cant_repo, 'Unidad Reposicion': unidad,
            'Cantidad Punto de Pedido': cant_pp, 'Tiempo preparación abast. (en días)': dias_prep,
            'Fecha Modificación': now, 'Usuario Modificación': usr
        }
        df_act = pd.concat([df_curr, pd.DataFrame([nuevo_reg])], ignore_index=True)
        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
            df_act.to_excel(writer, sheet_name=SHEET_NAME, index=False)
        st.success(f"Kanban {proximo_k_val} creado exitosamente.")
        st.rerun()