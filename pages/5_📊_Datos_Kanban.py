import streamlit as st
import pandas as pd
import os, io
from datetime import datetime, timedelta

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📊 Base General de Kanbans")

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

if os.path.exists(DB_FILE):
    df_live = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
    
    # Inferir Tipo Kanban
    def inferir_tipo_kanban(r):
        try:
            c_repo = float(r.get('Cantidad Reposicion', 0))
            c_pp = float(r.get('Cantidad Punto de Pedido', 0))
            return "GAVETA" if c_repo == c_pp and c_repo > 0 else "TARJETA"
        except (ValueError, TypeError):
            return "TARJETA"

    if 'Tipo Kanban' not in df_live.columns:
        df_live['Tipo Kanban'] = df_live.apply(inferir_tipo_kanban, axis=1)

    if 'Medio' not in df_live.columns:
        df_live['Medio'] = "SIN MEDIO DEFINIDO"

    # --- INDICADOR DE INACTIVIDAD (> 6 MESES / 180 DÍAS) ---
    fecha_limite = datetime.now() - timedelta(days=180)

    def evaluar_inactividad(fecha_val):
        if pd.isna(fecha_val) or str(fecha_val).strip() in ['-', '', 'nan']:
            return "🔴 Inactivo (> 6 meses)"
        try:
            dt = pd.to_datetime(fecha_val)
            if dt < fecha_limite:
                return "🔴 Inactivo (> 6 meses)"
            return "🟢 Activo Reciente"
        except Exception:
            return "🔴 Inactivo (> 6 meses)"

    if 'Fecha Modificación' in df_live.columns:
        df_live['Estado de Actividad'] = df_live['Fecha Modificación'].apply(evaluar_inactividad)
        df_live['Última Actualización'] = df_live['Fecha Modificación'].fillna('Sin Fecha')
    else:
        df_live['Estado de Actividad'] = "🔴 Inactivo (> 6 meses)"
        df_live['Última Actualización'] = "Sin Fecha"

    # --- FILTROS DE BÚSQUEDA ---
    with st.container(border=True):
        st.markdown("##### 🔍 Filtros de Búsqueda")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            filtro_k = st.text_input("🔍 Código Kanban:", placeholder="ej. K00000023").strip().upper()
        with c2:
            filtro_mat = st.text_input("🔍 Código Material:", placeholder="ej. CM001462").strip().upper()
        with c3:
            filtro_est = st.selectbox("Status Actividad:", ["TODOS", "🟢 Activo Reciente", "🔴 Inactivo (> 6 meses)"])

    df_filtrado = df_live.copy()

    if filtro_k and 'N° Etiquetas' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['N° Etiquetas'].fillna('').astype(str).str.upper().str.contains(filtro_k)]
        
    if filtro_mat and 'Material' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Material'].fillna('').astype(str).str.upper().str.contains(filtro_mat)]

    if filtro_est != "TODOS":
        df_filtrado = df_filtrado[df_filtrado['Estado de Actividad'] == filtro_est]

    st.caption(f"Mostrando **{len(df_filtrado)}** de **{len(df_live)}** registros totales.")
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_filtrado.to_excel(writer, sheet_name=SHEET_NAME, index=False)
    
    st.download_button(
        label="📥 Descargar Tabla (.xlsx)", 
        data=output.getvalue(), 
        file_name="Datos_Kanban_Filtrado.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
else:
    st.error(f"No se encontró el archivo {DB_FILE}")