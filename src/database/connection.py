import os
import sqlite3
import hashlib
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

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

@contextmanager
def get_db_session():
    """Provee un contexto de sesión transaccional de SQLAlchemy."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

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

        # Crear Tabla Usuarios
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

        conn.commit()
        conn.close()
    except Exception as e:
        print("Error en init_db:", e)