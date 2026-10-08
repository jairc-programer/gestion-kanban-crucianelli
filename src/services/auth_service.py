import bcrypt
from sqlalchemy.orm import Session
from src.database.models import Usuario, RolUsuario
from src.database.connection import get_db_session

ROLES_PREDEFINIDOS = {
    "jairc@crucianelli.com": RolUsuario.PROCESOS,
    "mmagarello@crucianelli.com": RolUsuario.PROCESOS,
    "mlopez@crucianelli.com": RolUsuario.LOGISTICA,
    "recepcion3@crucianelli.com": RolUsuario.LOGISTICA,
    "fany@crucianelli.com": RolUsuario.CONSULTA
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
        
        return usr, None

def registrar_usuario(email: str, password_plana: str):
    email_norm = email.strip().lower()
    if not email_norm.endswith("@crucianelli.com"):
        return False, "El correo debe pertenecer al dominio @crucianelli.com."

    with get_db_session() as db:
        if db.query(Usuario).filter(Usuario.email == email_norm).first():
            return False, "El usuario ya se encuentra registrado."
        
        rol_asig = ROLES_PREDEFINIDOS.get(email_norm, RolUsuario.CONSULTA)
        nuevo_usuario = Usuario(
            email=email_norm,
            password_hash=hash_password(password_plana),
            rol=rol_asig
        )
        db.add(nuevo_usuario)
    return True, f"Usuario registrado exitosamente con rol {rol_asig.value}."