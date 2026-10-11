import streamlit as st
import pandas as pd
import os

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📜 Historial de Auditoría")

LOG_FILE = "historial_cambios.csv"

if os.path.exists(LOG_FILE):
    df_log = pd.read_csv(LOG_FILE)
    
    # Sanitizar campos nulos o sin formato
    df_log = df_log.fillna('-')
    
    # Mostrar primero los cambios más recientes
    if not df_log.empty:
        df_log = df_log.iloc[::-1].reset_index(drop=True)
        
    st.dataframe(df_log, use_container_width=True)
else:
    st.info("Aún no se registraron movimientos en el historial de auditoría.")