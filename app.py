import streamlit as st
import pandas as pd
import re
import os

st.set_page_config(page_title="Gestor de Kanbans - Crucianelli", layout="wide")

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

COLUMNS = [
    'N° Etiquetas', 'Tipo Etiqueta', 'Material', 'Centro', 
    'Almacén Origen', 'Almacen Destino', 'Puesto trabajo Origen', 
    'Puesto de trabajo destino', 'Cantidad Reposicion', 
    'Unidad Reposicion', 'Cantidad Punto de Pedido', 
    'Tiempo preparación abast. (en días)'
]

# Mapeo automático de corrección/unificación
MAPEO_PUESTOS = {
    "ARM HORQ": "ARM_HORQ",
    "SOLDROB08": "SOLROB08",
    "PREBAL01": "PRENBAL1",
    "ALMACÉN": "PRINCIPAL",
    "LOGISTICA": "PRINCIPAL",
    "L010": "PRINCIPAL"
}

# Lista Maestra Depurada de Puestos de Trabajo
PUESTOS_MASTER = sorted([
    "APUNCHAS", "ARCUCH01", "ARM_HORQ", "ARMBAR01", "ARMCUERP", "ARMDOSIF", "ARMTOLV", 
    "ARM_MAZ1", "ARTOLVAS", "CARGAFIN", "CORTE_01", "CORTE_02", "HOSPITAL", "LAVADO01", 
    "MECANIZA", "MONFIN01", "MONFIN02", "MONFIN03", "MONFIN04", "MONTIN01", "MONTIN02", 
    "MONTIN03", "MONTIN04", "MONTJAD1", "MTJBARAP", "MTJF01PD", "MTJF02PD", "MTJF03PD", 
    "MTJPRS", "MURFINAL", "PINTURA1", "PINTURA2", "POSVENTA", "PRENBAL1", "PRINCIPAL", 
    "PROTOTIPO", "ROSC_REM", "SOLDCHA1", "SOLDMADR", "SOLDMAN1", "SOLDMAN2", "SOLDMAN3", 
    "SOLDMAN4", "SOLDMAN5", "SOLDMAN6", "SOLDMAN7", "SOLDMAP1", "SOLDMAP2", "SOLDMAP3", 
    "SOLROB06", "SOLROB08", "SOLROB09", "SOLROB10", "SOLROB12", "SOLROB13", "SOLROB14", 
    "SOLROB15", "SOLROB16", "SOLROB17", "SUBCONJU", "TURBINAS"
])

def cargar_datos():
    if os.path.exists(DB_FILE):
        df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
        for col in COLUMNS:
            if col not in df.columns:
                df[col] = None
        return df[COLUMNS]
    else:
        return pd.DataFrame(columns=COLUMNS)

def guardar_datos(df):
    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

def obtener_siguiente_codigo_k(df):
    if df.empty or df['N° Etiquetas'].dropna().empty:
        return "K00000001"
    
    numeros = []
    for val in df['N° Etiquetas'].dropna():
        match = re.search(r'\d+', str(val))
        if match:
            numeros.append(int(match.group(0)))
            
    if not numeros:
        return "K00000001"
        
    set_numeros = set(numeros)
    max_num = max(numeros)
    
    for i in range(1, max_num + 1):
        if i not in set_numeros:
            return f"K{i:08d}"
            
    return f"K{max_num + 1:08d}"

df_kanbans = cargar_datos()

st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")

tabs = st.tabs(["➕ Crear Nuevo Kanban", "📋 Lista y Eliminar Kanban", "📊 Exportar a SAP"])

