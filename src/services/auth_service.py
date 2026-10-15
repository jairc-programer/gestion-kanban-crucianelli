import hashlib
from src.database.connection import get_connection

def hash_password(password: str) -> str:
    """Genera un hash SHA-256 seguro para la contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def autenticar_usuario(email: str, password: str):
    """Autentica un usuario contra la base de datos SQLite nativa."""
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Buscar usuario por email y contraseña hash
    cursor.execute(
        "SELECT email, rol FROM usuarios WHERE LOWER(email) = ? AND password_hash = ?",
        (email_clean, pass_hash)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Devuelve diccionario con los datos del usuario si coincide
        return {"email": row["email"], "rol": row["rol"]}, None
    
    return None, "Correo o contraseña incorrectos."

def registrar_usuario(email: str, password: str, rol: str = "Procesos"):
    """Registra un nuevo usuario en la base de datos SQLite."""
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())
    
    if "@crucianelli.com" not in email_clean:
        return False, "Debe utilizar un correo corporativo (@crucianelli.com)."
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe
    cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = ?", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return False, "El usuario ya se encuentra registrado."
        
    try:
        cursor.execute(
            "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (?, ?, ?, datetime('now'))",
            (email_clean, pass_hash, rol)
        )
        conn.commit()
        conn.close()
        return True, "Usuario registrado exitosamente."
    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {str(e)}"