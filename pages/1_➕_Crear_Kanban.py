import streamlit as st
import pandas as pd
import re, os
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_kanbans_df
from src.services.kanban_service import crear_nuevo_kanban

aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

PKG_FILE = "Lote packaging.xlsx"

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

df_curr = obtener_kanbans_df()

col1, col2, col3 = st.columns(3)
with col1:
    centro = st.text_input("Centro", value="A110")
    material = st.text_input("Código de Material (ej. PB005075, CB003354)", max_chars=12).upper().strip()
    
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
    
    # 1. Validación de campos obligatorios
    if not material or not puesto_destino_final:
        st.error("❌ NO SE PUDO CREAR: El Código de Material y el Puesto Destino son campos obligatorios.")
        es_valido = False
    
    # 2. Validación de formato de Material Crucianelli (incluye CB, MPB, MCB, PB, CM)
    patron_material = r'^(PB|CM|MPB|MCB|CB|PA|C|M|P|A|K)[0-9]{3,8}$'
    if es_valido and not re.match(patron_material, material):
        st.error(f"❌ FORMATO DE MATERIAL INVÁLIDO: '{material}' no coincide con el estándar de códigos corporativos (ej. PB005075, CB003354, CM001462).")
        es_valido = False

    # 3. Cantidad de reposición válida
    if es_valido and float(cant_repo) <= 0:
        st.error("❌ CANTIDAD INVÁLIDA: La Cantidad de Reposición debe ser mayor a 0.")
        es_valido = False

    # 4. Inconsistencia Punto de Pedido en TARJETA
    elif es_valido and tipo_soporte == "TARJETA" and float(cant_pp) >= float(cant_repo):
        st.error(f"❌ NO SE PUDO CREAR: En Tipo TARJETA, el Punto de Pedido ({cant_pp}) debe ser estrictamente menor a la Reposición ({cant_repo}).")
        es_valido = False

    # 5. Validación Lote Packaging Estándar
    if es_valido and lote_pkg_std:
        if cant_repo < lote_pkg_std:
            st.error(f"⛔ NO SE PUDO CREAR: La Cantidad de Reposición ({cant_repo:.0f}) no puede ser menor al Lote de Packaging estándar ({lote_pkg_std:.0f}).")
            es_valido = False
        elif (cant_repo % lote_pkg_std) != 0:
            st.error(f"⛔ NO SE PUDO CREAR: La Cantidad de Reposición ({cant_repo:.0f}) debe ser múltiplo del Lote de Packaging ({lote_pkg_std:.0f}).")
            es_valido = False

    if es_valido:
        usr = st.session_state['usuario']['email']
        tipo_etiqueta_val = "KI" if es_interno else "KE"
        
        datos_kanban = {
            'tipo_etiqueta': tipo_etiqueta_val,
            'tipo_kanban': tipo_soporte,
            'medio': medio_str,
            'material': material,
            'centro': centro,
            'almacen_origen': almacen_origen,
            'almacen_destino': almacen_destino,
            'puesto_origen': puesto_origen,
            'puesto_destino': puesto_destino_final,
            'cantidad_reposicion': cant_repo,
            'unidad_reposicion': unidad,
            'cantidad_punto_pedido': cant_pp,
            'tiempo_preparacion_dias': int(dias_prep)
        }
        
        ok, msg = crear_nuevo_kanban(datos_kanban, usr)
        if ok:
            st.session_state['msg_crear_exito'] = f"✅ {msg}"
            st.toast(f"✅ {msg}", icon="🎉")
            st.rerun()
        else:
            st.error(f"⛔ {msg}")