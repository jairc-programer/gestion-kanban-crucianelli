import streamlit as st

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