# ==========================================
# TAB 1: CREAR KANBAN
# ==========================================
with tabs[0]:
    st.subheader("Alta de Nuevo Kanban")
    
    proximo_k = obtener_siguiente_codigo_k(df_kanbans)
    st.info(f"**Próximo Código K asignado automáticamente:** `{proximo_k}`")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        centro = st.text_input("Centro", value="A110")
        
        material = st.text_input("Código de Material (ej. PB005075)", max_chars=9).upper().strip()
        
        tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"])
        if tipo_soporte == "GAVETA":
            tamano_medio = st.selectbox("Tamaño Gaveta", ["S", "M", "L", "XL"])
        else:
            tamano_medio = st.selectbox("Tipo Tarjeta/Contenedor", [
                "PALLET CHICO", "PALLET GRANDE", "CANASTO", 
                "CAPACHO CHICO", "CAPACHO GRANDE", "RACK"
            ])
            
        opciones_puesto_dest = ["-- Seleccionar / Nuevo --"] + PUESTOS_MASTER
        puesto_dest_sel = st.selectbox("Puesto de Trabajo Destino", opciones_puesto_dest)
        
        if puesto_dest_sel == "-- Seleccionar / Nuevo --":
            puesto_destino = st.text_input("Escriba el Puesto Destino", max_chars=8).upper().strip()
        else:
            puesto_destino = puesto_dest_sel

    with col2:
        almacen_origen = st.selectbox("Almacén Origen", ["L010", "P110", "P120", "P130", "P140", "P150", "P160", "P170", "P180", "P190"])
        almacen_destino = st.selectbox("Almacén Destino", ["P140", "P160", "P120", "P130", "P150", "P180", "P110", "P190", "L010"])
        
        es_interno = (almacen_origen != "L010")
        
        if es_interno:
            tipo_etiqueta_sap = "KI"
            st.caption("ℹ️ Abastecimiento INTERNO (KI)")
            
            opciones_puesto_orig = ["-- Opcional / Seleccionar --"] + PUESTOS_MASTER
            puesto_orig_sel = st.selectbox("Puesto de Trabajo Origen", opciones_puesto_orig)
            if puesto_orig_sel == "-- Opcional / Seleccionar --":
                puesto_origen = st.text_input("Escriba Puesto Origen", max_chars=8).upper().strip()
            else:
                puesto_origen = puesto_orig_sel
        else:
            tipo_etiqueta_sap = "KE"
            st.caption("ℹ️ Abastecimiento EXTERNO (KE)")
            puesto_origen = None
            st.text_input("Puesto de Trabajo Origen", value="- No aplica (Externo L010) -", disabled=True)

    with col3:
        cant_repo = st.number_input("Cantidad Reposición (Lote)", min_value=0.0, step=1.0)
        cant_pp = st.number_input("Cantidad Punto de Pedido", min_value=0.0, step=1.0)
        unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
        dias_prep = st.number_input("Tiempo Preparación / Días Abast.", min_value=0, value=1)

    proceso_sel = None
    if es_interno:
        st.markdown("---")
        st.subheader("⚙️ Procesos del Abastecimiento Interno")
        proceso_sel = st.selectbox("Proceso Requerido", [
            "Sin proceso específico",
            "Pintura Roja", "Pintura Blanca", "Pintura Negra",
            "Soldadura", "Balancines", "Armado", "Corte"
        ])

    st.markdown("---")
    if st.button("💾 Guardar y Crear Kanban", type="primary"):
        # Normalización automática
        puesto_destino = MAPEO_PUESTOS.get(puesto_destino, puesto_destino)
        if puesto_origen:
            puesto_origen = MAPEO_PUESTOS.get(puesto_origen, puesto_origen)

        if not material or not puesto_destino:
            st.error("❌ El Código de Material y el Puesto Destino son obligatorios.")
        else:
            duplicados = df_kanbans[
                (df_kanbans['Material'] == material) & 
                (df_kanbans['Puesto de trabajo destino'] == puesto_destino)
            ]
            
            if not duplicados.empty:
                st.error(f"⚠️ Ya existe un Kanban activo ({duplicados.iloc[0]['N° Etiquetas']}) para el Material '{material}' en el Puesto '{puesto_destino}'.")
            else:
                nuevo_registro = {
                    'N° Etiquetas': proximo_k,
                    'Tipo Etiqueta': tipo_etiqueta_sap,
                    'Material': material,
                    'Centro': centro,
                    'Almacén Origen': almacen_origen,
                    'Almacen Destino': almacen_destino,
                    'Puesto trabajo Origen': puesto_origen if puesto_origen else None,
                    'Puesto de trabajo destino': puesto_destino,
                    'Cantidad Reposicion': cant_repo,
                    'Unidad Reposicion': unidad,
                    'Cantidad Punto de Pedido': cant_pp,
                    'Tiempo preparación abast. (en días)': dias_prep
                }
                
                df_kanbans = pd.concat([df_kanbans, pd.DataFrame([nuevo_registro])], ignore_index=True)
                guardar_datos(df_kanbans)
                st.success(f"✅ ¡Kanban **{proximo_k}** creado correctamente!")
                st.rerun()

# ==========================================
# TAB 2: CONSULTA Y BORRADO
# ==========================================
with tabs[1]:
    st.subheader("Registro General de Kanbans")
    
    filtro_mat = st.text_input("🔍 Buscar por Material o Etiqueta K:").strip().upper()
    
    df_mostrar = df_kanbans.copy()
    if filtro_mat:
        df_mostrar = df_mostrar[
            df_mostrar['Material'].astype(str).str.contains(filtro_mat, na=False) | 
            df_mostrar['N° Etiquetas'].astype(str).str.contains(filtro_mat, na=False)
        ]
        
    st.dataframe(df_mostrar, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🗑️ Eliminar Kanban")
    st.warning("Al eliminar un Kanban, su código K quedará liberado y será reutilizado de forma automática en la próxima alta.")
    
    k_a_eliminar = st.selectbox(
        "Seleccione el Código K a eliminar:", 
        options=["-- Seleccionar --"] + list(df_kanbans['N° Etiquetas'].unique())
    )
    
    if st.button("🗑️ Eliminar Definitivamente") and k_a_eliminar != "-- Seleccionar --":
        df_kanbans = df_kanbans[df_kanbans['N° Etiquetas'] != k_a_eliminar]
        guardar_datos(df_kanbans)
        st.success(f"♻️ Kanban **{k_a_eliminar}** eliminado con éxito. El código ha quedado libre para reutilización.")
        st.rerun()

# ==========================================
# TAB 3: EXPORTAR A SAP Z
# ==========================================
with tabs[2]:
    st.subheader("Exportar Datos para SAP")
    st.write("Descargue el archivo Excel listo para importar en la transacción Z de SAP:")
    
    excel_bytes = pd.ExcelWriter("TablaZ_Export.xlsx", engine='openpyxl')
    df_kanbans.to_excel(excel_bytes, sheet_name=SHEET_NAME, index=False)
    excel_bytes.close()
    
    with open("TablaZ_Export.xlsx", "rb") as f:
        st.download_button(
            label="📥 Descargar Tabla Z (.xlsx)",
            data=f,
            file_name="TablaZ_Kanbans.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
