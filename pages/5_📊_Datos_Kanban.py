import streamlit as st
import pandas as pd
import os, io

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📊 Base General de Kanbans")

DB_FILE = "TablaZ.xlsx"
if os.path.exists(DB_FILE):
    df = pd.read_excel(DB_FILE, sheet_name="Kanbans CRUCIANELLI")
    st.dataframe(df, use_container_width=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name="Kanbans CRUCIANELLI", index=False)
    
    st.download_button("📥 Descargar Tabla (.xlsx)", data=output.getvalue(), file_name="Kanbans_Crucianelli.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")