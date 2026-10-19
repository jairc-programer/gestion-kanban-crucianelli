import streamlit as st
from datetime import datetime
import pytz
import pandas as pd

# Zona horaria oficial para Armstrong, Santa Fe, Argentina (UTC-3)
ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

def obtener_ahora_arg() -> datetime:
    """Retorna el objeto datetime actual con la zona horaria oficial de Argentina (UTC-3)."""
    return datetime.now(ARG_TZ)

def formatear_fecha_arg(val) -> str:
    """
    Convierte cualquier fecha de la BD (incluso guardada en UTC)
    a la hora local de Argentina en formato limpio 'YYYY-MM-DD HH:MM:SS'.
    """
    if not val or str(val).strip() in ['-', '', 'nan', 'None', 'NaT']:
        return "-"
    try:
        dt = pd.to_datetime(val)
        if dt.tzinfo is None:
            # Si no tiene zona horaria asignada, se asume UTC de la nube y se convierte a UTC-3
            dt = pytz.utc.localize(dt).astimezone(ARG_TZ)
        else:
            dt = dt.astimezone(ARG_TZ)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        # Respaldo limpio en caso de fallo
        return str(val).split('.')[0]

def aplicar_estilo_enterprise():
    st.markdown("""
    <style>
    /* Fondo principal suave y visible */
    .stApp {
        background-color: #161920 !important;
        color: #E2E8F0 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Contenedor del contenido principal */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Barra lateral */
    section[data-testid="stSidebar"] {
        background-color: #1E222B !important;
        border-right: 1px solid #2B303C !important;
    }

    /* Títulos y textos */
    h1, h2, h3, h4, h5, h6, p, label, span {
        color: #F8FAFC !important;
    }

    /* Expander y Cards */
    div[data-testid="stExpander"] {
        background-color: #1E222B !important;
        border: 1px solid #2B303C !important;
        border-radius: 8px !important;
    }

    /* Botones primarios */
    button[kind="primary"] {
        background-color: #D62828 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
    }
    button[kind="primary"]:hover {
        background-color: #E63946 !important;
    }

    /* Inputs y Selects */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #252A34 !important;
        border-radius: 6px !important;
        border: 1px solid #323846 !important;
    }

    /* Tablas */
    div[data-testid="stDataFrame"] {
        background-color: #1E222B !important;
        border: 1px solid #2B303C !important;
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)