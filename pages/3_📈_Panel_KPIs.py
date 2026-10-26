import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from utils.style import aplicar_estilo_enterprise, obtener_ahora_arg
from src.services.db_service import obtener_kanbans_df, obtener_tracker_df

# Aplicar estilo visual Enterprise
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📈 Panel de Indicadores Clave (KPIs Ejecutivos)")

# --- 1. CARGA Y PREPARACIÓN DE DATOS DE KANBANS ---
df_kb = obtener_kanbans_df()

if not df_kb.empty:
    total_kanbans = len(df_kb)
    total_gaveta = len(df_kb[df_kb['Tipo Kanban'] == "GAVETA"])
    total_tarjeta = len(df_kb[df_kb['Tipo Kanban'] == "TARJETA"])

    # Lógica de Semáforo de Actividad (Nivel Directivo)
    ahora_actual = obtener_ahora_arg().replace(tzinfo=None)

    def evaluar_inactividad(fecha_val):
        if pd.isna(fecha_val) or str(fecha_val).strip() in ['-', '', 'nan', 'None', 'NaT']:
            return "🔴 Inactivo (> 6m)"
        try:
            dt = pd.to_datetime(fecha_val)
            if hasattr(dt, 'tz') and dt.tz is not None:
                dt = dt.tz_localize(None)
            dias = (ahora_actual - dt).days
            if dias <= 90:
                return "🟢 Activo Reciente (<= 3m)"
            elif 90 < dias <= 180:
                return "🟡 Moderado (3 a 6m)"
            else:
                return "🔴 Inactivo (> 6m)"
        except Exception:
            return "🔴 Inactivo (> 6m)"

    col_fecha_mod = 'Fecha Modificación' if 'Fecha Modificación' in df_kb.columns else 'fecha_modificacion'
    if col_fecha_mod in df_kb.columns:
        df_kb['Estado de Actividad'] = df_kb[col_fecha_mod].apply(evaluar_inactividad)
    else:
        df_kb['Estado de Actividad'] = "🔴 Inactivo (> 6m)"

    tot_activos_rec = len(df_kb[df_kb['Estado de Actividad'].str.contains('🟢')])
    tot_moderados = len(df_kb[df_kb['Estado de Actividad'].str.contains('🟡')])
    tot_inactivos = len(df_kb[df_kb['Estado de Actividad'].str.contains('🔴')])

    # TARJETAS DE MÉTRICAS GLOBALES
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📦 Total Kanbans", total_kanbans)
    m2.metric("📥 Gavetas / 🏷️ Tarjetas", f"{total_gaveta} / {total_tarjeta}")
    m3.metric("🟢 Activo Reciente (<=3m)", tot_activos_rec, f"{((tot_activos_rec/total_kanbans)*100):.1f}%")
    m4.metric("🟡 Moderado (3 a 6m)", tot_moderados, f"{((tot_moderados/total_kanbans)*100):.1f}%")
    m5.metric("🔴 Inactivo (>6m)", tot_inactivos, f"{((tot_inactivos/total_kanbans)*100):.1f}%", delta_color="inverse")

    st.markdown("---")
    
    col_g1, col_g2, col_g3 = st.columns([1, 1, 1])

    with col_g1:
        st.markdown("##### 🍕 Distribución por Tipo de Kanban")
        fig_pie = px.pie(
            df_kb, 
            names='Tipo Kanban', 
            color='Tipo Kanban',
            color_discrete_map={'GAVETA': '#2b5c8f', 'TARJETA': '#e07a5f'},
            hole=0.4
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("##### 🚦 Salud de Catálogo (Inactividad)")
        counts_act = df_kb['Estado de Actividad'].value_counts().reset_index()
        counts_act.columns = ['Estado', 'Cantidad']
        fig_sem = px.bar(
            counts_act,
            x='Estado',
            y='Cantidad',
            text='Cantidad',
            color='Estado',
            color_discrete_map={
                '🟢 Activo Reciente (<= 3m)': '#2a9d8f',
                '🟡 Moderado (3 a 6m)': '#e9c46a',
                '🔴 Inactivo (> 6m)': '#e76f51'
            }
        )
        fig_sem.update_traces(textposition='outside')
        fig_sem.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=False, height=300)
        st.plotly_chart(fig_sem, use_container_width=True)

    with col_g3:
        st.markdown("##### 🏭 Kanbans por Almacén Destino")
        almacenes_objetivo = ["P110", "P120", "P130", "P140", "P150", "P160", "P180", "P190"]
        col_alm = 'Almacen Destino' if 'Almacen Destino' in df_kb.columns else 'Almacén Destino'
        df_alm = df_kb[df_kb[col_alm].fillna('').isin(almacenes_objetivo)] if col_alm in df_kb.columns else pd.DataFrame()
        
        if not df_alm.empty:
            counts_alm = df_alm[col_alm].value_counts().reset_index()
            counts_alm.columns = ['Almacén', 'Cantidad']
            
            fig_alm = px.bar(
                counts_alm, 
                x='Almacén', 
                y='Cantidad', 
                text='Cantidad',
                color='Almacén',
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig_alm.update_traces(textposition='outside')
            fig_alm.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=False, height=300)
            st.plotly_chart(fig_alm, use_container_width=True)

    st.markdown("##### 📍 Cantidad de Kanbans por Puesto de Trabajo Destino (Top 15)")
    col_puesto = 'Puesto de trabajo destino' if 'Puesto de trabajo destino' in df_kb.columns else 'Puesto Destino'
    if col_puesto in df_kb.columns:
        counts_puesto = df_kb[col_puesto].fillna('SIN DEFINIR').value_counts().head(15).reset_index()
        counts_puesto.columns = ['Puesto Destino', 'Cantidad']
        
        fig_puesto = px.bar(
            counts_puesto, 
            y='Puesto Destino', 
            x='Cantidad', 
            orientation='h',
            text='Cantidad',
            color='Cantidad',
            color_continuous_scale='Viridis'
        )
        fig_puesto.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=20, b=20, l=10, r=10), height=360)
        st.plotly_chart(fig_puesto, use_container_width=True)

