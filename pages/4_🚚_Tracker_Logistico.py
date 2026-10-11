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
    
    # Asegurar columnas necesarias
    cols_necesarias = {
        'Estado SAP': 'PENDIENTE',
        'Fecha SAP': '-',
        'Usuario SAP': '-',
        'Estado Fisico': 'PENDIENTE',
        'Fecha Fisico': '-',
        'Usuario Fisico': '-'
    }
    for col, val_default in cols_necesarias.items():
        if col not in df_trk.columns:
            df_trk[col] = val_default
            
    # Filtro por estado
    estado_filter = st.radio("Filtrar por Estado:", ["TODOS", "PENDIENTES", "COMPLETADOS"], horizontal=True)
    
    df_show = df_trk.copy()
    if estado_filter == "PENDIENTES":
        df_show = df_show[(df_show['Estado SAP'] == 'PENDIENTE') | (df_show['Estado Fisico'] == 'PENDIENTE')]
    elif estado_filter == "COMPLETADOS":
        df_show = df_show[(df_show['Estado SAP'] == 'OK') & (df_show['Estado Fisico'] == 'OK')]

    st.markdown("##### 📋 Tareas Solicitadas por Procesos")
    
    for idx, row in df_show.iterrows():
        with st.expander(f"📦 [{row.get('Tipo de Acción', 'ACCIÓN')}] Código K: {row.get('Código K')} | Material: {row.get('Material')} | Puesto: {row.get('Puesto Destino')}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Fecha Solicitud:** `{row.get('Fecha Solicitud')}`")
                st.write(f"**Solicitante:** `{row.get('Usuario Solicitante')}`")
                st.write(f"**Detalle:** {row.get('Detalle')}")
                st.write(f"**Ubicación:** Origen `{row.get('Almacén Origen')}` ➔ Destino `{row.get('Puesto Destino')}`")
                
            with col2:
                usr_log = st.session_state['usuario']['email']
                now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
                
                # Check 1: Carga en SAP
                sap_ok = (row.get('Estado SAP') == 'OK')
                check_sap = st.checkbox("✅ Carga en SAP realizada", value=sap_ok, key=f"sap_{idx}")
                
                # Check 2: Cambio Físico
                fisico_ok = (row.get('Estado Fisico') == 'OK')
                check_fisico = st.checkbox("🏷️ Cambio Físico / Etiqueta colocada", value=fisico_ok, key=f"fis_{idx}")
                
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

            st.caption(f"Status SAP: {row.get('Estado SAP')} ({row.get('Fecha SAP')}) | Status Físico: {row.get('Estado Fisico')} ({row.get('Fecha Fisico')})")

    # Muestra de tabla general
    st.markdown("---")
    st.dataframe(df_show, use_container_width=True)

else:
    st.info("No hay solicitudes registradas aún en el Tracker Logístico.")