import plotly.express as px
import pandas as pd

def formatear_horas_a_tiempo_humano(horas: float) -> str:
    if pd.isna(horas) or horas is None:
        return "N/A"
    
    total_minutos = int(horas * 60)
    dias = total_minutos // (24 * 60)
    horas_rest = (total_minutos % (24 * 60)) // 60
    minutos_rest = total_minutos % 60
    
    partes = []
    if dias > 0: partes.append(f"{dias}d")
    if horas_rest > 0 or dias > 0: partes.append(f"{horas_rest}h")
    partes.append(f"{minutos_rest}m")
    
    return " ".join(partes)

def generar_grafico_tiempos_respuesta(df_t: pd.DataFrame):
    if df_t.empty or 'Fecha_Solicitud' not in df_t.columns:
        return None
        
    df_t['Fecha_Corta'] = pd.to_datetime(df_t['Fecha_Solicitud']).dt.strftime('%Y-%m-%d')
    cols_existentes = [col for col in ['Hs_Solicitud_a_SAP_Imp', 'Hs_Imp_a_AccionFisica', 'Hs_Ciclo_Total'] if col in df_t.columns]
    
    if not cols_existentes:
        return None

    df_prom_diario = df_t.groupby('Fecha_Corta')[cols_existentes].mean().reset_index()
    df_melted = df_prom_diario.melt(
        id_vars=['Fecha_Corta'],
        value_vars=cols_existentes,
        var_name='Etapa',
        value_name='Horas_Promedio'
    )
    
    mapeo_etapas = {
        'Hs_Solicitud_a_SAP_Imp': 'Solicitud ➔ Impresión',
        'Hs_Imp_a_AccionFisica': 'Impresión ➔ Acción Física',
        'Hs_Ciclo_Total': 'Ciclo Completo'
    }
    df_melted['Etapa'] = df_melted['Etapa'].map(mapeo_etapas)
    df_melted['Tiempo_Formateado'] = df_melted['Horas_Promedio'].apply(formatear_horas_a_tiempo_humano)

    fig = px.bar(
        df_melted,
        x='Fecha_Corta',
        y='Horas_Promedio',
        color='Etapa',
        barmode='group',
        template="plotly_dark",
        title="Tiempo Promedio de Respuesta por Fecha",
        hover_data={'Horas_Promedio': ':.2f', 'Tiempo_Formateado': True},
        labels={'Fecha_Corta': 'Fecha', 'Horas_Promedio': 'Horas', 'Tiempo_Formateado': 'Duración'}
    )
    fig.update_layout(height=380, margin=dict(l=20, r=20, t=40, b=20))
    return fig