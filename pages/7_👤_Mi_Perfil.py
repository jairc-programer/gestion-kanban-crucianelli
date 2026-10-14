import streamlit as st
import pandas as pd
import os
from utils.style import aplicar_estilo_enterprise

# Aplicar estilo visual Enterprise (Modo Oscuro Suave)
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

usr_email = st.session_state['usuario']['email']
usr_rol = st.session_state['usuario']['rol']

LOG_FILE = "historial_cambios.csv"
TRACKER_FILE = "tracker_ejecucion.csv"

st.subheader("👤 Mi Perfil de Usuario")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Usuario:** `{usr_email}`")
    with col2:
        st.markdown(f"**Rol Asignado:** `{usr_rol}`")

# --- SECCIÓN EXCLUSIVA DE ADMINISTRADOR ---
if usr_email.lower().strip() == "jairc@crucianelli.com":
    st.markdown("---")
    st.markdown("### ⚙️ Mantenimiento de Vista / Tracker (Exclusivo)")
    st.warning("⚠️ **Zona de Mantenimiento:** Esta sección solo es visible para tu usuario (`jairc@crucianelli.com`).")
    
    with st.expander("🧹 Limpiar Vista de Tracker Logístico y Auditoría"):
        st.write("Esta acción vacía la vista actual de:")
        st.write("1. El **Historial de Auditoría** (`historial_cambios.csv`).")
        st.write("2. Las tareas del **Tracker Logístico** (`tracker_ejecucion.csv`).")
        st.info("ℹ️ **Importante:** Las modificaciones, datos creados y cambios en la base `TablaZ.xlsx` NO se borran ni se ven modificados.")
        
        confirmacion = st.checkbox("Entiendo que limpia la vista de tareas y auditoría", key="chk_reset_confirm")
        
        if st.button("🧹 Limpiar Registros de Vista", type="primary", disabled=not confirmacion):
            # 1. Vaciar historial de cambios
            df_log_clean = pd.DataFrame(columns=['Fecha y Hora', 'Usuario', 'Acción', 'Código K', 'Material', 'Detalle de Cambios'])
            df_log_clean.to_csv(LOG_FILE, index=False)
            
            # 2. Vaciar tracker de ejecución
            df_trk_clean = pd.DataFrame(columns=[
                'Fecha Solicitud', 'Usuario Solicitante', 'Tipo de Acción', 'Código K', 'Material',
                'Almacén Origen', 'Puesto Destino', 'Detalle', 'Estado Logístico',
                'Estado SAP', 'Fecha SAP', 'Usuario SAP',
                'Estado Impresion', 'Fecha Impresion', 'Usuario Impresion',
                'Estado Puesto', 'Fecha Puesto', 'Usuario Puesto',
                'Fecha Ejecución Logística', 'Usuario Logística'
            ])
            df_trk_clean.to_csv(TRACKER_FILE, index=False)
            
            st.success("✅ Vista de Auditoría y Tracker Logístico limpiada correctamente.")
            st.rerun()