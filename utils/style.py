import streamlit as st

def aplicar_estilo_enterprise():
    st.markdown("""
    <style>
    /* Fondo principal y tipografía general */
    .stApp {
        background-color: #121418;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Barra lateral estilo Enterprise */
    section[data-testid="stSidebar"] {
        background-color: #1A1D24 !important;
        border-right: 1px solid #2A2F3D;
    }

    /* Encabezados y títulos */
    h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }

    /* Tarjetas y Contenedores */
    div[data-testid="stExpander"], div.stCard, div[data-testid="stForm"] {
        background-color: #1A1D24 !important;
        border: 1px solid #2A2F3D !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* Botones primarios (Crucianelli Brand) */
    button[kind="primary"] {
        background-color: #D62828 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out;
    }
    button[kind="primary"]:hover {
        background-color: #E63946 !important;
        box-shadow: 0 0 10px rgba(230, 57, 70, 0.4);
    }

    /* Campos de entrada (Inputs y Selects) */
    div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #222630 !important;
        border-radius: 6px !important;
        border: 1px solid #323846 !important;
    }
    input {
        color: #F8FAFC !important;
    }

    /* Tablas estilizadas */
    div[data-testid="stDataFrame"] {
        background-color: #1A1D24;
        border: 1px solid #2A2F3D;
        border-radius: 8px;
    }

    /* Notificaciones Toast y Alertas */
    div[data-testid="stToast"] {
        background-color: #222630 !important;
        color: #F8FAFC !important;
        border: 1px solid #323846 !important;
    }
    </style>
    """, unsafe_allow_html=True)