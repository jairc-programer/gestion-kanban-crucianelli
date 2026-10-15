import hashlib
from src.database.connection import get_connection

def hash_password(password: str) -> str:
    """Genera un hash SHA-256 seguro para la contraseña."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def autenticar_usuario(email: str, password: str):
    """Autentica un usuario contra PostgreSQL (Supabase) o SQLite."""
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Detectar si estamos usando PostgreSQL (psycopg2) o SQLite
    is_pg = "psycopg2" in str(type(conn))
    param = "%s" if is_pg else "?"
    
    query = f"SELECT email, rol FROM usuarios WHERE LOWER(email) = {param} AND password_hash = {param}"
    
    cursor.execute(query, (email_clean, pass_hash))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {"email": row["email"], "rol": row["rol"]}, None
    
    return None, "Correo o contraseña incorrectos."

def registrar_usuario(email: str, password: str):
    """Registra un nuevo usuario respetando los comodines del motor activo."""
    email_clean = email.strip().lower()
    pass_hash = hash_password(password.strip())
    
    if not email_clean.endswith("@crucianelli.com"):
        return False, "Debe utilizar un correo corporativo (@crucianelli.com)."
        
    conn = get_connection()
    cursor = conn.cursor()
    
    is_pg = "psycopg2" in str(type(conn))
    param = "%s" if is_pg else "?"
    
    cursor.execute(f"SELECT id FROM usuarios WHERE LOWER(email) = {param}", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return False, "El usuario ya se encuentra registrado. Inicie sesión directamente."
    
    rol_asignado = "Consulta"
    
    try:
        if is_pg:
            query_insert = f"INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES ({param}, {param}, {param}, CURRENT_TIMESTAMP)"
        else:
            query_insert = f"INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES ({param}, {param}, {param}, datetime('now'))"
            
        cursor.execute(query_insert, (email_clean, pass_hash, rol_asignado))
        conn.commit()
        conn.close()
        return True, "Usuario registrado exitosamente con rol Consulta."
    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {str(e)}"