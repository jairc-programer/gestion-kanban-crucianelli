from src.database.connection import get_db_session
from src.database.models import Usuario, RolUsuario
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

email = "mmagarello@crucianelli.com"
password_plana = "mati1234"

with get_db_session() as db:
    usr = db.query(Usuario).filter(Usuario.email == email).first()
    if usr:
        usr.password_hash = hash_password(password_plana)
        usr.rol = RolUsuario.PROCESOS
        print(f"✅ Usuario {email} actualizado con contraseña 'mati1234' y rol PROCESOS.")
    else:
        nuevo_usuario = Usuario(
            email=email,
            password_hash=hash_password(password_plana),
            rol=RolUsuario.PROCESOS
        )
        db.add(nuevo_usuario)
        print(f"✅ Usuario {email} creado exitosamente con rol PROCESOS.")