import streamlit as st
import pandas as pd
import re
import os
from datetime import datetime

st.set_page_config(page_title="Gestor de Kanbans - Crucianelli", layout="wide")

DB_FILE = "TablaZ.xlsx"
PKG_FILE = "Lote packaging.xlsx"
LOG_FILE = "historial_cambios.csv"
SHEET_NAME = "Kanbans CRUCIANELLI"

COLUMNS = [
    'N° Etiquetas', 'Tipo Etiqueta', 'Material', 'Centro', 
    'Almacén Origen', 'Almacen Destino', 'Puesto trabajo Origen', 
    'Puesto de trabajo destino', 'Cantidad Reposicion', 
    'Unidad Reposicion', 'Cantidad Punto de Pedido', 
    'Tiempo preparación abast. (en días)'
]

MAPEO_PUESTOS = {
    "ARM HORQ": "ARM_HORQ",
    "SOLDROB08": "SOLROB08",
    "PREBAL01": "PRENBAL1",
    "ALMACÉN": "PRINCIPAL",
    "LOGISTICA": "PRINCIPAL",
    "L010": "PRINCIPAL"
}

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

def cargar_packaging():
    if os.path.exists(PKG_FILE):
        try:
            df = pd.read_excel(PKG_FILE)
            df['Material'] = df['Material'].astype(str).str.strip().str.upper()
            return df.set_index('Material')['Packaing'].to_dict()
        except Exception:
            return {}
    return {}

def guardar_datos(df):
    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

