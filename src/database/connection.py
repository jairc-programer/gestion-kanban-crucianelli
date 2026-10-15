import sqlite3
import os

DB_PATH = "kanban_crucianelli.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL,
        fecha_creacion TEXT
    )
    """)
    
    # Tabla Principal de Kanbans
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
    
    # Tabla de Historial de Auditoría
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

    # Tabla de Tracker Logístico
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
    
    conn.commit()
    conn.close()