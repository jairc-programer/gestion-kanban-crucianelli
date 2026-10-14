import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, timedelta
from utils.style import aplicar_estilo_enterprise

# Aplicar estilo visual Enterprise (Modo Oscuro Suave)
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📈 Panel de Indicadores Clave (KPIs)")

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"
TRACKER_FILE = "tracker_ejecucion.csv"

# --- 1. CARGA Y PREPARACIÓN DE DATOS BASE ---
if os.path.exists(DB_FILE):
    df_kb = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
    
    def inferir_tipo(r):
        try:
            c_repo = float(r.get('Cantidad Reposicion', 0))
            c_pp = float(r.get('Cantidad Punto de Pedido', 0))
            return "GAVETA" if c_repo == c_pp and c_repo > 0 else "TARJETA"
        except (ValueError, TypeError):
            return "TARJETA"
            
    if 'Tipo Kanban' not in df_kb.columns:
        df_kb['Tipo Kanban'] = df_kb.apply(inferir_tipo, axis=1)
    else:
        df_kb['Tipo Kanban'] = df_kb['Tipo Kanban'].fillna(df_kb.apply(inferir_tipo, axis=1))

    total_kanbans = len(df_kb)
    total_gaveta = len(df_kb[df_kb['Tipo Kanban'] == "GAVETA"])
    total_tarjeta = len(df_kb[df_kb['Tipo Kanban'] == "TARJETA"])

    m1, m2, m3 = st.columns(3)
    m1.metric("📦 Total Kanbans Activos", total_kanbans)
    m2.metric("📥 Total Gavetas", total_gaveta)
    m3.metric("🏷️ Total Tarjetas", total_tarjeta)

    col_g1, col_g2 = st.columns([1, 1])

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
        fig_pie.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_g2:
        st.markdown("##### 🏭 Cantidad de Kanbans por Almacén Destino")
        almacenes_objetivo = ["P110", "P120", "P130", "P140", "P150", "P160", "P180", "P190"]
        df_alm = df_kb[df_kb['Almacen Destino'].fillna('').isin(almacenes_objetivo)]
        
        counts_alm = df_alm['Almacen Destino'].value_counts().reset_index()
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
        fig_alm.update_layout(margin=dict(t=20, b=20, l=10, r=10), showlegend=False, height=320)
        st.plotly_chart(fig_alm, use_container_width=True)

    st.markdown("##### 📍 Cantidad de Kanbans por Puesto de Trabajo Destino (Top 15)")
    if 'Puesto de trabajo destino' in df_kb.columns:
        counts_puesto = df_kb['Puesto de trabajo destino'].fillna('SIN DEFINIR').value_counts().head(15).reset_index()
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
        fig_puesto.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=20, b=20, l=10, r=10), height=380)
        st.plotly_chart(fig_puesto, use_container_width=True)

# --- 2. ANÁLISIS DE SLAs Y EVOLUCIÓN TEMPORAL LOGÍSTICA ---
st.markdown("---")
st.markdown("### ⏱️ Tiempos de Respuesta y Cumplimiento de SLAs")

