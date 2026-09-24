import streamlit as st
import pandas as pd
import re
import os
import json
from datetime import datetime
import pytz

st.set_page_config(page_title="Gestor de Kanbans - Crucianelli", layout="wide")

# Configuración de Zona Horaria Argentina
ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def obtener_fecha_hora_arg():
    return datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")

DB_FILE = "TablaZ.xlsx"
PKG_FILE = "Lote packaging.xlsx"
LOG_FILE = "historial_cambios.csv"
USERS_FILE = "usuarios.json"
SHEET_NAME = "Kanbans CRUCIANELLI"

LOG_COLUMNS = [
    "Fecha_Hora", "Acción", "Código_K", "Material", 
    "Medio", "Almacén_Destino", "Puesto_Destino", "Usuario"
]

# ==========================================
# GESTIÓN DE USUARIOS PERSISTENTES
# ==========================================
def cargar_usuarios():
    usuarios_default = {
        "jairc@crucianelli.com": "procesojair"
    }
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return usuarios_default
    else:
        guardar_usuarios(usuarios_default)
        return usuarios_default

def guardar_usuarios(usuarios_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(usuarios_dict, f, indent=4)

USUARIOS_REGISTRADOS = cargar_usuarios()

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
OPCIONES_SOPORTE_TARJETA = ["PALLET CHICO", "PALLET GRANDE", "CANASTO", "CAPACHO CHICO", "CAPACHO GRANDE", "RACK"]
OPCIONES_GAVETA = ["S", "M", "L", "XL"]

# ==========================================
# GESTIÓN DE SESIÓN Y LOGIN / REGISTRO
# ==========================================
if 'usuario_email' not in st.session_state:
    st.session_state['usuario_email'] = None

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
                elif email_input in USUARIOS_REGISTRADOS and USUARIOS_REGISTRADOS[email_input] == password_input:
                    st.session_state['usuario_email'] = email_input
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
                    USUARIOS_REGISTRADOS[reg_email] = reg_pass1
                    guardar_usuarios(USUARIOS_REGISTRADOS)
                    st.success("✅ ¡Cuenta creada exitosamente! Ya puede iniciar sesión.")
    st.stop()

# ==========================================
# FUNCIONES DE BASE DE DATOS Y AUDITORÍA
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

def cargar_logs():
    if os.path.exists(LOG_FILE):
        try:
            df_logs = pd.read_csv(LOG_FILE, on_bad_lines='skip')
            for col in LOG_COLUMNS:
                if col not in df_logs.columns:
                    df_logs[col] = None
            return df_logs[LOG_COLUMNS]
        except Exception:
            return pd.DataFrame(columns=LOG_COLUMNS)
    return pd.DataFrame(columns=LOG_COLUMNS)

def registrar_log(accion, codigo_k, material, medio, alm_dest, puesto_dest, usuario):
    now = obtener_fecha_hora_arg()
    df_actual = cargar_logs()
    nuevo_log = pd.DataFrame([{
        "Fecha_Hora": now,
        "Acción": accion,
        "Código_K": codigo_k,
        "Material": material,
        "Medio": medio,
        "Almacén_Destino": alm_dest,
        "Puesto_Destino": puesto_dest,
        "Usuario": usuario
    }])
    df_final = pd.concat([df_actual, nuevo_log], ignore_index=True)
    df_final.to_csv(LOG_FILE, index=False)

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

val_fecha_str = "-"
val_detalle_str = "Sin registros"

df_logs_temp = cargar_logs()
if not df_logs_temp.empty:
    ultimo_reg = df_logs_temp.iloc[-1]
    val_fecha_str = str(ultimo_reg['Fecha_Hora'])
    usr = str(ultimo_reg['Usuario']).split('@')[0] if pd.notna(ultimo_reg['Usuario']) else ""
    acc = str(ultimo_reg['Acción']) if pd.notna(ultimo_reg['Acción']) else ""
    k_code = str(ultimo_reg['Código_K']) if pd.notna(ultimo_reg['Código_K']) else ""
    val_detalle_str = f"{usr} ({acc} {k_code})"

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
kpi1.metric("Total Kanbans", total_k)
kpi2.metric("Internos (KI)", internos_k)
kpi3.metric("Externos (KE)", externos_k)
kpi4.metric("Próximo Código K", proximo_k_val)

with kpi5:
    st.caption("Última Modificación (UTC-3)")
    st.markdown(f"**{val_fecha_str}**")
    st.caption(val_detalle_str)

st.markdown("---")

tabs = st.tabs(["➕ Crear Nuevo Kanban", "✏️ Modificar y Eliminar", "📊 Exportar Datos", "📜 Historial Auditoría"])

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
            tamano_medio = st.selectbox("Tamaño Gaveta", OPCIONES_GAVETA)
        else:
            tamano_medio = st.selectbox("Tipo Tarjeta/Contenedor", OPCIONES_SOPORTE_TARJETA)

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
            st.warning(f"⚠️ Atención: La cantidad ({int(cant_repo)}) debe ser múltiplo de {pkg_sugerido}.")
            
        # Lógica auto-copia y bloqueo si es GAVETA
        if tipo_soporte == "GAVETA":
            cant_pp = st.number_input(
                "Cantidad Punto de Pedido (Igual al Lote por ser Gaveta)", 
                value=cant_repo, 
                disabled=True
            )
        else:
            cant_pp = st.number_input(
                "Cantidad Punto de Pedido (Menor al Lote)", 
                min_value=0.0, 
                step=1.0
            )

        unidad = st.selectbox("Unidad Base", ["UN", "M", "L", "KG"])
        dias_prep = st.number_input("Tiempo Preparación / Días Abast.", min_value=0, value=1)

    st.markdown("---")
    if st.button("💾 Guardar y Crear Kanban", type="primary"):
        puesto_destino = MAPEO_PUESTOS.get(puesto_destino, puesto_destino)
        if puesto_origen:
            puesto_origen = MAPEO_PUESTOS.get(puesto_origen, puesto_origen)

        if not material or not puesto_destino:
            st.error("❌ El Código de Material y el Puesto Destino son obligatorios.")
        elif not re.match(r'^[A-Z]{2,3}\d{6}$', material):
            st.error("❌ Formato de Material inválido. Debe tener 2 o 3 letras seguidas de 6 números (ej. PB005075).")
        elif tipo_soporte == "TARJETA" and cant_pp >= cant_repo:
            st.error(f"❌ Regla de TARJETA: El Punto de Pedido ({cant_pp}) debe ser MENOR a la Cantidad de Reposición ({cant_repo}).")
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
                fecha_actual = obtener_fecha_hora_arg()
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
                registrar_log("CREO", proximo_k_val, material, tipo_soporte, almacen_destino, puesto_destino, usuario_actual)
                st.success(f"✅ ¡Kanban **{proximo_k_val}** creado correctamente por **{usuario_actual}**!")
                st.rerun()

# ==========================================
# TAB 2: CONSULTA, MODIFICACIÓN Y ELIMINACIÓN
# ==========================================
with tabs[1]:
    st.subheader("📋 Registro General de Kanbans")
    
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
    
    col_mod, col_del = st.columns([2, 1])
    
    # ----------------------------------
    # SECCIÓN DE MODIFICACIÓN
    # ----------------------------------
    with col_mod:
        st.subheader("✏️ Modificar Kanban Existente")
        
        busqueda_material = st.text_input("Ingrese Código de Material a Buscar:", key="search_mod").upper().strip()
        
        if busqueda_material:
            kanbans_encontrados = df_kanbans[df_kanbans['Material'] == busqueda_material]
            
            if kanbans_encontrados.empty:
                st.warning(f"No se encontraron Kanbans registrados para el material: **{busqueda_material}**")
            else:
                opciones_k = kanbans_encontrados['N° Etiquetas'].tolist()
                k_seleccionado = st.selectbox("Seleccione el Código K a modificar:", opciones_k)
                
                row = kanbans_encontrados[kanbans_encontrados['N° Etiquetas'] == k_seleccionado].iloc[0]
                
                pkg_sugerido_mod = dict_pkg.get(busqueda_material, None)
                if pkg_sugerido_mod:
                    st.info(f"📦 Lote de Packaging de Referencia: **{pkg_sugerido_mod}** unidades.")
                
                st.markdown(f"**Modificando Kanban:** `{k_seleccionado}` | **Material:** `{busqueda_material}`")
                
                m_col1, m_col2, m_col3 = st.columns(3)
                
                with m_col1:
                    m_centro = st.text_input("Centro", value=str(row['Centro'] or "A110"), key="m_centro")
                    
                    m_tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"], key="m_soporte")
                    if m_tipo_soporte == "GAVETA":
                        m_tamano_medio = st.selectbox("Tamaño Gaveta", OPCIONES_GAVETA, key="m_tam_gav")
                    else:
                        m_tamano_medio = st.selectbox("Tipo Tarjeta/Contenedor", OPCIONES_SOPORTE_TARJETA, key="m_tam_tarj")

                with m_col2:
                    alm_orig_val = row['Almacén Origen'] if row['Almacén Origen'] in LISTA_ALMACENES else "L010"
                    alm_dest_val = row['Almacen Destino'] if row['Almacen Destino'] in LISTA_ALMACENES else "P140"
                    
                    m_almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=LISTA_ALMACENES.index(alm_orig_val), key="m_alm_orig")
                    m_almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=LISTA_ALMACENES.index(alm_dest_val), key="m_alm_dest")
                    
                    m_es_interno = (m_almacen_origen != "L010")
                    m_tipo_etiqueta_sap = "KI" if m_es_interno else "KE"
                    
                    if m_es_interno:
                        puestos_orig_disp = ALMACENES_PUESTOS.get(m_almacen_origen, [])
                        m_puesto_origen = st.selectbox("Puesto Origen", ["-- Opcional / Seleccionar --"] + puestos_orig_disp, key="m_p_orig")
                        if m_puesto_origen == "-- Opcional / Seleccionar --":
                            m_puesto_origen = str(row['Puesto trabajo Origen'] or '')
                    else:
                        m_puesto_origen = None
                        st.caption("Puesto Origen: No aplica (Externo L010)")
                    
                    puestos_dest_disp = ALMACENES_PUESTOS.get(m_almacen_destino, [])
                    curr_p_dest = str(row['Puesto de trabajo destino'] or '')
                    idx_dest = (puestos_dest_disp.index(curr_p_dest) + 1) if curr_p_dest in puestos_dest_disp else 0
                    
                    m_puesto_dest_sel = st.selectbox("Puesto Destino", ["-- Seleccionar / Nuevo --"] + puestos_dest_disp, index=idx_dest, key="m_p_dest")
                    if m_puesto_dest_sel == "-- Seleccionar / Nuevo --":
                        m_puesto_destino = st.text_input("Escriba Puesto Destino", value=curr_p_dest, key="m_p_dest_text").upper().strip()
                    else:
                        m_puesto_destino = m_puesto_dest_sel

                with m_col3:
                    m_cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=float(row['Cantidad Reposicion'] or 0.0), step=1.0, key="m_cant_repo")
                    
                    # Lógica auto-copia y bloqueo si es GAVETA en Modificación
                    if m_tipo_soporte == "GAVETA":
                        m_cant_pp = st.number_input(
                            "Cantidad Punto Pedido (Igual al Lote)", 
                            value=m_cant_repo, 
                            disabled=True, 
                            key="m_cant_pp_gav"
                        )
                    else:
                        m_cant_pp = st.number_input(
                            "Cantidad Punto Pedido", 
                            min_value=0.0, 
                            value=float(row['Cantidad Punto de Pedido'] or 0.0), 
                            step=1.0, 
                            key="m_cant_pp_tarj"
                        )
                    
                    unidades_opts = ["UN", "M", "L", "KG"]
                    curr_un = str(row['Unidad Reposicion'] or "UN")
                    idx_un = unidades_opts.index(curr_un) if curr_un in unidades_opts else 0
                    m_unidad = st.selectbox("Unidad Base", unidades_opts, index=idx_un, key="m_un")
                    
                    m_dias_prep = st.number_input("Días Abastecimiento", min_value=0, value=int(row['Tiempo preparación abast. (en días)'] or 1), key="m_dias")

                if st.button("💾 Guardar Cambios del Kanban", type="primary"):
                    m_puesto_destino = MAPEO_PUESTOS.get(m_puesto_destino, m_puesto_destino)
                    if m_puesto_origen:
                        m_puesto_origen = MAPEO_PUESTOS.get(m_puesto_origen, m_puesto_origen)

                    if not m_puesto_destino:
                        st.error("❌ El Puesto Destino es obligatorio.")
                    elif m_tipo_soporte == "TARJETA" and m_cant_pp >= m_cant_repo:
                        st.error(f"❌ Regla de TARJETA: El Punto de Pedido ({m_cant_pp}) debe ser MENOR al Lote de Reposición ({m_cant_repo}).")
                    elif pkg_sugerido_mod and (m_cant_repo == 0 or m_cant_repo % pkg_sugerido_mod != 0):
                        st.error(f"❌ REGLA DE PACKAGING: La Cantidad ({int(m_cant_repo)}) debe ser múltiplo exacto de {pkg_sugerido_mod}.")
                    else:
                        fecha_actual = obtener_fecha_hora_arg()
                        usuario_actual = st.session_state['usuario_email']
                        
                        idx_target = df_kanbans[df_kanbans['N° Etiquetas'] == k_seleccionado].index[0]
                        
                        df_kanbans.loc[idx_target, 'Tipo Etiqueta'] = m_tipo_etiqueta_sap
                        df_kanbans.loc[idx_target, 'Centro'] = m_centro
                        df_kanbans.loc[idx_target, 'Almacén Origen'] = m_almacen_origen
                        df_kanbans.loc[idx_target, 'Almacen Destino'] = m_almacen_destino
                        df_kanbans.loc[idx_target, 'Puesto trabajo Origen'] = m_puesto_origen if m_puesto_origen else None
                        df_kanbans.loc[idx_target, 'Puesto de trabajo destino'] = m_puesto_destino
                        df_kanbans.loc[idx_target, 'Cantidad Reposicion'] = m_cant_repo
                        df_kanbans.loc[idx_target, 'Unidad Reposicion'] = m_unidad
                        df_kanbans.loc[idx_target, 'Cantidad Punto de Pedido'] = m_cant_pp
                        df_kanbans.loc[idx_target, 'Tiempo preparación abast. (en días)'] = m_dias_prep
                        df_kanbans.loc[idx_target, 'Fecha Modificación'] = fecha_actual
                        df_kanbans.loc[idx_target, 'Usuario Modificación'] = usuario_actual
                        
                        guardar_datos(df_kanbans)
                        registrar_log("ACTUALIZO", k_seleccionado, busqueda_material, m_tipo_soporte, m_almacen_destino, m_puesto_destino, usuario_actual)
                        st.success(f"✅ ¡Kanban **{k_seleccionado}** actualizado correctamente por **{usuario_actual}**!")
                        st.rerun()

    # ----------------------------------
    # SECCIÓN DE ELIMINACIÓN
    # ----------------------------------
    with col_del:
        st.subheader("🗑️ Eliminar Kanban")
        st.warning("Al eliminar un Kanban, su código K se libera y se registra en la auditoría.")
        
        k_a_eliminar = st.selectbox(
            "Seleccione Código K a eliminar:", 
            options=["-- Seleccionar --"] + list(df_kanbans['N° Etiquetas'].unique()),
            key="del_k_select"
        )
        
        if st.button("🗑️ Eliminar Definitivamente") and k_a_eliminar != "-- Seleccionar --":
            fila_del = df_kanbans[df_kanbans['N° Etiquetas'] == k_a_eliminar].iloc[0]
            mat_afectado = fila_del['Material']
            alm_dest_del = fila_del['Almacen Destino']
            puesto_dest_del = fila_del['Puesto de trabajo destino']
            usuario_actual = st.session_state['usuario_email']
            
            df_kanbans = df_kanbans[df_kanbans['N° Etiquetas'] != k_a_eliminar]
            guardar_datos(df_kanbans)
            registrar_log("ELIMINO", k_a_eliminar, mat_afectado, "N/A", alm_dest_del, puesto_dest_del, usuario_actual)
            st.success(f"♻️ Kanban **{k_a_eliminar}** eliminado con éxito.")
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
    st.subheader("📜 Historial Completo y Filtrado de Modificaciones")
    
    df_logs = cargar_logs()
    
    if not df_logs.empty:
        # Convertimos la columna Fecha_Hora a datetime para poder filtrar por fechas
        df_logs['Fecha_dt'] = pd.to_datetime(df_logs['Fecha_Hora'], errors='coerce')
        
        f_col1, f_col2, f_col3 = st.columns(3)
        
        valid_dates = df_logs['Fecha_dt'].dropna()
        min_date = valid_dates.min().date() if not valid_dates.empty else datetime.now().date()
        max_date = valid_dates.max().date() if not valid_dates.empty else datetime.now().date()
        
        with f_col1:
            rango_fechas = st.date_input(
                "📅 Seleccione Rango de Fechas:",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date
            )
        
        with f_col2:
            usuarios_list = ["Todos"] + list(df_logs['Usuario'].dropna().unique())
            usr_sel = st.selectbox("👤 Filtrar por Usuario:", usuarios_list)
            
        with f_col3:
            acciones_list = ["Todas", "CREO", "ACTUALIZO", "ELIMINO"]
            acc_sel = st.selectbox("⚡ Filtrar por Acción:", acciones_list)

        # Aplicación de filtros
        df_logs_filtrado = df_logs.copy()
        
        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            f_inicio, f_fin = rango_fechas
            df_logs_filtrado = df_logs_filtrado[
                (df_logs_filtrado['Fecha_dt'].dt.date >= f_inicio) & 
                (df_logs_filtrado['Fecha_dt'].dt.date <= f_fin)
            ]
            
        if usr_sel != "Todos":
            df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Usuario'] == usr_sel]
            
        if acc_sel != "Todas":
            df_logs_filtrado = df_logs_filtrado[df_logs_filtrado['Acción'] == acc_sel]

        # Eliminamos la columna auxiliar de datetime antes de mostrar/descargar
        df_logs_mostrar = df_logs_filtrado.drop(columns=['Fecha_dt']).sort_values(by="Fecha_Hora", ascending=False)

        st.dataframe(df_logs_mostrar, use_container_width=True)
        
        col_down_log, _ = st.columns([1, 2])
        with col_down_log:
            csv_logs = df_logs_mostrar.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte Filtrado (CSV)",
                data=csv_logs,
                file_name=f"Auditoria_Kanbans_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                type="primary"
            )
    else:
        st.info("Aún no hay registros de cambios en el sistema.")
