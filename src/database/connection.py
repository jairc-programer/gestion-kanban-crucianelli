import os
import sqlite3
import hashlib
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

DB_PATH = "kanban_crucianelli.db"

def get_db_url():
    """Obtiene la URL de conexión desde Secrets de Streamlit Cloud o usa SQLite local."""
    if "postgres" in st.secrets and "url" in st.secrets["postgres"]:
        url = st.secrets["postgres"]["url"]
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return f"sqlite:///{DB_PATH}"

def get_engine():
    """Retorna un motor de SQLAlchemy configurado para el motor activo."""
    db_url = get_db_url()
    if "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url)

def get_connection():
    """Abre y retorna una conexión directa a PostgreSQL (psycopg2) o SQLite."""
    db_url = get_db_url()
    if "postgresql" in db_url:
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def hash_password(password: str) -> str:
    """Genera hash SHA-256 para contraseñas."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    """Inicializa la estructura de tablas y siembra los usuarios autorizados."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        is_pg = "psycopg2" in str(type(conn))
        param = "%s" if is_pg else "?"

        # 1. Crear Tabla Usuarios si no existe
        if is_pg:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                rol VARCHAR(50) NOT NULL,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
        else:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                rol TEXT NOT NULL,
                fecha_creacion TEXT
            );
            """)

        # 2. Siembra de Usuarios Semilla (Procesos y Logística)
        usuarios_semilla = [
            ("jairc@crucianelli.com", "Procesos"),
            ("mmagarello@crucianelli.com", "Procesos"),
            ("tabrate@crucianelli.com", "Procesos"),
            ("abacelli@crucianelli.com", "Procesos"),
            ("gtuninetti@crucianelli.com", "Procesos"),
            ("llatanzi@crucianelli.com", "Procesos"),
            ("mcabral@crucianelli.com", "Procesos"),
            ("ileon@crucianelli.com", "Logistica"),
            ("gfianchini@crucianelli.com", "Logistica")
        ]
        
        pass_hash_default = hash_password("Crucianelli2026!")
        
        for email, rol in usuarios_semilla:
            email_clean = email.lower().strip()
            cursor.execute(f"SELECT id FROM usuarios WHERE LOWER(email) = {param}", (email_clean,))
            if not cursor.fetchone():
                if is_pg:
                    query_insert = f"INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES ({param}, {param}, {param}, CURRENT_TIMESTAMP)"
                else:
                    query_insert = f"INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES ({param}, {param}, {param}, datetime('now'))"
                cursor.execute(query_insert, (email_clean, pass_hash_default, rol))
                
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error en init_db:", e)