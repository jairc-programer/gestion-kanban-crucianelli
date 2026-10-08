import streamlit as st
from src.services.kanban_service import eliminar_kanban_seguro

st.title("✏️ Modificar y Eliminar Kanban")

# Verificar sesión activa
if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.warning("Debe iniciar sesión para realizar modificaciones o borrados.")
    st.stop()

usuario_actual = st.session_state['usuario']

st.subheader("🗑️ Zona de Borrado Restringido")
st.caption(f"Usuario activo: **{usuario_actual['email']}** | Rol: **{usuario_actual['rol']}**")

with st.form("form_eliminar_kanban"):
    codigo_k = st.text_input("Ingrese el Código K a eliminar (ej. K00000012)")
    confirmacion = st.checkbox("Confirmo que deseo eliminar este registro de la base de datos de forma permanente.")
    
    submit_borrar = st.form_submit_button("Eliminar Kanban", type="primary")
    
    if submit_borrar:
        if not codigo_k:
            st.error("Debe ingresar un Código K.")
        elif not confirmacion:
            st.warning("Debe marcar la casilla de confirmación.")
        else:
            exito, mensaje = eliminar_kanban_seguro(codigo_k.strip(), usuario_actual['email'])
            if exito:
                st.success(mensaje)
            else:
                st.error(mensaje)