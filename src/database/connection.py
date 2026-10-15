import os
import sqlite3
import hashlib
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine

DB_PATH = "kanban_crucianelli.db"

def get_db_url():
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
        # Psycopg2 acepta directamente la URL en la conexión por DSN
        return psycopg2.connect(db_url, cursor_factory=RealDictCursor)
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        is_pg = "psycopg2" in str(type(conn))
        param_symbol = "%s" if is_pg else "?"

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
            cursor.execute(f"SELECT id FROM usuarios WHERE LOWER(email) = {param_symbol}", (email_clean,))
            if not cursor.fetchone():
                if is_pg:
                    query_insert = "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (%s, %s, %s, CURRENT_TIMESTAMP)"
                else:
                    query_insert = "INSERT INTO usuarios (email, password_hash, rol, fecha_creacion) VALUES (?, ?, ?, datetime('now'))"
                cursor.execute(query_insert, (email_clean, pass_hash_default, rol))
                
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error en init_db:", e)