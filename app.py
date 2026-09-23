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

# ==========================================
# BASE DE DATOS DE USUARIOS Y CONTRASEÑAS
# (Puedes agregar más usuarios en este diccionario)
# ==========================================
USUARIOS_REGISTRADOS = {
    "jairc@crucianelli.com": "procesojair",
    "admin@crucianelli.com": "admin123"
}

COLUMNS = [
    'N° Etiquetas', 'Tipo Etiqueta', 'Material', 'Centro', 
    'Almacén Origen', 'Almacen Destino', 'Puesto trabajo Origen', 
    'Puesto de trabajo destino', 'Cantidad Reposicion', 
    'Unidad Reposicion', 'Cantidad Punto de Pedido', 
    'Tiempo preparación abast. (en días)',
    'Fecha Modificación', 'Usuario Modificación'
]

MAPEO_PUESTOS = {
    "ARM HORQ": "ARM_HORQ",
    "SOLDROB08": "SOLROB08",
    "PREBAL01": "PRENBAL1",
    "ALMACÉN": "PRINCIPAL",
    "LOGISTICA": "PRINCIPAL",
    "L010": "PRINCIPAL"
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

# ==========================================
# GESTIÓN DE SESIÓN Y LOGIN
# ==========================================
if 'usuario_email' not in st.session_state:
    st.session_state['usuario_email'] = None

if not st.session_state['usuario_email']:
    st.title("🔐 Acceso al Sistema - Crucianelli")
    st.subheader("Ingrese sus credenciales corporativas")
    
    col_login1, col_login2 = st.columns([1, 2])
    with col_login1:
        email_input = st.text_input("Correo electrónico (@crucianelli.com):").strip().lower()
        password_input = st.text_input("Contraseña:", type="password")
        
        if st.button("Iniciar Sesión", type="primary"):
            if not email_input or not password_input:
                st.error("❌ Por favor ingrese su correo y contraseña.")
            elif not email_input.endswith("@crucianelli.com"):
                st.error("❌ El correo debe pertenecer al dominio @crucianelli.com.")
            elif email_input in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[email_input] == password_input:
                st.session_state['usuario_email'] = email_input
                st.success(f"Bienvenido/a {email_input}")
                st.rerun()
            else:
                st.error("❌ Credenciales incorrectas. Verifique el usuario y la contraseña.")
    st.stop()

# ==========================================
# FUNCIONES DE BASE DE DATOS
# ==========================================
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

def registrar_log(accion, codigo_k, material, usuario):
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

# ==========================================
# CABECERA Y METRICAS / KPIS
# ==========================================
col_title, col_user = st.columns([4, 1])
with col_title:
    st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")
with col_user:
    st.write(f"👤 **Usuario:** `{st.session_state['usuario_email']}`")
    if st.button("Cerrar Sesión"):
        st.session_state['usuario_email'] = None
        st.rerun()

total_k = len(df_kanbans)
internos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KI'])
externos_k = len(df_kanbans[df_kanbans['Tipo Etiqueta'] == 'KE'])
proximo_k_val = obtener_siguiente_codigo_k(df_kanbans)

ultima_modif_str = "Sin registros"
if os.path.exists(LOG_FILE):
    df_logs_temp = pd.read_csv(LOG_FILE)
    if not df_logs_temp.empty:
        ultimo_reg = df_logs_temp.iloc[-1]
        fecha_h = ultimo_reg['Fecha_Hora']
        usr = ultimo_reg['Usuario'].split('@')[0]
        acc = ultimo_reg['Acción']
        k_code = ultimo_reg['Código_K']
        ultima_modif_str = f"{fecha_h} | {usr} ({acc} {k_code})"

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Kanbans", total_k)
kpi2.metric("Internos (KI)", internos_k)
kpi3.metric("Externos (KE)", externos_k)
kpi4.metric("Próximo Código K", proximo_k_val)
kpi5.metric("Última Modificación", ultima_modif_str)

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

    with col2:
        almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index("L010"))
        almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index("P140"))
        
        es_interno = (almacen_origen != "L010")
        
        if es_interno:
            tipo_etiqueta_sap = "KI"
            st.markdown("🟡 **Estado:** :green[**ABASTECIMIENTO INTERNO (KI)**]")
            
            puestos_origen_disponibles = ALMACENES_PUESTOS.get(almacen_origen, [])
            opciones_puesto_orig = ["-- Opcional / Seleccionar --"] + puestos_origen_disponibles
            puesto_orig_sel = st.selectbox(f"Puesto Origen (Filtrado por {almacen_origen})", opciones_puesto_orig)
            
            if puesto_orig_sel == "-- Opcional / Seleccionar --":
                puesto_origen = st.text_input("Escriba Puesto Origen", max_chars=8).upper().strip()
            else:
                puesto_origen = puesto_orig_sel
        else:
            tipo_etiqueta_sap = "KE"
            st.markdown("🟡 **Estado:** :orange[**ABASTECIMIENTO EXTERNO (KE - L010)**]")
            puesto_origen = None
            st.text_input("Puesto de Trabajo Origen", value="- No aplica (Externo L010) -", disabled=True)

        puestos_destino_disponibles = ALMACENES_PUESTOS.get(almacen_destino, [])
        opciones_puesto_dest = ["-- Seleccionar / Nuevo --"] + puestos_destino_disponibles
        puesto_dest_sel = st.selectbox(f"Puesto Destino (Filtrado por {almacen_destino})", opciones_puesto_dest)
        
        if puesto_dest_sel == "-- Seleccionar / Nuevo --":
            puesto_destino = st.text_input("Escriba el Puesto Destino", max_chars=8).upper().strip()
        else:
            puesto_destino = puesto_dest_sel

    with col3:
        default_cant = float(pkg_sugerido) if pkg_sugerido else 0.0
        cant_repo = st.number_input("Cantidad Reposición (Lote)", min_value=0.0, value=default_cant, step=1.0)
        
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
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                usuario_actual = st.session_state['usuario_email']
                
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
                    'Tiempo preparación abast. (en días)': dias_prep,
                    'Fecha Modificación': fecha_actual,
                    'Usuario Modificación': usuario_actual
                }
                
                df_kanbans = pd.concat([df_kanbans, pd.DataFrame([nuevo_registro])], ignore_index=True)
                guardar_datos(df_kanbans)
                registrar_log("CREAR", proximo_k_val, material, usuario_actual)
                st.success(f"✅ ¡Kanban **{proximo_k_val}** creado correctamente por **{usuario_actual}**!")
                st.rerun()

