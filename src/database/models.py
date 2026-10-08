import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Sequence
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class RolUsuario(str, enum.Enum):
    PROCESOS = "Procesos"
    LOGISTICA = "Logistica"
    CONSULTA = "Consulta"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_order=True, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(Enum(RolUsuario), default=RolUsuario.CONSULTA, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

class Kanban(Base):
    __tablename__ = "kanbans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Generación auto-incremental protegida en BD
    numero_etiqueta = Column(String(20), unique=True, nullable=False, index=True)
    tipo_etiqueta = Column(String(10), nullable=False)  # KI / KE
    tipo_kanban = Column(String(20), nullable=False)    # GAVETA / TARJETA
    medio = Column(String(50), nullable=False)
    material = Column(String(50), nullable=False, index=True)
    centro = Column(String(10), default="A110")
    almacen_origen = Column(String(20), nullable=False)
    almacen_destino = Column(String(20), nullable=False)
    puesto_origen = Column(String(50), default="-")
    puesto_destino = Column(String(50), nullable=False, index=True)
    cantidad_reposicion = Column(Float, nullable=False)
    unidad_reposicion = Column(String(10), default="UN")
    cantidad_punto_pedido = Column(Float, nullable=False)
    tiempo_preparacion_dias = Column(Integer, default=1)
    fecha_modificacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_modificacion = Column(String(255), nullable=False)

class TrackerSolicitud(Base):
    __tablename__ = "tracker_solicitudes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_solicitud = Column(String(20), unique=True, nullable=False, index=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow, nullable=False)
    material = Column(String(50), nullable=False)
    codigo_k = Column(String(20), nullable=False)
    tipo_kb = Column(String(10), nullable=False)
    puesto_destino = Column(String(50), nullable=False)
    medio = Column(String(50), nullable=False)
    cambio = Column(String(100), nullable=False)
    accion_requerida = Column(String(100), nullable=False)
    cargado_sap = Column(String(5), default="NO")
    impreso = Column(String(5), default="NO")
    fecha_impresion = Column(DateTime, nullable=True)
    estado_fisico = Column(String(30), default="Pendiente")
    fecha_finalizacion = Column(DateTime, nullable=True)
    observacion = Column(String(255), default="-")
    usuario_procesos = Column(String(255), nullable=False)

class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fecha_hora = Column(DateTime, default=datetime.utcnow, nullable=False)
    accion = Column(String(30), nullable=False)
    codigo_k = Column(String(20), nullable=False)
    material = Column(String(50), nullable=False)
    medio = Column(String(50), nullable=False)
    almacen_destino = Column(String(20), nullable=False)
    puesto_destino = Column(String(50), nullable=False)
    detalle_cambio = Column(String(500), default="-")
    usuario = Column(String(255), nullable=False)