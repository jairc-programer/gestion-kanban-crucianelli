import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_kanbans_df

# Aplicar estilo visual Enterprise
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📊 Base General de Kanbans")

# Cargar catálogo directamente con inferencia automatizada de Tipo/Medio
df_live = obtener_kanbans_df()

if not df_live.empty:
    # --- INDICADOR DE INACTIVIDAD (> 6 MESES / 180 DÍAS) ---
    fecha_limite = datetime.now() - timedelta(days=180)

    def evaluar_inactividad(fecha_val):
        if pd.isna(fecha_val) or str(fecha_val).strip() in ['-', '', 'nan', 'None']:
            return "🔴 Inactivo (> 6 meses)"
        try:
            dt = pd.to_datetime(fecha_val)
            if hasattr(dt, 'tz') and dt.tz is not None:
                dt = dt.tz_localize(None)
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
        df_filtrado.to_excel(writer, sheet_name="Kanbans CRUCIANELLI", index=False)
    
    st.download_button(
        label="📥 Descargar Tabla (.xlsx)", 
        data=output.getvalue(), 
        file_name="Datos_Kanban_Filtrado.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
else:
    st.info("ℹ️ No se encontraron registros en la base de datos de Supabase.")