def registrar_log(accion, codigo_k, material, usuario="SISTEMA"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    nuevo_log = pd.DataFrame([{
        "Fecha_Hora": now,
        "Acción": accion,
        "Código_K": codigo_k,
        "Material": material,
        "Usuario": usuario
    }])
    if os.path.exists(LOG_FILE):
        nuevo_log.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        nuevo_log.to_csv(LOG_FILE, mode='w', header=True, index=False)

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
dict_pkg = cargar_packaging()

st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")

# INDICADORES CLAVE (KPIs)
total_k = len(df_kanbans)
internos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KI'])
externos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KE'])
proximo_k_val = obtener_siguiente_codigo_k(df_kanbans)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Kanbans Activos", total_k)
kpi2.metric("Internos (KI)", internos_k)
kpi3.metric("Externos (KE)", externos_k)
kpi4.metric("Próximo Código K", proximo_k_val)

st.markdown("---")

tabs = st.tabs(["➕ Crear Nuevo Kanban", "📋 Lista y Eliminar", "📊 Exportar Datos", "📜 Historial Auditoría"])

# ==========================================
# TAB 1: CREAR KANBAN
# ==========================================
with tabs[0]:
    st.subheader("Alta de Nuevo Kanban")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        centro = st.text_input("Centro", value="A110")
        
        material = st.text_input("Código de Material (ej. PB005075)", max_chars=9).upper().strip()
        
        # Validar Packaging
        pkg_sugerido = dict_pkg.get(material, None)
        if pkg_sugerido:
            st.info(f"📦 **Lote de Packaging requerido:** {pkg_sugerido} unidades (o sus múltiplos)")
        
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
            st.markdown("🟡 **Estado:** :green[**ABASTECIMIENTO INTERNO (KI)**]")
            
            opciones_puesto_orig = ["-- Opcional / Seleccionar --"] + PUESTOS_MASTER
            puesto_orig_sel = st.selectbox("Puesto de Trabajo Origen", opciones_puesto_orig)
            if puesto_orig_sel == "-- Opcional / Seleccionar --":
                puesto_origen = st.text_input("Escriba Puesto Origen", max_chars=8).upper().strip()
            else:
                puesto_origen = puesto_orig_sel
        else:
            tipo_etiqueta_sap = "KE"
            st.markdown("🟡 **Estado:** :orange[**ABASTECIMIENTO EXTERNO (KE - L010)**]")
            puesto_origen = None
            st.text_input("Puesto de Trabajo Origen", value="- No aplica (Externo L010) -", disabled=True)

    with col3:
        default_cant = float(pkg_sugerido) if pkg_sugerido else 0.0
        cant_repo = st.number_input("Cantidad Reposición (Lote)", min_value=0.0, value=default_cant, step=1.0)
        
        # Alerta visual previa
        if pkg_sugerido and cant_repo > 0 and (cant_repo % pkg_sugerido != 0):
            st.warning(f"⚠️ Atención: Para creaciones nuevas, la cantidad ({int(cant_repo)}) debe ser múltiplo de {pkg_sugerido}.")
            
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
        puesto_destino = MAPEO_PUESTOS.get(puesto_destino, puesto_destino)
        if puesto_origen:
            puesto_origen = MAPEO_PUESTOS.get(puesto_origen, puesto_origen)

        # VALIDACIONES STRICTAS PARA NUEVAS CREACIONES
        if not material or not puesto_destino:
            st.error("❌ El Código de Material y el Puesto Destino son obligatorios.")
        elif not re.match(r'^[A-Z]{2,3}\d{6}$', material):
            st.error("❌ Formato de Material inválido. Debe tener 2 o 3 letras seguidas de 6 números (ej. PB005075).")
        elif pkg_sugerido and (cant_repo == 0 or cant_repo % pkg_sugerido != 0):
            st.error(f"❌ REGLA DE PACKAGING: La Cantidad de Reposición ({int(cant_repo)}) debe ser un múltiplo exacto de {pkg_sugerido} unidades para este material.")
        else:
            duplicados = df_kanbans[
                (df_kanbans['Material'] == material) & 
                (df_kanbans['Puesto de trabajo destino'] == puesto_destino)
            ]
            
            if not duplicados.empty:
                st.error(f"⚠️ Ya existe un Kanban activo ({duplicados.iloc[0]['N° Etiquetas']}) para el Material '{material}' en el Puesto '{puesto_destino}'.")
            else:
                nuevo_registro = {
                    'N° Etiquetas': proximo_k_val,
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
                registrar_log("CREAR", proximo_k_val, material)
                st.success(f"✅ ¡Kanban **{proximo_k_val}** creado correctamente respetando las reglas!")
                st.rerun()

# ==========================================
# TAB 2: CONSULTA Y BORRADO CON BADGES
# ==========================================
with tabs[1]:
    st.subheader("Registro General de Kanbans")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_mat = st.text_input("🔍 Buscar por Material o Código K:").strip().upper()
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por Tipo de Abastecimiento:", ["Todos", "KE - Externo", "KI - Interno"])

    df_mostrar = df_kanbans.copy()
    if filtro_mat:
        df_mostrar = df_mostrar[
            df_mostrar['Material'].astype(str).str.contains(filtro_mat, na=False) | 
            df_mostrar['N° Etiquetas'].astype(str).str.contains(filtro_mat, na=False)
        ]
        
    if filtro_tipo == "KE - Externo":
        df_mostrar = df_mostrar[df_mostrar['Tipo Etiqueta'] == 'KE']
    elif filtro_tipo == "KI - Interno":
        df_mostrar = df_mostrar[df_mostrar['Tipo Etiqueta'] == 'KI']

    def colorear_filas(val):
        if val == 'KE':
            return 'background-color: #FFF3CD; color: #856404; font-weight: bold;' # Amarillo
        elif val == 'KI':
            return 'background-color: #D4EDDA; color: #155724; font-weight: bold;' # Verde
        return ''

    st.dataframe(
        df_mostrar.style.map(colorear_filas, subset=['Tipo Etiqueta']),
        use_container_width=True
    )
    
    st.markdown("---")
    st.subheader("🗑️ Eliminar Kanban")
    st.warning("Al eliminar un Kanban, su código K quedará liberado y será reutilizado de forma automática en la próxima alta.")
    
    k_a_eliminar = st.selectbox(
        "Seleccione el Código K a eliminar:", 
        options=["-- Seleccionar --"] + list(df_kanbans['N° Etiquetas'].unique())
    )
    
    if st.button("🗑️ Eliminar Definitivamente") and k_a_eliminar != "-- Seleccionar --":
        mat_afectado = df_kanbans[df_kanbans['N° Etiquetas'] == k_a_eliminar]['Material'].values[0]
        df_kanbans = df_kanbans[df_kanbans['N° Etiquetas'] != k_a_eliminar]
        guardar_datos(df_kanbans)
        registrar_log("ELIMINAR", k_a_eliminar, mat_afectado)
        st.success(f"♻️ Kanban **{k_a_eliminar}** eliminado con éxito. El código ha quedado libre para reutilización.")
        st.rerun()

# ==========================================
# TAB 3: EXPORTAR DATOS
# ==========================================
with tabs[2]:
    st.subheader("Exportar Datos para SAP")
    st.write("Descargue los archivos sincronizados:")
    
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        excel_bytes = pd.ExcelWriter("TablaZ_Export.xlsx", engine='openpyxl')
        df_kanbans.to_excel(excel_bytes, sheet_name=SHEET_NAME, index=False)
        excel_bytes.close()
        
        with open("TablaZ_Export.xlsx", "rb") as f:
            st.download_button(
                label="📥 Descargar Tabla Z en Excel (.xlsx)",
                data=f,
                file_name="TablaZ_Kanbans.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with col_exp2:
        csv_data = df_kanbans.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📄 Descargar Tabla Z en CSV (.csv)",
            data=csv_data,
            file_name="TablaZ_Kanbans.csv",
            mime="text/csv"
        )

# ==========================================
# TAB 4: AUDITORÍA DE CAMBIOS
# ==========================================
with tabs[3]:
    st.subheader("Historial de Operaciones")
    if os.path.exists(LOG_FILE):
        df_logs = pd.read_csv(LOG_FILE)
        st.dataframe(df_logs.sort_values(by="Fecha_Hora", ascending=False), use_container_width=True)
    else:
        st.info("Aún no hay registros de cambios.")
