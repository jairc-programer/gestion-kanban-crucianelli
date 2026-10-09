import streamlit as st

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

usr = st.session_state['usuario']

st.subheader("👤 Perfil de Usuario")
st.write(f"**Correo Corporativo:** {usr['email']}")
st.write(f"**Rol Asignado:** {usr['rol']}")