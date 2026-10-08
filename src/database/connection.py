import os
from contextlib import contextmanager
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.database.models import Base

def get_database_url():
    url = None
    # 1. Intentar obtener desde los Secrets de Streamlit Cloud
    try:
        url = st.secrets.get("DATABASE_URL")
    except Exception:
        pass

    # 2. Si no existe en secrets, buscar en el entorno local (variables de sistema o .env)
    if not url:
        url = os.getenv("DATABASE_URL", "sqlite:///kanban_crucianelli.db")

    # 3. Corregir el prefijo para SQLAlchemy + psycopg3 si la URL viene de Supabase
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    return url

DATABASE_URL = get_database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db_session():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()