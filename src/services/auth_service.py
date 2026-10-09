import bcrypt
from sqlalchemy.orm import Session
from src.database.models import Usuario, RolUsuario
from src.database.connection import get_db_session

# Lista actualizada de roles asignados por correo
ROLES_PREDEFINIDOS = {
    # Procesos
    "jairc@crucianelli.com": RolUsuario.PROCESOS,
    "mmagarello@crucianelli.com": RolUsuario.PROCESOS,
    "mcabral@crucianelli.com": RolUsuario.PROCESOS,
    "tabrate@crucianelli.com": RolUsuario.PROCESOS,
    "gtuninetti@crucianelli.com": RolUsuario.PROCESOS,
    # Logística
    "ileon@crucianelli.com": RolUsuario.LOGISTICA,
    "recepcion3@crucianelli.com": RolUsuario.LOGISTICA,
    "gfianchini@crucianelli.com": RolUsuario.LOGISTICA,
}

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def autenticar_usuario(email: str, password_plana: str):
    email_norm = email.strip().lower()
    if not email_norm.endswith("@crucianelli.com"):
        return None, "El correo debe pertenecer al dominio @crucianelli.com."

    with get_db_session() as db:
        usr = db.query(Usuario).filter(Usuario.email == email_norm).first()
        if not usr:
            return None, "Usuario no registrado."
        
        if not verify_password(password_plana, usr.password_hash):
            return None, "Contraseña incorrecta."
        
        # Se extrae el rol como cadena dentro de la sesión activa para evitar DetachedInstanceError
        rol_valor = usr.rol.value if hasattr(usr.rol, 'value') else str(usr.rol)
        email_valor = usr.email

    # Creamos un objeto simple desconectado de la ORM
    class UsuarioDTO:
        def __init__(self, email, rol_str):
            self.email = email
            self.rol = self._RolWrapper(rol_str)
        
        class _RolWrapper:
            def __init__(self, val):
                self.value = val

    return UsuarioDTO(email_valor, rol_valor), None

def registrar_usuario(email: str, password_plana: str):
    email_norm = email.strip().lower()
    if not email_norm.endswith("@crucianelli.com"):
        return False, "El correo debe pertenecer al dominio @crucianelli.com."

    with get_db_session() as db:
        if db.query(Usuario).filter(Usuario.email == email_norm).first():
            return False, "El usuario ya se encuentra registrado."
        
        # Asigna el rol definido o CONSULTA por defecto
        rol_asig = ROLES_PREDEFINIDOS.get(email_norm, RolUsuario.CONSULTA)
        nuevo_usuario = Usuario(
            email=email_norm,
            password_hash=hash_password(password_plana),
            rol=rol_asig
        )
        db.add(nuevo_usuario)
    return True, f"Usuario registrado exitosamente con rol {rol_asig.value}."