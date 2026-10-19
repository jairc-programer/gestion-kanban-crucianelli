import streamlit as st
import pandas as pd
from utils.style import aplicar_estilo_enterprise, formatear_fecha_arg
from src.services.db_service import obtener_auditoria_df

aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📜 Historial de Auditoría de Cambios")

df_aud = obtener_auditoria_df()

if df_aud.empty:
    st.info("ℹ️ Aún no se registraron movimientos en el historial de auditoría de Supabase.")
else:
    # Formatear la columna 'Fecha y Hora' a hora local Argentina (UTC-3)
    if 'Fecha y Hora' in df_aud.columns:
        df_aud['Fecha y Hora'] = df_aud['Fecha y Hora'].apply(formatear_fecha_arg)

    col1, col2 = st.columns(2)
    with col1:
        busq = st.text_input("🔍 Buscar por Código K, Material o Usuario:", key="aud_search_input").strip().upper()
    with col2:
        accion_sel = st.selectbox("Filtrar por Acción:", ["TODAS", "CREACIÓN", "MODIFICACIÓN", "ELIMINACIÓN"], key="aud_action_filter")

    df_filt = df_aud.copy()
    
    if busq:
        df_filt = df_filt[
            df_filt['Código K'].fillna('').astype(str).str.contains(busq, case=False) |
            df_filt['Material'].fillna('').astype(str).str.contains(busq, case=False) |
            df_filt['Usuario'].fillna('').astype(str).str.contains(busq, case=False)
        ]
        
    if accion_sel != "TODAS":
        df_filt = df_filt[df_filt['Acción'].fillna('').astype(str).str.upper() == accion_sel]

    st.caption(f"Mostrando **{len(df_filt)}** de **{len(df_aud)}** eventos de auditoría.")
    st.dataframe(df_filt, use_container_width=True)