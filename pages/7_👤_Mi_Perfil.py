import streamlit as st
import pandas as pd
import os

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

# --- SECCIÓN EXCLUSIVA DE ADMINISTRADOR / SUPERUSUARIO ---
if usr_email.lower().strip() == "jairc@crucianelli.com":
    st.markdown("---")
    st.markdown("### ⚙️ Administración del Sistema (Exclusivo)")
    st.warning("⚠️ **Zona de Mantenimiento:** Esta sección solo es visible para tu usuario (`jairc@crucianelli.com`).")
    
    with st.expander("🚨 Reiniciar Historial y Tracker (Borrar Pruebas)"):
        st.write("Esta acción borrará de forma permanente:")
        st.write("1. El registro del **Historial de Auditoría** (`historial_cambios.csv`).")
        st.write("2. Todas las solicitudes del **Tracker Logístico** (`tracker_ejecucion.csv`).")
        st.caption("Nota: La base de datos `TablaZ.xlsx` NO se verá afectada.")
        
        confirmacion = st.checkbox("Entiendo que esta acción no se puede deshacer", key="chk_reset_confirm")
        
        if st.button("🔥 Reiniciar Registros de Prueba", type="primary", disabled=not confirmacion):
            # 1. Vaciar o reiniciar historial_cambios.csv
            df_log_clean = pd.DataFrame(columns=['Fecha y Hora', 'Usuario', 'Acción', 'Código K', 'Material', 'Detalle de Cambios'])
            df_log_clean.to_csv(LOG_FILE, index=False)
            
            # 2. Vaciar o reiniciar tracker_ejecucion.csv
            df_trk_clean = pd.DataFrame(columns=[
                'Fecha Solicitud', 'Usuario Solicitante', 'Tipo de Acción', 'Código K', 'Material',
                'Almacén Origen', 'Puesto Destino', 'Detalle', 'Estado Logístico',
                'Estado SAP', 'Fecha SAP', 'Usuario SAP',
                'Estado Impresion', 'Fecha Impresion', 'Usuario Impresion',
                'Estado Puesto', 'Fecha Puesto', 'Usuario Puesto',
                'Fecha Ejecución Logística', 'Usuario Logística'
            ])
            df_trk_clean.to_csv(TRACKER_FILE, index=False)
            
            st.success("✅ Historial de Auditoría y Tracker Logístico reiniciados correctamente.")
            st.rerun()