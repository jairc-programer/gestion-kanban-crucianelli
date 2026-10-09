import streamlit as st
import pandas as pd
import os

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("🚚 Tracker de Ejecución Logística")

TRACKER_FILE = "tracker_ejecucion.csv"
if os.path.exists(TRACKER_FILE):
    df = pd.read_csv(TRACKER_FILE)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Sin registros de tracker logístico.")