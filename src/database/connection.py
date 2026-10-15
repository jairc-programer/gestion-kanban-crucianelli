import sqlite3
import hashlib

DB_PATH = "kanban_crucianelli.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL,
        fecha_creacion TEXT
    )
    """)
    
    # 2. Tabla Principal de Kanbans
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kanbans (
        codigo_k TEXT PRIMARY KEY,
        tipo_etiqueta TEXT,
        tipo_kanban TEXT,
        medio TEXT,
        material TEXT NOT NULL,
        centro TEXT,
        almacen_origen TEXT,
        almacen_destino TEXT,
        puesto_origen TEXT,
        puesto_destino TEXT NOT NULL,
        cantidad_reposicion REAL,
        unidad_reposicion TEXT,
        cantidad_punto_pedido REAL,
        dias_abastecimiento INTEGER,
        fecha_modificacion TEXT,
        usuario_modificacion TEXT
    )
    """)
    
    # 3. Tabla de Auditoría
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auditoria (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_hora TEXT,
        usuario TEXT,
        accion TEXT,
        codigo_k TEXT,
        material TEXT,
        detalle TEXT
    )
    """)

    # 4. Tabla de Tracker Logístico
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracker (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha_solicitud TEXT,
        usuario_solicitante TEXT,
        tipo_accion TEXT,
        codigo_k TEXT,
        material TEXT,
        almacen_origen TEXT,
        puesto_destino TEXT,
        detalle TEXT,
        estado_logistico TEXT DEFAULT 'PENDIENTE',
        estado_sap TEXT DEFAULT 'PENDIENTE',
        fecha_sap TEXT DEFAULT '-',
        usuario_sap TEXT DEFAULT '-',
        estado_impresion TEXT DEFAULT 'PENDIENTE',
        fecha_impresion TEXT DEFAULT '-',
        usuario_impresion TEXT DEFAULT '-',
        estado_puesto TEXT DEFAULT 'PENDIENTE',
        fecha_puesto TEXT DEFAULT '-',
        usuario_puesto TEXT DEFAULT '-',
        fecha_ejecucion TEXT DEFAULT '-',
        usuario_logistica TEXT DEFAULT '-'
    )
    """)

    # Lista de usuarios iniciales autorizados
    usuarios_semilla = [
        # Equipo PROCESOS
        ("jairc@crucianelli.com", "Procesos"),
        ("mmagarello@crucianelli.com", "Procesos"),
        ("tabrate@crucianelli.com", "Procesos"),
        ("abacelli@crucianelli.com", "Procesos"),
        ("gtuninetti@crucianelli.com", "Procesos"),
        ("llatanzi@crucianelli.com", "Procesos"),
        ("mcabral@crucianelli.com", "Procesos"),
        
        # Equipo LOGÍSTICA
        ("ileon@crucianelli.com", "Logistica"),
        ("gfianchini@crucianelli.com", "Logistica")
    ]
    
    pass_hash_default = hash_password("Crucianelli2026!")
    
    for email, rol in usuarios_semilla:
        email_clean = email.lower().strip()
        cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = ?", (email_clean,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (?, ?, ?, datetime('now'))",
                (email_clean, pass_hash_default, rol)
            )
            
    conn.commit()
    conn.close()