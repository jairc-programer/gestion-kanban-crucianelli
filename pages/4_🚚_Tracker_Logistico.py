import streamlit as st
import pandas as pd
import os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    ARG_TZ = ZoneInfo('America/Argentina/Buenos_Aires')
except ImportError:
    import pytz
    ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("🚚 Tracker de Ejecución Logística")

TRACKER_FILE = "tracker_ejecucion.csv"

if os.path.exists(TRACKER_FILE):
    df_trk = pd.read_csv(TRACKER_FILE)
    
    # Normalización y compatibilidad de nombres de columnas
    if 'Detalle / Observaciones' in df_trk.columns and 'Detalle' not in df_trk.columns:
        df_trk['Detalle'] = df_trk['Detalle / Observaciones']
    elif 'Detalle' in df_trk.columns and 'Detalle / Observaciones' not in df_trk.columns:
        df_trk['Detalle / Observaciones'] = df_trk['Detalle']

    cols_defaults = {
        'Estado Logístico': 'PENDIENTE',
        'Estado SAP': 'PENDIENTE',
        'Fecha SAP': '-',
        'Usuario SAP': '-',
        'Estado Fisico': 'PENDIENTE',
        'Fecha Fisico': '-',
        'Usuario Fisico': '-',
        'Detalle': 'Sin Detalle'
    }
    
    for col, default_val in cols_defaults.items():
        if col not in df_trk.columns:
            df_trk[col] = default_val
        else:
            df_trk[col] = df_trk[col].fillna(default_val)

    # Filtro por Estado
    estado_filter = st.radio("Filtrar por Estado:", ["TODOS", "PENDIENTES", "COMPLETADOS"], horizontal=True)
    
    def es_pendiente(r):
        s_sap = str(r.get('Estado SAP', '')).strip().upper()
        s_fis = str(r.get('Estado Fisico', '')).strip().upper()
        return s_sap != 'OK' or s_fis != 'OK'

    if estado_filter == "PENDIENTES":
        df_show = df_trk[df_trk.apply(es_pendiente, axis=1)]
    elif estado_filter == "COMPLETADOS":
        df_show = df_trk[~df_trk.apply(es_pendiente, axis=1)]
    else:
        df_show = df_trk.copy()

    st.markdown("##### 📋 Tareas Solicitadas por Procesos")
    
    if df_show.empty:
        st.info("No se encontraron tareas para el filtro seleccionado.")
    else:
        for idx, row in df_show.iterrows():
            k_code = str(row.get('Código K', '-'))
            mat_code = str(row.get('Material', '-'))
            action_type = str(row.get('Tipo de Acción', 'ACCIÓN'))
            puesto_dest = str(row.get('Puesto Destino', '-'))
            
            with st.expander(f"📦 [{action_type}] Código K: {k_code} | Material: {mat_code} | Puesto Destino: {puesto_dest}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Fecha Solicitud:** `{row.get('Fecha Solicitud')}`")
                    st.write(f"**Solicitante:** `{row.get('Usuario Solicitante')}`")
                    
                    # Detalle explicativo exacto de la modificación
                    det_val = str(row.get('Detalle', row.get('Detalle / Observaciones', '-')))
                    st.markdown(f"**Detalle de Cambios:** `{det_val}`")
                    st.write(f"**Ubicación:** Origen `{row.get('Almacén Origen')}` ➔ Destino `{puesto_dest}`")
                    
                with col2:
                    usr_log = st.session_state['usuario']['email']
                    now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    
                    sap_ok = (str(row.get('Estado SAP')).upper() == 'OK')
                    check_sap = st.checkbox("✅ Carga en SAP realizada", value=sap_ok, key=f"sap_chk_{idx}")
                    
                    fisico_ok = (str(row.get('Estado Fisico')).upper() == 'OK')
                    check_fisico = st.checkbox("🏷️ Cambio Físico / Etiqueta colocada", value=fisico_ok, key=f"fis_chk_{idx}")
                    
                    if check_sap != sap_ok or check_fisico != fisico_ok:
                        df_trk.loc[idx, 'Estado SAP'] = 'OK' if check_sap else 'PENDIENTE'
                        df_trk.loc[idx, 'Fecha SAP'] = now_str if check_sap else '-'
                        df_trk.loc[idx, 'Usuario SAP'] = usr_log if check_sap else '-'
                        
                        df_trk.loc[idx, 'Estado Fisico'] = 'OK' if check_fisico else 'PENDIENTE'
                        df_trk.loc[idx, 'Fecha Fisico'] = now_str if check_fisico else '-'
                        df_trk.loc[idx, 'Usuario Fisico'] = usr_log if check_fisico else '-'
                        
                        if check_sap and check_fisico:
                            df_trk.loc[idx, 'Estado Logístico'] = 'COMPLETADO'
                            df_trk.loc[idx, 'Fecha Ejecución Logística'] = now_str
                            df_trk.loc[idx, 'Usuario Logística'] = usr_log
                        else:
                            df_trk.loc[idx, 'Estado Logístico'] = 'PENDIENTE'

                        df_trk.to_csv(TRACKER_FILE, index=False)
                        st.toast("Estado logístico actualizado.", icon="💾")
                        st.rerun()

                st.caption(f"Status SAP: {df_trk.loc[idx, 'Estado SAP']} ({df_trk.loc[idx, 'Fecha SAP']}) | Status Físico: {df_trk.loc[idx, 'Estado Fisico']} ({df_trk.loc[idx, 'Fecha Fisico']})")

    st.markdown("---")
    st.dataframe(df_show, use_container_width=True)

else:
    st.info("No hay solicitudes registradas aún en el Tracker Logístico.")