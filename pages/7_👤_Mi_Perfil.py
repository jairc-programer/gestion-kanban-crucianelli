import streamlit as st
import pandas as pd
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_auditoria_df, obtener_tracker_df
from src.database.connection import get_db_session
from src.database.models import Usuario, LogAuditoria, TrackerSolicitud

# Aplicar estilo visual Enterprise
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

usr_email = st.session_state['usuario']['email']
usr_rol = st.session_state['usuario']['rol']

st.subheader("👤 Mi Perfil de Usuario")

# --- 1. FICHA TÉCNICA DEL USUARIO ---
with st.container(border=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Usuario:** `{usr_email}`")
    with col2:
        st.markdown(f"**Rol Asignado:** `{usr_rol}`")
    with col3:
        st.markdown("**Estado:** `🟢 Activo`")

# --- 2. CAMBIO DE CONTRASEÑA ---
st.markdown("---")
st.markdown("### 🔒 Seguridad y Contraseña")

with st.expander("🔑 Cambiar mi contraseña de acceso"):
    with st.form("form_cambiar_pass"):
        pass_actual = st.text_input("Contraseña Actual:", type="password")
        pass_nueva = st.text_input("Nueva Contraseña:", type="password")
        pass_confirm = st.text_input("Confirmar Nueva Contraseña:", type="password")
        
        btn_cambiar_pass = st.form_submit_button("💾 Actualizar Contraseña", type="primary")
        
        if btn_cambiar_pass:
            if not pass_actual or not pass_nueva or not pass_confirm:
                st.error("❌ Todos los campos son obligatorios.")
            elif pass_nueva != pass_confirm:
                st.error("❌ La nueva contraseña y su confirmación no coinciden.")
            elif len(pass_nueva) < 6:
                st.error("❌ La nueva contraseña debe tener al menos 6 caracteres.")
            else:
                with get_db_session() as db:
                    u = db.query(Usuario).filter(Usuario.email.ilike(usr_email.strip())).first()
                    if u and u.password == pass_actual:
                        u.password = pass_nueva
                        db.commit()
                        st.success("✅ ¡Contraseña actualizada exitosamente!")
                        st.toast("✅ Contraseña cambiada", icon="🔒")
                    else:
                        st.error("❌ La contraseña actual ingresada es incorrecta.")

# --- 3. MI HISTORIAL DE ACTIVIDAD (SUPABASE) ---
st.markdown("---")
st.markdown("### 📜 Mi Historial de Operaciones")

df_aud = obtener_auditoria_df()

if not df_aud.empty:
    df_mi_aud = df_aud[df_aud['Usuario'].fillna('').astype(str).str.lower() == usr_email.lower()]
    
    m1, m2 = st.columns(2)
    tot_ops = len(df_mi_aud)
    ult_fecha = df_mi_aud.iloc[0]['Fecha y Hora'] if not df_mi_aud.empty else "Sin actividad registrada"
    
    m1.metric("📊 Mis Operaciones Registradas", tot_ops)
    m2.metric("⏱️ Última Acción Realizada", str(ult_fecha))

    if not df_mi_aud.empty:
        st.caption("Últimos movimientos realizados en el sistema:")
        st.dataframe(df_mi_aud.head(10), use_container_width=True)
    else:
        st.info("ℹ️ Aún no registraste acciones de creación, modificación o eliminación.")
else:
    st.info("ℹ️ No hay registros generales de auditoría en la base de datos.")

# --- 4. SECCIÓN EXCLUSIVA DE ADMINISTRADOR ---
if usr_email.lower().strip() == "jairc@crucianelli.com":
    st.markdown("---")
    st.markdown("### ⚙️ Mantenimiento de Tablas Supabase (Exclusivo)")
    st.warning("⚠️ **Zona de Mantenimiento:** Esta sección solo es visible para tu usuario (`jairc@crucianelli.com`).")
    
    with st.expander("🧹 Limpiar Registros de Auditoría o Tracker Logístico"):
        st.write("Esta acción borra los registros de vista en Supabase para las siguientes tablas:")
        st.write("1. **Historial de Auditoría** (`logs_auditoria`).")
        st.write("2. Solicitudes del **Tracker Logístico** (`tracker_solicitudes`).")
        st.info("ℹ️ **Importante:** La tabla máster de **Kanbans** NO se ve modificada ni alterada.")
        
        confirmacion = st.checkbox("Entiendo que esto eliminará el historial de vista en Supabase", key="chk_reset_confirm_db")
        
        col_b1, col_b2 = st.columns(2)
        with col_b1:
            if st.button("🧹 Limpiar Registro de Auditoría", type="primary", disabled=not confirmacion):
                with get_db_session() as db:
                    db.query(LogAuditoria).delete()
                    db.commit()
                st.success("✅ Historial de auditoría en Supabase limpiado correctamente.")
                st.rerun()

        with col_b2:
            if st.button("🧹 Limpiar Tracker Logístico", type="primary", disabled=not confirmacion):
                with get_db_session() as db:
                    db.query(TrackerSolicitud).delete()
                    db.commit()
                st.success("✅ Tareas del Tracker Logístico en Supabase limpiadas correctamente.")
                st.rerun()