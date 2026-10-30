import hashlib
import bcrypt
import re
from src.database.connection import get_connection

def es_email_valido(email: str) -> bool:
    """Valida que el texto tenga una estructura de correo electrónico válida (ejemplo@dominio.com)."""
    patron = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(patron, email.strip().lower()))

def verificar_password(password_plana: str, pass_db: str) -> bool:
    """Verifica la contraseña contra Bcrypt (Supabase) o SHA-256."""
    if not pass_db:
        return False
        
    # Si la clave en BD es hash Bcrypt ($2a$, $2b$, $2y$)
    if pass_db.startswith("$2"):
        try:
            return bcrypt.checkpw(password_plana.encode('utf-8'), pass_db.encode('utf-8'))
        except Exception:
            return False
            
    # Si es hash SHA-256
    hash_sha = hashlib.sha256(password_plana.encode('utf-8')).hexdigest()
    return hash_sha == pass_db

def hash_password(password: str) -> str:
    """Genera hash Bcrypt estándar para nuevos usuarios."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def autenticar_usuario(email: str, password: str):
    email_clean = email.strip().lower()
    pass_clean = password.strip()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    is_pg = "psycopg2" in str(type(conn))
    param = "%s" if is_pg else "?"
    
    query = f"SELECT email, password_hash, rol FROM usuarios WHERE LOWER(TRIM(email)) = {param}"
    cursor.execute(query, (email_clean,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        # Extraer campos de la BD
        email_db = row["email"]
        pass_db = row["password_hash"]
        rol_db = str(row["rol"])
        
        # Validar la contraseña
        if verificar_password(pass_clean, pass_db):
            return {"email": email_db, "rol": rol_db}, None
            
    return None, "Correo o contraseña incorrectos."

def registrar_usuario(email: str, password: str):
    email_clean = email.strip().lower()
    pass_clean = password.strip()
    
    # Validación estándar de formato de correo (sin restringir dominio)
    if not es_email_valido(email_clean):
        return False, "Por favor ingrese un correo electrónico válido."
        
    conn = get_connection()
    cursor = conn.cursor()
    
    is_pg = "psycopg2" in str(type(conn))
    param = "%s" if is_pg else "?"
    
    cursor.execute(f"SELECT id FROM usuarios WHERE LOWER(TRIM(email)) = {param}", (email_clean,))
    if cursor.fetchone():
        conn.close()
        return False, "El usuario ya se encuentra registrado. Inicie sesión directamente."
    
    pass_hash = hash_password(pass_clean)
    
    # Todo usuario nuevo registrado desde la app asumirá el rol restrictivo 'Consulta'
    rol_asignado = "CONSULTA" if is_pg else "Consulta"
    
    try:
        if is_pg:
            query_insert = f"INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES ({param}, {param}, {param}::rolusuario, CURRENT_TIMESTAMP)"
        else:
            query_insert = f"INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES ({param}, {param}, {param}, datetime('now'))"
            
        cursor.execute(query_insert, (email_clean, pass_hash, rol_asignado))
        conn.commit()
        conn.close()
        return True, "Usuario registrado exitosamente."
    except Exception as e:
        conn.close()
        return False, f"Error al registrar usuario: {str(e)}"