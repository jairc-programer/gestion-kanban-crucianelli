import streamlit as st
import pandas as pd
import os

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📜 Historial de Auditoría")

LOG_FILE = "historial_cambios.csv"
if os.path.exists(LOG_FILE):
    df = pd.read_csv(LOG_FILE)
    st.dataframe(df.sort_values(by=df.columns[0], ascending=False), use_container_width=True)
else:
    st.info("Sin movimientos registrados en auditoría.")