# --- 2. ANÁLISIS DE SLAs Y EVOLUCIÓN TEMPORAL LOGÍSTICA ---
st.markdown("---")
st.markdown("### ⏱️ Tiempos de Respuesta y Cumplimiento de SLAs Logísticos")

df_trk = obtener_tracker_df()

if not df_trk.empty:
    def parse_dt(val):
        if pd.isna(val) or str(val).strip() in ['-', '', 'nan', 'None']:
            return None
        try:
            return pd.to_datetime(val)
        except Exception:
            return None

    df_trk['dt_solicitud'] = df_trk['Fecha Solicitud'].apply(parse_dt) if 'Fecha Solicitud' in df_trk.columns else None
    
    col_f_imp = 'Fecha Impresion' if 'Fecha Impresion' in df_trk.columns else 'fecha_impresion'
    col_f_fin = 'Fecha Ejecución Logística' if 'Fecha Ejecución Logística' in df_trk.columns else 'fecha_finalizacion'
    
    df_trk['dt_imp'] = df_trk[col_f_imp].apply(parse_dt) if col_f_imp in df_trk.columns else None
    df_trk['dt_pst'] = df_trk[col_f_fin].apply(parse_dt) if col_f_fin in df_trk.columns else None

    # FILTRO POR RANGO DE FECHAS
    with st.container(border=True):
        st.markdown("##### 📅 Filtro por Rango de Fechas de Solicitud")
        col_f1, col_f2 = st.columns(2)
        f_min_default = datetime.now() - timedelta(days=90)
        f_max_default = datetime.now()
        
        with col_f1:
            fecha_inicio = st.date_input("Fecha Desde:", value=f_min_default.date())
        with col_f2:
            fecha_fin = st.date_input("Fecha Hasta:", value=f_max_default.date())

    # Filtrar dataframe según rango seleccionado
    if 'dt_solicitud' in df_trk.columns and df_trk['dt_solicitud'].notna().any():
        mask_fecha = df_trk['dt_solicitud'].apply(
            lambda dt: dt is not None and fecha_inicio <= dt.date() <= fecha_fin
        )
        df_trk_filtered = df_trk[mask_fecha].copy()
    else:
        df_trk_filtered = df_trk.copy()

    def diff_horas(dt1, dt2):
        if dt1 and dt2 and dt2 >= dt1:
            return round((dt2 - dt1).total_seconds() / 3600.0, 2)
        return np.nan

    df_trk_filtered['Horas_Imp'] = df_trk_filtered.apply(lambda r: diff_horas(r.get('dt_solicitud'), r.get('dt_imp')), axis=1)
    df_trk_filtered['Horas_Pst'] = df_trk_filtered.apply(lambda r: diff_horas(r.get('dt_solicitud'), r.get('dt_pst')), axis=1)

    # EVALUACIÓN DE SLAs
    sla_imp_cumplidos = (df_trk_filtered['Horas_Imp'] <= 24).sum()
    sla_imp_totales = df_trk_filtered['Horas_Imp'].dropna().count()
    pct_imp = (sla_imp_cumplidos / sla_imp_totales * 100) if sla_imp_totales > 0 else 0

    sla_pst_cumplidos = (df_trk_filtered['Horas_Pst'] <= 48).sum()
    sla_pst_totales = df_trk_filtered['Horas_Pst'].dropna().count()
    pct_pst = (sla_pst_cumplidos / sla_pst_totales * 100) if sla_pst_totales > 0 else 0

    # Estado de Carga SAP
    col_sap = 'Estado SAP' if 'Estado SAP' in df_trk_filtered.columns else 'cargado_sap'
    tot_sap_ok = df_trk_filtered[df_trk_filtered[col_sap].fillna('').astype(str).str.upper().isin(['SI', 'OK'])].shape[0] if col_sap in df_trk_filtered.columns else 0
    tot_general = df_trk_filtered.shape[0]
    pct_sap = (tot_sap_ok / tot_general * 100) if tot_general > 0 else 0

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    kpi_col1.metric("💻 Carga en SAP Realizada", f"{pct_sap:.0f}%", f"{tot_sap_ok} de {tot_general} tareas")
    kpi_col2.metric("🖨️ SLA Impresión (<24h)", f"{pct_imp:.0f}%", f"{df_trk_filtered['Horas_Imp'].mean():.1f} hs prom." if pd.notna(df_trk_filtered['Horas_Imp'].mean()) else "Sin datos")
    kpi_col3.metric("📍 SLA Puesto Destino (<48h)", f"{pct_pst:.0f}%", f"{df_trk_filtered['Horas_Pst'].mean():.1f} hs prom." if pd.notna(df_trk_filtered['Horas_Pst'].mean()) else "Sin datos")

    # Gráfico de tendencias
    df_trk_valid = df_trk_filtered.dropna(subset=['dt_solicitud']).copy() if 'dt_solicitud' in df_trk_filtered.columns else pd.DataFrame()
    if not df_trk_valid.empty:
        df_trk_valid['Fecha_Dia'] = df_trk_valid['dt_solicitud'].dt.strftime('%Y-%m-%d')
        
        df_group = df_trk_valid.groupby('Fecha_Dia').agg(
            Horas_Pst=('Horas_Pst', 'mean'),
            Horas_Imp=('Horas_Imp', 'mean')
        ).reset_index()

        st.markdown("##### 📈 Evolución Temporal de Tiempos de Respuesta (Horas)")
        
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=df_group['Fecha_Dia'], y=df_group['Horas_Pst'], mode='lines+markers',
            name='Total Llevado a Puesto', line=dict(color='#4285F4', width=3, shape='spline')
        ))
        fig_line.add_trace(go.Scatter(
            x=df_group['Fecha_Dia'], y=df_group['Horas_Imp'], mode='lines+markers',
            name='Carga a Impresión', line=dict(color='#F2994A', width=3, shape='spline')
        ))

        fig_line.update_layout(
            xaxis_title="Fecha de Solicitud", yaxis_title="Horas Transcurridas",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(t=30, b=20, l=10, r=10), height=380
        )
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info("Aún no hay registros en el Tracker Logístico de Supabase para analizar SLAs.")