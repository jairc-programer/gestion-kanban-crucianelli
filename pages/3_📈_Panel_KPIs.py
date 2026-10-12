import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📈 Panel de Indicadores Clave (KPIs)")

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"
TRACKER_FILE = "tracker_ejecucion.csv"

# --- 1. CARGA Y PREPARACIÓN DE DATOS BASE ---
if os.path.exists(DB_FILE):
    df_kb = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
    
    # Inferir Tipo Kanban si no existe
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

    m1, m2, m3, m4 = st.columns(4)
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
            color_discrete_sequence=px.colors.qualitative.Blues_r
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

# --- 2. ANÁLISIS DE TIEMPOS Y LEAD TIME LOGÍSTICO ---
st.markdown("---")
st.markdown("### ⏱️ Tiempos de Respuesta de Ejecución Logística")

if os.path.exists(TRACKER_FILE):
    df_trk = pd.read_csv(TRACKER_FILE, dtype=str)
    
    # Calcular horas transcurridas
    def calcular_horas(row, col_fin):
        f_sol = row.get('Fecha Solicitud')
        f_ej = row.get(col_fin)
        if pd.notna(f_sol) and pd.notna(f_ej) and f_sol != '-' and f_ej != '-':
            try:
                dt_sol = datetime.strptime(f_sol, "%Y-%m-%d %H:%M:%S")
                dt_ej = datetime.strptime(f_ej, "%Y-%m-%d %H:%M:%S")
                diff = (dt_ej - dt_sol).total_seconds() / 3600.0
                return round(max(diff, 0.01), 2)
            except Exception:
                return np.nan
        return np.nan

    df_trk['Horas SAP'] = df_trk.apply(lambda r: calcular_horas(r, 'Fecha SAP'), axis=1)
    df_trk['Horas Impresión'] = df_trk.apply(lambda r: calcular_horas(r, 'Fecha Impresion'), axis=1)
    df_trk['Horas Puesto'] = df_trk.apply(lambda r: calcular_horas(r, 'Fecha Puesto'), axis=1)

    t_sap_avg = df_trk['Horas SAP'].mean()
    t_imp_avg = df_trk['Horas Impresión'].mean()
    t_pst_avg = df_trk['Horas Puesto'].mean()

    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
    col_kpi1.metric("💻 Promedio Carga SAP", f"{t_sap_avg:.1f} hs" if pd.notna(t_sap_avg) else "Sin datos")
    col_kpi2.metric("🖨️ Promedio Impresión/Etiqueta", f"{t_imp_avg:.1f} hs" if pd.notna(t_imp_avg) else "Sin datos")
    col_kpi3.metric("📍 Promedio Llevado a Puesto", f"{t_pst_avg:.1f} hs" if pd.notna(t_pst_avg) else "Sin datos")

    # Unificar tiempos finalizados para el histograma
    tiempos_data = []
    for idx, r in df_trk.iterrows():
        if pd.notna(r['Horas SAP']):
            tiempos_data.append({'Etapa': 'Carga en SAP', 'Horas': r['Horas SAP'], 'Código K': r.get('Código K')})
        if pd.notna(r['Horas Impresión']):
            tiempos_data.append({'Etapa': 'Impresión / Etiqueta', 'Horas': r['Horas Impresión'], 'Código K': r.get('Código K')})
        if pd.notna(r['Horas Puesto']):
            tiempos_data.append({'Etapa': 'Llevado a Puesto Destino', 'Horas': r['Horas Puesto'], 'Código K': r.get('Código K')})

    df_tiempos = pd.DataFrame(tiempos_data)

    if not df_tiempos.empty:
        st.markdown("##### 📊 Histograma de Distribución de Tiempos de Respuesta (en Horas)")
        fig_hist = px.histogram(
            df_tiempos, 
            x="Horas", 
            color="Etapa", 
            barmode="overlay",
            nbins=20,
            opacity=0.75,
            color_discrete_map={
                'Carga en SAP': '#1f77b4',
                'Impresión / Etiqueta': '#ff7f0e',
                'Llevado a Puesto Destino': '#2ca02c'
            }
        )
        fig_hist.update_layout(
            xaxis_title="Tiempo Transcurrido (Horas)", 
            yaxis_title="Cantidad de Tareas",
            margin=dict(t=20, b=20, l=10, r=10),
            height=380
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("💡 A medida que el equipo de Logística complete los checks en el Tracker, se generarán aquí las métricas y gráficos de tiempo de respuesta.")
else:
    st.info("Aún no hay registros en el Tracker Logístico para analizar tiempos de respuesta.")