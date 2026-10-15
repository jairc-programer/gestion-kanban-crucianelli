import streamlit as st
import pandas as pd
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_kanbans_df
from src.services.kanban_service import eliminar_kanban_seguro
from src.database.connection import get_db_session
from src.database.models import Kanban, LogAuditoria, TrackerSolicitud

aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

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

st.subheader("✏️ Modificar / 🗑️ Eliminar Kanban")

if 'msg_mod_exito' in st.session_state:
    st.success(st.session_state['msg_mod_exito'])
    del st.session_state['msg_mod_exito']

if 'msg_del_exito' in st.session_state:
    st.success(st.session_state['msg_del_exito'])
    del st.session_state['msg_del_exito']

df_live = obtener_kanbans_df()

if not df_live.empty:
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
                mat_sel = str(row['Material']).strip().upper()
                
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
                    es_valido = True
                    
                    if not m_puesto_destino:
                        st.error("❌ NO SE PUDO MODIFICAR: El Puesto Destino es obligatorio.")
                        es_valido = False
                    elif m_tipo_soporte == "TARJETA" and float(m_cant_pp) >= float(m_cant_repo):
                        st.error(f"❌ NO SE PUDO MODIFICAR: En Tipo TARJETA, el Punto de Pedido ({m_cant_pp}) debe ser menor a la Reposición ({m_cant_repo}).")
                        es_valido = False

                    if es_valido:
                        usr_act = st.session_state['usuario']['email']
                        cant_pp_final = m_cant_repo if m_tipo_soporte == "GAVETA" else m_cant_pp
                        
                        # Guardar directo en Supabase via SQLAlchemy
                        with get_db_session() as db:
                            kb = db.query(Kanban).filter(Kanban.numero_etiqueta == k_sel).first()
                            if kb:
                                kb.centro = m_centro
                                kb.tipo_etiqueta = "KI" if m_es_interno else "KE"
                                kb.tipo_kanban = m_tipo_soporte
                                kb.medio = m_medio_str
                                kb.almacen_origen = m_almacen_origen
                                kb.almacen_destino = m_almacen_destino
                                kb.puesto_origen = m_puesto_origen
                                kb.puesto_destino = m_puesto_destino
                                kb.cantidad_reposicion = m_cant_repo
                                kb.cantidad_punto_pedido = cant_pp_final
                                kb.unidad_reposicion = m_unidad
                                kb.tiempo_preparacion_dias = int(m_dias)
                                kb.usuario_modificacion = usr_act
                                
                                # Auditoría
                                db.add(LogAuditoria(
                                    accion="MODIFICACIÓN",
                                    codigo_k=k_sel,
                                    material=mat_sel,
                                    medio=m_medio_str,
                                    almacen_destino=m_almacen_destino,
                                    puesto_destino=m_puesto_destino,
                                    detalle_cambio="Modificación de parámetros Kanban",
                                    usuario=usr_act
                                ))
                                db.commit()
                                
                        st.session_state['msg_mod_exito'] = f"✅ ¡Kanban {k_sel} modificado exitosamente!"
                        st.toast(f"✅ ¡Kanban {k_sel} modificado!", icon="💾")
                        st.rerun()
            else:
                st.warning(f"⚠️ No se encontraron Kanbans activos para la búsqueda: '{busqueda}'")

    with col_right:
        st.markdown("##### 🗑️ Eliminar Kanban")
        k_del = st.text_input("Código K a eliminar:", key="k_del_input").strip().upper()
        if st.button("Eliminar Definitivamente", type="primary", key="btn_del"):
            if not k_del:
                st.error("❌ NO SE PUDO ELIMINAR: Ingrese un Código K válido.")
            else:
                usr_act = st.session_state['usuario']['email']
                ok, msg = eliminar_kanban_seguro(k_del, usr_act)
                if ok:
                    st.session_state['msg_del_exito'] = msg
                    st.toast(msg, icon="🗑️")
                    st.rerun()
                else:
                    st.error(msg)