# ==========================================
# TAB 2: CONSULTA Y BORRADO
# ==========================================
with tabs[1]:
    st.subheader("Registro General de Kanbans")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_mat = st.text_input("🔍 Buscar por Material, Código K o Usuario:").strip().upper()
    with col_f2:
        filtro_tipo = st.selectbox("Filtrar por Tipo de Abastecimiento:", ["Todos", "KE - Externo", "KI - Interno"])

    df_mostrar = df_kanbans.copy()
    if filtro_mat:
        df_mostrar = df_mostrar[
            df_mostrar['Material'].astype(str).str.contains(filtro_mat, na=False) | 
            df_mostrar['N° Etiquetas'].astype(str).str.contains(filtro_mat, na=False) |
            df_mostrar['Usuario Modificación'].astype(str).str.upper().str.contains(filtro_mat, na=False)
        ]
        
    if filtro_tipo == "KE - Externo":
        df_mostrar = df_mostrar[df_mostrar['Tipo Etiqueta'] == 'KE']
    elif filtro_tipo == "KI - Interno":
        df_mostrar = df_mostrar[df_mostrar['Tipo Etiqueta'] == 'KI']

    def colorear_filas(val):
        if val == 'KE':
            return 'background-color: #FFF3CD; color: #856404; font-weight: bold;'
        elif val == 'KI':
            return 'background-color: #D4EDDA; color: #155724; font-weight: bold;'
        return ''

    st.dataframe(
        df_mostrar.style.map(colorear_filas, subset=['Tipo Etiqueta']),
        use_container_width=True
    )
    
    st.markdown("---")
    st.subheader("🗑️ Eliminar Kanban")
    st.warning("Al eliminar un Kanban, su código K quedará liberado y se registrará la baja en el historial.")
    
    k_a_eliminar = st.selectbox(
        "Seleccione el Código K a eliminar:", 
        options=["-- Seleccionar --"] + list(df_kanbans['N° Etiquetas'].unique())
    )
    
    if st.button("🗑️ Eliminar Definitivamente") and k_a_eliminar != "-- Seleccionar --":
        mat_afectado = df_kanbans[df_kanbans['N° Etiquetas'] == k_a_eliminar]['Material'].values[0]
        usuario_actual = st.session_state['usuario_email']
        
        df_kanbans = df_kanbans[df_kanbans['N° Etiquetas'] != k_a_eliminar]
        guardar_datos(df_kanbans)
        registrar_log("ELIMINAR", k_a_eliminar, mat_afectado, usuario_actual)
        st.success(f"♻️ Kanban **{k_a_eliminar}** eliminado con éxito por **{usuario_actual}**.")
        st.rerun()

# ==========================================
# TAB 3: EXPORTAR DATOS
# ==========================================
with tabs[2]:
    st.subheader("Exportar Datos para SAP")
    st.write("Descargue la base de datos actualizada con trazabilidad:")
    
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
    st.subheader("Historial Completo de Operaciones por Usuario")
    if os.path.exists(LOG_FILE):
        df_logs = pd.read_csv(LOG_FILE)
        
        usuarios_list = ["Todos"] + list(df_logs['Usuario'].unique())
        usr_sel = st.selectbox("Filtrar auditoría por usuario:", usuarios_list)
        
        if usr_sel != "Todos":
            df_logs = df_logs[df_logs['Usuario'] == usr_sel]
            
        st.dataframe(df_logs.sort_values(by="Fecha_Hora", ascending=False), use_container_width=True)
        
        csv_logs = df_logs.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte de Auditoría (CSV)",
            data=csv_logs,
            file_name="Auditoria_Kanbans.csv",
            mime="text/csv"
        )
    else:
        st.info("Aún no hay registros de cambios.")
