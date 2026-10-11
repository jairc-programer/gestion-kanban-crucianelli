import streamlit as st
import pandas as pd
import os, re
from datetime import datetime

# Manejo de Zona Horaria (zoneinfo nativo / pytz respaldo)
try:
    from zoneinfo import ZoneInfo
    ARG_TZ = ZoneInfo('America/Argentina/Buenos_Aires')
except ImportError:
    import pytz
    ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

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
OPCIONES_SOPORTE_TARJETA = ["SIN MEDIO DEFINIDO", "PALLET CHICO", "PALLET GRANDE", "CANASTO", "CAPACHO CHICO", "CAPACHO GRANDE", "RACK"]
OPCIONES_GAVETA = ["S", "M", "L", "XL"]

def registrar_auditoria(fecha_hora, usuario, accion, codigo_k, material, detalle):
    log_entry = {
        'Fecha y Hora': fecha_hora,
        'Usuario': usuario,
        'Acción': accion,
        'Código K': codigo_k,
        'Material': material,
        'Detalle de Cambios': detalle
    }
    df_log = pd.DataFrame([log_entry])
    if os.path.exists(LOG_FILE):
        df_log.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        df_log.to_csv(LOG_FILE, mode='w', header=True, index=False)

def registrar_tracker_logistica(fecha_hora, usuario, accion, codigo_k, material, origen, destino, detalle):
    tracker_entry = {
        'Fecha Solicitud': fecha_hora,
        'Usuario Solicitante': usuario,
        'Tipo de Acción': accion,
        'Código K': codigo_k,
        'Material': material,
        'Almacén Origen': origen,
        'Puesto Destino': destino,
        'Detalle / Observaciones': detalle,
        'Estado Logístico': 'PENDIENTE',
        'Fecha Ejecución Logística': '-',
        'Usuario Logística': '-'
    }
    df_trk = pd.DataFrame([tracker_entry])
    if os.path.exists(TRACKER_FILE):
        df_trk.to_csv(TRACKER_FILE, mode='a', header=False, index=False)
    else:
        df_trk.to_csv(TRACKER_FILE, mode='w', header=True, index=False)

st.subheader("✏️ Modificar / 🗑️ Eliminar Kanban")

