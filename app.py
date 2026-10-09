import streamlit as st
from src.database.connection import init_db
from src.services.auth_service import autenticar_usuario, registrar_usuario

st.set_page_config(page_title="Gestor de Kanbans - Crucianelli", layout="wide")

# Inicialización de la base de datos relacional
init_db()

# Inicialización de estado global
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None

# --- CONTROL DE ACCESO Y AUTENTICACIÓN ---
if not st.session_state['usuario']:
    st.title("📦 Sistema de Gestión de Kanbans - Crucianelli")
    
    with st.container(border=True):
        st.subheader("🔐 Acceso al Sistema")
        tab_login, tab_reg = st.tabs(["🔑 Iniciar Sesión", "📝 Registrarse"])
        
        with tab_login:
            with st.form("form_login"):
                email = st.text_input("Correo Corporativo (@crucianelli.com):", key="log_email")
                password = st.text_input("Contraseña:", type="password", key="log_pass")
                btn_login = st.form_submit_button("Ingresar", type="primary", use_container_width=True)
                
                if btn_login:
                    e_clean = email.strip().lower()
                    p_clean = password.strip()
                    usr_data, err = autenticar_usuario(e_clean, p_clean)
                    if err:
                        st.toast(err, icon="❌")
                    else:
                        st.session_state['usuario'] = {
                            "email": usr_data.email,
                            "rol": usr_data.rol.value
                        }
                        st.toast(f"Bienvenido {usr_data.email}", icon="✅")
                        st.rerun()

        with tab_reg:
            with st.form("form_registro"):
                reg_email = st.text_input("Correo Corporativo (@crucianelli.com):", key="reg_email")
                reg_pass1 = st.text_input("Contraseña:", type="password", key="reg_p1")
                reg_pass2 = st.text_input("Confirmar Contraseña:", type="password", key="reg_p2")
                btn_reg = st.form_submit_button("Crear Cuenta", use_container_width=True)
                
                if btn_reg:
                    e_clean = reg_email.strip().lower()
                    p1_clean = reg_pass1.strip()
                    p2_clean = reg_pass2.strip()
                    
                    if not e_clean or not p1_clean or not p2_clean:
                        st.toast("Ingrese un correo y contraseña válidos.", icon="⚠️")
                    elif p1_clean != p2_clean:
                        st.toast("Las contraseñas no coinciden.", icon="⚠️")
                    else:
                        ok, msj = registrar_usuario(e_clean, p1_clean)
                        if ok:
                            st.toast(msj, icon="✅")
                        else:
                            st.toast(msj, icon="❌")
    st.stop()

# --- BARRA SUPERIOR Y ROUTING DE NAVEGACIÓN ---
usr_data = st.session_state['usuario']

with st.container(border=True):
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"### 📦 Gestor de Kanbans | **{usr_data['email']}**")
    with col2:
        st.markdown(f"**Rol:** `{usr_data['rol'].upper()}`")
    with col3:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state['usuario'] = None
            st.rerun()

# Definición de páginas seguras según rol (RBAC)
rol = usr_data['rol']

paginas = []
if rol == "Procesos":
    paginas = [
        st.Page("pages/1_➕_Crear_Kanban.py", title="Crear Kanban", icon="➕"),
        st.Page("pages/2_✏️_Modificar_y_Eliminar.py", title="Modificar/Eliminar", icon="✏️"),
        st.Page("pages/3_📈_Panel_KPIs.py", title="Panel KPIs", icon="📈"),
        st.Page("pages/4_🚚_Tracker_Logistico.py", title="Tracker Logístico", icon="🚚"),
        st.Page("pages/5_📊_Datos_Kanban.py", title="Datos Kanban", icon="📊"),
        st.Page("pages/6_📜_Historial_Auditoria.py", title="Auditoría", icon="📜"),
        st.Page("pages/7_👤_Mi_Perfil.py", title="Mi Perfil", icon="👤")
    ]
elif rol == "Logistica":
    paginas = [
        st.Page("pages/4_🚚_Tracker_Logistico.py", title="Tracker Logístico", icon="🚚"),
        st.Page("pages/3_📈_Panel_KPIs.py", title="Panel KPIs", icon="📈"),
        st.Page("pages/5_📊_Datos_Kanban.py", title="Datos Kanban", icon="📊"),
        st.Page("pages/6_📜_Historial_Auditoria.py", title="Auditoría", icon="📜"),
        st.Page("pages/7_👤_Mi_Perfil.py", title="Mi Perfil", icon="👤")
    ]
else: # Consulta
    paginas = [
        st.Page("pages/3_📈_Panel_KPIs.py", title="Panel KPIs", icon="📈"),
        st.Page("pages/5_📊_Datos_Kanban.py", title="Datos Kanban", icon="📊"),
        st.Page("pages/7_👤_Mi_Perfil.py", title="Mi Perfil", icon="👤")
    ]

# Ejecutar el enrutador de páginas
pg = st.navigation(paginas)
pg.run()