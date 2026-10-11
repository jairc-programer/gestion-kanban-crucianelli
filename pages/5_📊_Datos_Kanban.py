import streamlit as st
import pandas as pd
import os
import io

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📊 Base General de Kanbans")

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

if os.path.exists(DB_FILE):
    df_live = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
    
    # --- FILTROS DE BÚSQUEDA DINÁMICOS ---
    with st.container(border=True):
        st.markdown("##### 🔍 Filtros de Búsqueda")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            filtro_k = st.text_input("🔍 Filtro por Código Kanban (ej. K00000023):", placeholder="Buscar fragmento de código K...").strip().upper()
        with col_f2:
            filtro_mat = st.text_input("🔍 Filtro por Código de Material (ej. CM001462):", placeholder="Buscar fragmento de material...").strip().upper()

    df_filtrado = df_live.copy()

    # Aplicar filtros progresivos
    if filtro_k and 'N° Etiquetas' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado['N° Etiquetas'].fillna('').astype(str).str.upper().str.contains(filtro_k, na=False)
        ]
        
    if filtro_mat and 'Material' in df_filtrado.columns:
        df_filtrado = df_filtrado[
            df_filtrado['Material'].fillna('').astype(str).str.upper().str.contains(filtro_mat, na=False)
        ]

    st.caption(f"Mostrando **{len(df_filtrado)}** de **{len(df_live)}** registros totales.")
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    # Exportación a Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtrado.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    
    st.download_button(
        label="📥 Descargar Datos de Kanban (.xlsx)", 
        data=output.getvalue(), 
        file_name="Datos_Kanban_Filtrado.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
else:
    st.error(f"No se encontró el archivo de base de datos {DB_FILE}.")