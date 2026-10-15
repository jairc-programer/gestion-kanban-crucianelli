import hashlib
from src.database.connection import get_connection

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def autenticar_usuario(email: str, password: str):
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT email, rol FROM usuarios WHERE LOWER(email) = ? AND password_hash = ?",
        (email_clean, pass_hash)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"email": row["email"], "rol": row["rol"]}, None
    
    return None, "Correo o contraseña incorrectos."

def registrar_usuario(email: str, password: str):
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())
    
    if not email_clean.endswith("@crucianelli.com"):
        return False, "Debe utilizar un correo corporativo (@crucianelli.com)."
        
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return False, "El usuario ya se encuentra registrado. Inicie sesión directamente."
    
    # Asignación de rol por defecto para nuevos registros: Consulta
    rol_asignado = "Consulta"
    
    try:
        cursor.execute(
            "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (?, ?, ?, datetime('now'))",
            (email_clean, pass_hash, rol_asignado)
        )
        conn.commit()
        conn.close()
        return True, "Usuario registrado exitosamente con rol Consulta."
    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {str(e)}"