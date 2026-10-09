import streamlit as st
import pandas as pd
import plotly.express as px
import os

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📈 Panel Interactivo de KPIs")

DB_FILE = "TablaZ.xlsx"
if os.path.exists(DB_FILE):
    df = pd.read_excel(DB_FILE, sheet_name="Kanbans CRUCIANELLI")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Kanbans", len(df))
    c2.metric("Internos (KI)", len(df[df['Tipo Etiqueta'] == 'KI']))
    c3.metric("Externos (KE)", len(df[df['Tipo Etiqueta'] == 'KE']))
    
    if 'Puesto de trabajo destino' in df.columns:
        fig = px.bar(df['Puesto de trabajo destino'].value_counts().reset_index(), x='count', y='Puesto de trabajo destino', orientation='h', title="Top Puestos Destino", template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)