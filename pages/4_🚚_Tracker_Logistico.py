import streamlit as st
import pandas as pd
import urllib.parse
from datetime import datetime
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_tracker_df
from src.database.connection import get_db_session
from src.database.models import TrackerSolicitud

aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("🚚 Tracker de Ejecución Logística")

with st.sidebar:
    st.markdown("### 🖨️ Configuración Impresora")
    printer_ip = st.text_input("IP Rotuladora Brother (Wi-Fi):", value="192.168.1.150", help="Dirección IP asignada a la Brother QL-1110NWB en la red de la planta.")

df_trk = obtener_tracker_df()

if df_trk.empty:
    st.info("ℹ️ No hay tareas ni solicitudes pendientes registradas en el Tracker Logístico.")
else:
    # Helper para normalizar valores 'SI', 'OK', etc.
    def es_si(val):
        return str(val).strip().upper() in ['SI', 'OK', 'COMPLETADO', 'TRUE', '1']

    def calcular_estado_general(row):
        c_sap = es_si(row.get('Estado SAP', 'NO'))
        c_imp = es_si(row.get('Estado Impresion', 'NO'))
        c_pst = es_si(row.get('Estado Puesto', 'Pendiente'))
        
        c = sum([c_sap, c_imp, c_pst])
        if c == 3:
            return "COMPLETADO"
        elif c > 0:
            return "EN PROCESO"
        return "PENDIENTE"

    df_trk['Estado General'] = df_trk.apply(calcular_estado_general, axis=1)

    estado_filter = st.radio("Filtrar por Estado:", ["TODOS", "PENDIENTES", "COMPLETADOS"], horizontal=True)

    if estado_filter == "PENDIENTES":
        df_show = df_trk[df_trk['Estado General'].isin(['PENDIENTE', 'EN PROCESO'])]
    elif estado_filter == "COMPLETADOS":
        df_show = df_trk[df_trk['Estado General'] == 'COMPLETADO']
    else:
        df_show = df_trk.copy()

    st.markdown("##### 📋 Tareas Solicitadas por Procesos")
    
    if df_show.empty:
        st.info("ℹ️ No se encontraron tareas para el filtro seleccionado.")
    else:
        for idx, row in df_show.iterrows():
            sol_id = str(row.get('ID Solicitud', f"row_{idx}"))
            k_code = str(row.get('Código K', '-')).strip().upper()
            mat_code = str(row.get('Material', '-')).strip().upper()
            action_type = str(row.get('Tipo de Acción', 'ACCIÓN')).strip().upper()
            puesto_dest = str(row.get('Puesto Destino', '-')).strip().upper()
            est_gen = str(row.get('Estado General', 'PENDIENTE'))
            solicitante = str(row.get('Usuario Solicitante', 'Sistema'))
            f_sol = str(row.get('Fecha Solicitud', '-'))

            # Estados actuales de los 3 checks
            st_sap = es_si(row.get('Estado SAP'))
            st_imp = es_si(row.get('Estado Impresion'))
            st_pst = es_si(row.get('Estado Puesto'))

            badge = "🔴" if est_gen == "PENDIENTE" else ("🟡" if est_gen == "EN PROCESO" else "🟢")

            with st.expander(f"{badge} [{action_type}] Código K: {k_code} | Material: {mat_code} | Destino: {puesto_dest} ({est_gen})"):
                c1, c_checks, c2 = st.columns([2, 2, 1])
                
                # --- DATOS DE LA SOLICITUD ---
                with c1:
                    st.write(f"**Fecha Solicitud:** `{f_sol}`")
                    st.write(f"**Solicitante:** `{solicitante}`")
                    st.write(f"**Acción Requerida:** `{row.get('Acción Requerida', '-')}`")
                    st.write(f"**Medio Físico:** `{row.get('Medio', '-')}`")
                    st.write(f"**Puesto Destino:** `{puesto_dest}`")
                
                # --- CONTROLES DE VERIFICACIÓN / CHECKS ---
                with c_checks:
                    st.markdown("##### ⚙️ Acciones Logística")
                    
                    # 1. Carga en SAP
                    chk1 = st.checkbox("1. Carga en SAP", value=st_sap, key=f"sap_{sol_id}_{idx}")
                    if chk1 != st_sap:
                        with get_db_session() as db:
                            t_sol = db.query(TrackerSolicitud).filter(TrackerSolicitud.id_solicitud == sol_id).first()
                            if t_sol:
                                t_sol.cargado_sap = "SI" if chk1 else "NO"
                                db.commit()
                        st.toast(f"✅ Estado SAP actualizado para {k_code}", icon="💾")
                        st.rerun()

                    # 2. Impresión de Etiqueta
                    chk2 = st.checkbox("2. Etiqueta Impresa", value=st_imp, key=f"imp_{sol_id}_{idx}")
                    if chk2 != st_imp:
                        with get_db_session() as db:
                            t_sol = db.query(TrackerSolicitud).filter(TrackerSolicitud.id_solicitud == sol_id).first()
                            if t_sol:
                                t_sol.impreso = "SI" if chk2 else "NO"
                                if chk2:
                                    t_sol.fecha_impresion = datetime.utcnow()
                                db.commit()
                        st.toast(f"✅ Estado Impresión actualizado para {k_code}", icon="🖨️")
                        st.rerun()

                    # 3. Ubicación física en Puesto
                    chk3 = st.checkbox("3. Kanban en Puesto Destino", value=st_pst, key=f"pst_{sol_id}_{idx}")
                    if chk3 != st_pst:
                        with get_db_session() as db:
                            t_sol = db.query(TrackerSolicitud).filter(TrackerSolicitud.id_solicitud == sol_id).first()
                            if t_sol:
                                t_sol.estado_fisico = "OK" if chk3 else "Pendiente"
                                if chk3:
                                    t_sol.fecha_finalizacion = datetime.utcnow()
                                db.commit()
                        st.toast(f"✅ Ubicación física registrada para {k_code}", icon="📍")
                        st.rerun()

                # --- VISTA QR ---
                with c2:
                    st.markdown("##### 🏷️ Etiqueta Kanban")
                    qr_data = f"KANBAN|{k_code}|MAT:{mat_code}|DEST:{puesto_dest}"
                    qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_data)}&size=140"
                    st.image(qr_url, width=140)