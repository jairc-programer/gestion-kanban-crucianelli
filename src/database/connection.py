import os
import sqlite3
import hashlib
import streamlit as st
from sqlalchemy import create_engine

DB_PATH = "kanban_crucianelli.db"

def get_db_url():
    # Intenta obtener la URL de Supabase desde Secrets de Streamlit
    if "postgres" in st.secrets and "url" in st.secrets["postgres"]:
        url = st.secrets["postgres"]["url"]
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return f"sqlite:///{DB_PATH}"

def get_engine():
    db_url = get_db_url()
    if "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url)

def get_connection():
    db_url = get_db_url()
    if "postgresql" in db_url:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        # Extraer conexión directa para compatibilidad
        clean_url = db_url.replace("postgresql://", "")
        user_pass, host_port_db = clean_url.split("@")
        user, password = user_pass.split(":")
        host_port, dbname = host_port_db.split("/")
        host = host_port.split(":")[0]
        port = host_port.split(":")[1] if ":" in host_port else "5432"
        
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            cursor_factory=RealDictCursor
        )
        return conn
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    # Con el esquema ya creado en Supabase, aseguramos la siembra de usuarios iniciales
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
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
            # Compatible con sintaxis PostgreSQL y SQLite
            cursor.execute("SELECT id FROM usuarios WHERE LOWER(email) = %s" if "psycopg2" in str(type(conn)) else "SELECT id FROM usuarios WHERE LOWER(email) = ?", (email_clean,))
            if not cursor.fetchone():
                query_insert = "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)" if "psycopg2" in str(type(conn)) else "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (?, ?, ?, datetime('now'))"
                cursor.execute(query_insert, (email_clean, pass_hash_default, rol))
                
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error en init_db:", e)