import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

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

    # --- TARJETAS MÉTRICAS DE RESUMEN ---
    total_kanbans = len(df_kb)
    total_gaveta = len(df_kb[df_kb['Tipo Kanban'] == "GAVETA"])
    total_tarjeta = len(df_kb[df_kb['Tipo Kanban'] == "TARJETA"])

    m1, m2, m3 = st.columns(3)
    m1.metric("📦 Total Kanbans Activos", total_kanbans)
    m2.metric("📥 Total Gavetas", total_gaveta)
    m3.metric("🏷️ Total Tarjetas", total_tarjeta)

    # --- GRÁFICOS DE VOLUMEN DE KANBANS ---
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

    # --- KANBANS POR PUESTO DE TRABAJO DESTINO ---
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

else:
    st.error(f"No se encontró el archivo de datos {DB_FILE}")

# --- 2. EVOLUCIÓN TEMPORAL DE TIEMPOS DE RESPUESTA LOGÍSTICA ---
st.markdown("---")
st.markdown("### ⏱️ Tiempos de Respuesta de Ejecución Logística")

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

    # Cálculo de diferencias en días / horas
    def diff_dias(dt1, dt2):
        if dt1 and dt2 and dt2 >= dt1:
            return round((dt2 - dt1).total_seconds() / 86400.0, 2)
        return np.nan

    def diff_horas(dt1, dt2):
        if dt1 and dt2 and dt2 >= dt1:
            return round((dt2 - dt1).total_seconds() / 3600.0, 2)
        return np.nan

    df_trk['Dias_SAP'] = df_trk.apply(lambda r: diff_dias(r['dt_solicitud'], r['dt_sap']), axis=1)
    df_trk['Dias_Imp'] = df_trk.apply(lambda r: diff_dias(r['dt_solicitud'], r['dt_imp']), axis=1)
    df_trk['Dias_Total'] = df_trk.apply(lambda r: diff_dias(r['dt_solicitud'], r['dt_pst']), axis=1)

    df_trk['Horas_SAP'] = df_trk.apply(lambda r: diff_horas(r['dt_solicitud'], r['dt_sap']), axis=1)
    df_trk['Horas_Imp'] = df_trk.apply(lambda r: diff_horas(r['dt_solicitud'], r['dt_imp']), axis=1)
    df_trk['Horas_Pst'] = df_trk.apply(lambda r: diff_horas(r['dt_solicitud'], r['dt_pst']), axis=1)

    # Tarjetas Promedio
    avg_sap_h = df_trk['Horas_SAP'].dropna().mean()
    avg_imp_h = df_trk['Horas_Imp'].dropna().mean()
    avg_pst_h = df_trk['Horas_Pst'].dropna().mean()

    col_k1, col_k2, col_k3 = st.columns(3)
    col_k1.metric("💻 Promedio Carga SAP", f"{avg_sap_h:.1f} hs" if pd.notna(avg_sap_h) else "Sin datos")
    col_k2.metric("🖨️ Promedio Impresión/Etiqueta", f"{avg_imp_h:.1f} hs" if pd.notna(avg_imp_h) else "Sin datos")
    col_k3.metric("📍 Promedio Llevado a Puesto", f"{avg_pst_h:.1f} hs" if pd.notna(avg_pst_h) else "Sin datos")

    # Agrupar por Fecha de Solicitud (Día / Mes)
    df_trk_valid = df_trk.dropna(subset=['dt_solicitud']).copy()
    
    if not df_trk_valid.empty:
        df_trk_valid['Fecha_Dia'] = df_trk_valid['dt_solicitud'].dt.strftime('%Y-%m-%d')
        
        df_group = df_trk_valid.groupby('Fecha_Dia').agg(
            Dias_Total=('Dias_Total', 'mean'),
            Dias_SAP=('Dias_SAP', 'mean'),
            Dias_Imp=('Dias_Imp', 'mean')
        ).reset_index()

        st.markdown("##### 📈 Evolución Temporal de Tiempos de Respuesta (en Días / Horas)")
        
        fig_line = go.Figure()
        
        # Línea 1: Días Totales de Resolución
        fig_line.add_trace(go.Scatter(
            x=df_group['Fecha_Dia'],
            y=df_group['Dias_Total'],
            mode='lines+markers',
            name='Días Totales de Resolución',
            line=dict(color='#4285F4', width=3, shape='spline'),
            marker=dict(size=8)
        ))

        # Línea 2: Días Carga / Impresión
        fig_line.add_trace(go.Scatter(
            x=df_group['Fecha_Dia'],
            y=df_group['Dias_Imp'],
            mode='lines+markers',
            name='Días Carga a Impresión',
            line=dict(color='#F2994A', width=3, shape='spline'),
            marker=dict(size=8)
        ))

        # Línea 3: Días Entrega en Puesto
        fig_line.add_trace(go.Scatter(
            x=df_group['Fecha_Dia'],
            y=df_group['Dias_SAP'],
            mode='lines+markers',
            name='Días Carga en SAP',
            line=dict(color='#BB6BD9', width=3, shape='spline'),
            marker=dict(size=8)
        ))

        fig_line.update_layout(
            xaxis_title="Fecha de Solicitud",
            yaxis_title="Días Transcurridos",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(t=30, b=20, l=10, r=10),
            height=380
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("💡 A medida que Logística complete las tareas en el Tracker, se trazará aquí el gráfico evolutivo de tiempos de respuesta.")
else:
    st.info("Aún no hay registros en el Tracker Logístico para mostrar tendencias temporales.")