if os.path.exists(TRACKER_FILE):
    df_trk = pd.read_csv(TRACKER_FILE, dtype=str)
    
    def parse_dt(val):
        if pd.isna(val) or str(val).strip() in ['-', '', 'nan', 'None']:
            return None
        try:
            return datetime.strptime(str(val).strip(), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    df_trk['dt_solicitud'] = df_trk['Fecha Solicitud'].apply(parse_dt)
    df_trk['dt_sap'] = df_trk['Fecha SAP'].apply(parse_dt)
    df_trk['dt_imp'] = df_trk['Fecha Impresion'].apply(parse_dt)
    df_trk['dt_pst'] = df_trk['Fecha Puesto'].apply(parse_dt)

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
    mask_fecha = df_trk['dt_solicitud'].apply(
        lambda dt: dt is not None and fecha_inicio <= dt.date() <= fecha_fin
    )
    df_trk_filtered = df_trk[mask_fecha].copy()

    def diff_horas(dt1, dt2):
        if dt1 and dt2 and dt2 >= dt1:
            return round((dt2 - dt1).total_seconds() / 3600.0, 2)
        return np.nan

    df_trk_filtered['Horas_SAP'] = df_trk_filtered.apply(lambda r: diff_horas(r['dt_solicitud'], r['dt_sap']), axis=1)
    df_trk_filtered['Horas_Imp'] = df_trk_filtered.apply(lambda r: diff_horas(r['dt_solicitud'], r['dt_imp']), axis=1)
    df_trk_filtered['Horas_Pst'] = df_trk_filtered.apply(lambda r: diff_horas(r['dt_solicitud'], r['dt_pst']), axis=1)

    # EVALUACIÓN DE SLAs
    # Metas: SAP < 24h, Impresión < 24h, Puesto < 48h
    sla_sap_cumplidos = (df_trk_filtered['Horas_SAP'] <= 24).sum()
    sla_sap_totales = df_trk_filtered['Horas_SAP'].dropna().count()
    pct_sap = (sla_sap_cumplidos / sla_sap_totales * 100) if sla_sap_totales > 0 else 0

    sla_imp_cumplidos = (df_trk_filtered['Horas_Imp'] <= 24).sum()
    sla_imp_totales = df_trk_filtered['Horas_Imp'].dropna().count()
    pct_imp = (sla_imp_cumplidos / sla_imp_totales * 100) if sla_imp_totales > 0 else 0

    sla_pst_cumplidos = (df_trk_filtered['Horas_Pst'] <= 48).sum()
    sla_pst_totales = df_trk_filtered['Horas_Pst'].dropna().count()
    pct_pst = (sla_pst_cumplidos / sla_pst_totales * 100) if sla_pst_totales > 0 else 0

    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
    kpi_col1.metric("💻 SLA Carga SAP (<24h)", f"{pct_sap:.0f}%", f"{df_trk_filtered['Horas_SAP'].mean():.1f} hs prom." if pd.notna(df_trk_filtered['Horas_SAP'].mean()) else "Sin datos")
    kpi_col2.metric("🖨️ SLA Impresión (<24h)", f"{pct_imp:.0f}%", f"{df_trk_filtered['Horas_Imp'].mean():.1f} hs prom." if pd.notna(df_trk_filtered['Horas_Imp'].mean()) else "Sin datos")
    kpi_col3.metric("📍 SLA Puesto Destino (<48h)", f"{pct_pst:.0f}%", f"{df_trk_filtered['Horas_Pst'].mean():.1f} hs prom." if pd.notna(df_trk_filtered['Horas_Pst'].mean()) else "Sin datos")

    # Gráfico de tendencias
    df_trk_valid = df_trk_filtered.dropna(subset=['dt_solicitud']).copy()
    if not df_trk_valid.empty:
        df_trk_valid['Fecha_Dia'] = df_trk_valid['dt_solicitud'].dt.strftime('%Y-%m-%d')
        
        df_group = df_trk_valid.groupby('Fecha_Dia').agg(
            Horas_Pst=('Horas_Pst', 'mean'),
            Horas_Imp=('Horas_Imp', 'mean'),
            Horas_SAP=('Horas_SAP', 'mean')
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
        fig_line.add_trace(go.Scatter(
            x=df_group['Fecha_Dia'], y=df_group['Horas_SAP'], mode='lines+markers',
            name='Carga en SAP', line=dict(color='#BB6BD9', width=3, shape='spline')
        ))

        fig_line.update_layout(
            xaxis_title="Fecha de Solicitud", yaxis_title="Horas Transcurridas",
            hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(t=30, b=20, l=10, r=10), height=380
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("💡 No hay registros dentro del rango de fechas seleccionado.")
else:
    st.info("Aún no hay registros en el Tracker Logístico para analizar SLAs.")