if os.path.exists(DB_FILE):
    df_live = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
    
    if 'Tipo Kanban' not in df_live.columns:
        def inferir_tipo_kanban(r):
            try:
                c_repo = float(r.get('Cantidad Reposicion', 0))
                c_pp = float(r.get('Cantidad Punto de Pedido', 0))
                return "GAVETA" if c_repo == c_pp and c_repo > 0 else "TARJETA"
            except (ValueError, TypeError):
                return "TARJETA"
        df_live['Tipo Kanban'] = df_live.apply(inferir_tipo_kanban, axis=1)

    if 'Medio' not in df_live.columns:
        df_live['Medio'] = "SIN MEDIO DEFINIDO"

    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("##### ✏️ Modificar Kanban Existente")
        busqueda = st.text_input("Buscar por Material o Código K:", key="search_mod", placeholder="ej. CM000016").upper().strip()
        
        if busqueda:
            kanbans_encontrados = df_live[
                (df_live['Material'].fillna('').astype(str).str.strip().str.upper() == busqueda) |
                (df_live['Material'].fillna('').astype(str).str.contains(busqueda, na=False, regex=False)) |
                (df_live['N° Etiquetas'].fillna('').astype(str).str.strip().str.upper() == busqueda)
            ]
            
            if not kanbans_encontrados.empty:
                opciones_k = [
                    f"{r['N° Etiquetas']} | Material: {r['Material']} | Puesto: {r['Puesto de trabajo destino']}" 
                    for _, r in kanbans_encontrados.iterrows()
                ]
                
                sel_k_fmt = st.selectbox("Seleccione el Código K a modificar:", opciones_k, key="sel_k_mod_dropdown")
                k_sel = sel_k_fmt.split(" | ")[0].strip()
                row = kanbans_encontrados[kanbans_encontrados['N° Etiquetas'] == k_sel].iloc[0]
                mat_sel = str(row['Material'])
                
                st.markdown(f"**Modificando:** `{k_sel}` | **Material:** `{mat_sel}`")
                
                m_c1, m_c2, m_c3 = st.columns(3)
                with m_c1:
                    m_centro = st.text_input("Centro", value=str(row['Centro'] if pd.notna(row['Centro']) else "A110"), key=f"m_c_{k_sel}")
                    
                    tipo_kb_row = str(row.get('Tipo Kanban', 'TARJETA')).upper()
                    idx_soporte = 0 if "GAVETA" in tipo_kb_row else 1
                    m_tipo_soporte = st.selectbox("Tipo de Kanban", ["GAVETA", "TARJETA"], index=idx_soporte, key=f"m_sop_{k_sel}")
                    
                    medio_row = str(row.get('Medio', '')).strip() if pd.notna(row.get('Medio')) else ""
                    if m_tipo_soporte == "GAVETA":
                        tam_ext = medio_row.replace("GAVETA", "").strip()
                        idx_tam = OPCIONES_GAVETA.index(tam_ext) if tam_ext in OPCIONES_GAVETA else 0
                        m_tam_gav = st.selectbox("Tamaño Gaveta", OPCIONES_GAVETA, index=idx_tam, key=f"m_gav_{k_sel}")
                        m_medio_str = f"GAVETA {m_tam_gav}"
                    else:
                        idx_med = OPCIONES_SOPORTE_TARJETA.index(medio_row) if medio_row in OPCIONES_SOPORTE_TARJETA else 0
                        m_medio_str = st.selectbox("Medio Físico", OPCIONES_SOPORTE_TARJETA, index=idx_med, key=f"m_tarj_{k_sel}")

                with m_c2:
                    alm_o_val = str(row['Almacén Origen']).strip() if pd.notna(row['Almacén Origen']) else "L010"
                    alm_d_val = str(row['Almacen Destino']).strip() if pd.notna(row['Almacen Destino']) else "P140"
                    
                    idx_alm_o = LISTA_ALMACENES.index(alm_o_val) if alm_o_val in LISTA_ALMACENES else LISTA_ALMACENES.index("L010")
                    idx_alm_d = LISTA_ALMACENES.index(alm_d_val) if alm_d_val in LISTA_ALMACENES else LISTA_ALMACENES.index("P140")
                    
                    m_almacen_origen = st.selectbox("Almacén Origen", LISTA_ALMACENES, index=idx_alm_o, key=f"m_alm_o_{k_sel}")
                    m_almacen_destino = st.selectbox("Almacén Destino", LISTA_ALMACENES, index=idx_alm_d, key=f"m_alm_d_{k_sel}")
                    
                    m_es_interno = (m_almacen_origen != "L010")
                    p_orig_val = str(row['Puesto trabajo Origen']).strip() if pd.notna(row['Puesto trabajo Origen']) else "-"
                    
                    if m_es_interno:
                        opts_p_orig = ["-- Seleccionar --"] + ALMACENES_PUESTOS.get(m_almacen_origen, [])
                        idx_p_o = opts_p_orig.index(p_orig_val) if p_orig_val in opts_p_orig else 0
                        m_puesto_origen_sel = st.selectbox("Puesto Origen", opts_p_orig, index=idx_p_o, key=f"m_p_o_{k_sel}")
                        m_puesto_origen = m_puesto_origen_sel if m_puesto_origen_sel != "-- Seleccionar --" else "-"
                    else:
                        st.text_input("Puesto Origen", value="- No aplica (Externo L010) -", disabled=True, key=f"m_p_o_dis_{k_sel}")
                        m_puesto_origen = "-"

                    p_dest_val = str(row['Puesto de trabajo destino']).strip() if pd.notna(row['Puesto de trabajo destino']) else ""
                    opts_p_dest = ALMACENES_PUESTOS.get(m_almacen_destino, [])
                    if opts_p_dest:
                        idx_p_d = opts_p_dest.index(p_dest_val) if p_dest_val in opts_p_dest else 0
                        m_puesto_destino = st.selectbox("Puesto Destino", opts_p_dest, index=idx_p_d, key=f"m_p_d_{k_sel}")
                    else:
                        m_puesto_destino = st.text_input("Puesto Destino", value=p_dest_val, key=f"m_p_d_txt_{k_sel}").upper().strip()

                with m_c3:
                    try:
                        val_repo_init = float(row['Cantidad Reposicion'])
                    except (ValueError, TypeError):
                        val_repo_init = 0.0
                        
                    m_cant_repo = st.number_input("Cantidad Reposición", min_value=0.0, value=val_repo_init, step=1.0, key=f"m_cant_r_{k_sel}")
                    
                    if m_tipo_soporte == "GAVETA":
                        m_cant_pp = st.number_input("Cantidad Punto Pedido", value=m_cant_repo, disabled=True, key=f"m_cant_p_g_{k_sel}")
                    else:
                        try:
                            val_pp_init = float(row['Cantidad Punto de Pedido'])
                        except (ValueError, TypeError):
                            val_pp_init = 0.0
                        m_cant_pp = st.number_input("Cantidad Punto Pedido", min_value=0.0, value=val_pp_init, step=1.0, key=f"m_cant_p_t_{k_sel}")

                    unidades_lista = ["UN", "M", "L", "KG"]
                    un_val = str(row['Unidad Reposicion']).strip() if pd.notna(row['Unidad Reposicion']) else "UN"
                    idx_un = unidades_lista.index(un_val) if un_val in unidades_lista else 0
                    m_unidad = st.selectbox("Unidad Base", unidades_lista, index=idx_un, key=f"m_un_{k_sel}")
                    
                    try:
                        val_dias_init = int(row['Tiempo preparación abast. (en días)'])
                    except (ValueError, TypeError):
                        val_dias_init = 1
                    m_dias = st.number_input("Días Abastecimiento", min_value=0, value=val_dias_init, key=f"m_dias_{k_sel}")

                if st.button("💾 Guardar Cambios", type="primary", key=f"btn_save_{k_sel}"):
                    if not m_puesto_destino:
                        st.error("NO SE PUDO MODIFICAR: El Puesto Destino es obligatorio.")
                    elif m_tipo_soporte == "TARJETA" and float(m_cant_pp) >= float(m_cant_repo):
                        st.error(f"NO SE PUDO MODIFICAR: En Tipo TARJETA, Punto de Pedido ({m_cant_pp}) debe ser menor a Reposición ({m_cant_repo}).")
                    else:
                        usr_act = st.session_state['usuario']['email']
                        idx = df_live[df_live['N° Etiquetas'] == k_sel].index[0]
                        cant_pp_final = m_cant_repo if m_tipo_soporte == "GAVETA" else m_cant_pp
                        now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Actualizar base Excel
                        df_live.loc[idx, 'Centro'] = m_centro
                        df_live.loc[idx, 'Tipo Etiqueta'] = "KI" if m_es_interno else "KE"
                        df_live.loc[idx, 'Tipo Kanban'] = m_tipo_soporte
                        df_live.loc[idx, 'Medio'] = m_medio_str
                        df_live.loc[idx, 'Almacén Origen'] = m_almacen_origen
                        df_live.loc[idx, 'Almacen Destino'] = m_almacen_destino
                        df_live.loc[idx, 'Puesto trabajo Origen'] = m_puesto_origen
                        df_live.loc[idx, 'Puesto de trabajo destino'] = m_puesto_destino
                        df_live.loc[idx, 'Cantidad Reposicion'] = m_cant_repo
                        df_live.loc[idx, 'Cantidad Punto de Pedido'] = cant_pp_final
                        df_live.loc[idx, 'Unidad Reposicion'] = m_unidad
                        df_live.loc[idx, 'Tiempo preparación abast. (en días)'] = m_dias
                        df_live.loc[idx, 'Fecha Modificación'] = now_str
                        df_live.loc[idx, 'Usuario Modificación'] = usr_act
                        
                        with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                            df_live.to_excel(writer, sheet_name=SHEET_NAME, index=False)
                            
                        det_str = f"Modificación: Reposición={m_cant_repo}, PP={cant_pp_final}, Destino={m_puesto_destino}"
                        
                        # 1. Registrar en Auditoría (Página 6)
                        registrar_auditoria(now_str, usr_act, "MODIFICACIÓN", k_sel, mat_sel, det_str)
                        
                        # 2. Registrar en Tracker Logística (Página 4)
                        registrar_tracker_logistica(now_str, usr_act, "MODIFICAR ETIQUETA", k_sel, mat_sel, m_almacen_origen, m_puesto_destino, det_str)
                        
                        st.success(f"✅ Kanban {k_sel} actualizado y registrado en Auditoría y Tracker Logístico.")
                        st.rerun()
            else:
                st.warning(f"No se encontraron Kanbans activos para: {busqueda}")

    with col_right:
        st.markdown("##### 🗑️ Eliminar Kanban")
        k_del = st.text_input("Código K a eliminar:", key="k_del_input").strip().upper()
        if st.button("Eliminar Definitivamente", type="primary", key="btn_del") and k_del:
            if k_del in df_live['N° Etiquetas'].values:
                usr_act = st.session_state['usuario']['email']
                row_del = df_live[df_live['N° Etiquetas'] == k_del].iloc[0]
                mat_del = str(row_del['Material'])
                alm_o_del = str(row_del.get('Almacén Origen', '-'))
                p_d_del = str(row_del.get('Puesto de trabajo destino', '-'))
                now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
                
                df_del = df_live[df_live['N° Etiquetas'] != k_del]
                with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                    df_del.to_excel(writer, sheet_name=SHEET_NAME, index=False)
                    
                det_del = f"Eliminación permanente de Kanban {k_del}"
                
                # 1. Registrar en Auditoría (Página 6)
                registrar_auditoria(now_str, usr_act, "ELIMINACIÓN", k_del, mat_del, det_del)
                
                # 2. Registrar en Tracker Logística (Página 4)
                registrar_tracker_logistica(now_str, usr_act, "RETIRAR KANBAN", k_del, mat_del, alm_o_del, p_d_del, det_del)
                
                st.success(f"Código {k_del} eliminado y registrado en Auditoría y Tracker Logístico.")
                st.rerun()
            else:
                st.error("El Código K ingresado no existe.")