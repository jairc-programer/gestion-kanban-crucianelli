import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Kanban, LogAuditoria, TrackerSolicitud, Usuario, RolUsuario
from src.database.connection import get_db_session

def obtener_siguiente_codigo_k_transaccional(db: Session) -> str:
    """Escanea Supabase y obtiene el número K mayor asignado + 1."""
    registros = db.query(Kanban.numero_etiqueta).all()
    
    max_num = 0
    for (k_code,) in registros:
        if k_code:
            match = re.search(r'\d+', str(k_code))
            if match:
                num = int(match.group(0))
                if num > max_num:
                    max_num = num
                    
    siguiente_num = max_num + 1
    return f"K{siguiente_num:08d}"

def crear_nuevo_kanban(datos: dict, usuario_email: str) -> tuple[bool, str]:
    """Crea un nuevo Kanban, registra la auditoría y genera la tarea para Logística."""
    with get_db_session() as db:
        # 1. Validar si ya existe la combinación Material + Puesto Destino
        existente = db.query(Kanban).filter(
            func.lower(Kanban.material) == datos['material'].strip().lower(),
            func.lower(Kanban.puesto_destino) == datos['puesto_destino'].strip().lower()
        ).first()
        
        if existente:
            return False, f"Ya existe el Kanban {existente.numero_etiqueta} asignado al material {datos['material']} en el puesto {datos['puesto_destino']}."
        
        # 2. Generar el código K correlativo único basado en el máximo existente
        codigo_k = obtener_siguiente_codigo_k_transaccional(db)
        
        # 3. Crear el nuevo registro Kanban
        nuevo_kb = Kanban(
            numero_etiqueta=codigo_k,
            tipo_etiqueta=datos['tipo_etiqueta'],
            tipo_kanban=datos['tipo_kanban'],
            medio=datos['medio'],
            material=datos['material'].strip().upper(),
            centro=datos['centro'],
            almacen_origen=datos['almacen_origen'],
            almacen_destino=datos['almacen_destino'],
            puesto_origen=datos['puesto_origen'],
            puesto_destino=datos['puesto_destino'].strip().upper(),
            cantidad_reposicion=datos['cantidad_reposicion'],
            unidad_reposicion=datos['unidad_reposicion'],
            cantidad_punto_pedido=datos['cantidad_punto_pedido'],
            tiempo_preparacion_dias=datos['tiempo_preparacion_dias'],
            usuario_modificacion=usuario_email
        )
        db.add(nuevo_kb)
        
        # 4. Registrar en Logs de Auditoría
        db.add(LogAuditoria(
            accion="CREACIÓN",
            codigo_k=codigo_k,
            material=datos['material'].strip().upper(),
            medio=datos['medio'],
            almacen_destino=datos['almacen_destino'],
            puesto_destino=datos['puesto_destino'].strip().upper(),
            detalle_cambio="Creación inicial de registro en Supabase",
            usuario=usuario_email
        ))
        
        # 5. Registrar en Tracker de Solicitudes
        count_sol = db.query(func.count(TrackerSolicitud.id)).scalar() or 0
        id_sol = f"SOL-{(count_sol + 1):05d}"
        
        db.add(TrackerSolicitud(
            id_solicitud=id_sol,
            material=datos['material'].strip().upper(),
            codigo_k=codigo_k,
            tipo_kb=datos['tipo_etiqueta'],
            puesto_destino=datos['puesto_destino'].strip().upper(),
            medio=datos['medio'],
            cambio="CÓDIGO NUEVO",
            accion_requerida="ARMAR PEDIDO",
            usuario_procesos=usuario_email
        ))
        
        db.commit()
        
    return True, f"Kanban {codigo_k} creado exitosamente."

def modificar_kanban_existente(codigo_k: str, datos: dict, usuario_email: str) -> tuple[bool, str]:
    """Modifica un Kanban existente, actualiza la auditoría y envía la tarea al Tracker Logístico."""
    with get_db_session() as db:
        kb = db.query(Kanban).filter(Kanban.numero_etiqueta == codigo_k).first()
        if not kb:
            return False, f"❌ El Kanban {codigo_k} no existe en el sistema."
        
        # Actualizar campos
        kb.centro = datos.get('centro', kb.centro)
        kb.tipo_etiqueta = datos.get('tipo_etiqueta', kb.tipo_etiqueta)
        kb.tipo_kanban = datos.get('tipo_kanban', kb.tipo_kanban)
        kb.medio = datos.get('medio', kb.medio)
        kb.almacen_origen = datos.get('almacen_origen', kb.almacen_origen)
        kb.almacen_destino = datos.get('almacen_destino', kb.almacen_destino)
        kb.puesto_origen = datos.get('puesto_origen', kb.puesto_origen)
        kb.puesto_destino = datos.get('puesto_destino', kb.puesto_destino).strip().upper()
        kb.cantidad_reposicion = datos.get('cantidad_reposicion', kb.cantidad_reposicion)
        kb.cantidad_punto_pedido = datos.get('cantidad_punto_pedido', kb.cantidad_punto_pedido)
        kb.unidad_reposicion = datos.get('unidad_reposicion', kb.unidad_reposicion)
        kb.tiempo_preparacion_dias = datos.get('tiempo_preparacion_dias', kb.tiempo_preparacion_dias)
        kb.usuario_modificacion = usuario_email
        
        # 1. Registrar Auditoría
        db.add(LogAuditoria(
            accion="MODIFICACIÓN",
            codigo_k=codigo_k,
            material=kb.material,
            medio=kb.medio,
            almacen_destino=kb.almacen_destino,
            puesto_destino=kb.puesto_destino,
            detalle_cambio=datos.get('detalle_cambio', "Modificación de parámetros Kanban"),
            usuario=usuario_email
        ))
        
        # 2. Registrar Solicitud en Tracker Logístico
        count_sol = db.query(func.count(TrackerSolicitud.id)).scalar() or 0
        id_sol = f"SOL-{(count_sol + 1):05d}"
        
        db.add(TrackerSolicitud(
            id_solicitud=id_sol,
            material=kb.material,
            codigo_k=codigo_k,
            tipo_kb=kb.tipo_etiqueta,
            puesto_destino=kb.puesto_destino,
            medio=kb.medio,
            cambio="MODIFICACIÓN",
            accion_requerida="REVISAR Y REUBICAR",
            usuario_procesos=usuario_email
        ))
        
        db.commit()
        
    return True, f"Kanban {codigo_k} modificado exitosamente."

def eliminar_kanban_seguro(codigo_k: str, email_usuario: str) -> tuple[bool, str]:
    """Elimina un Kanban validando rol de Procesos, registra auditoría y avisa a Logística."""
    with get_db_session() as session:
        user = session.query(Usuario).filter(func.lower(Usuario.email) == email_usuario.strip().lower()).first()
        
        rol_user = str(user.rol).upper() if user and hasattr(user, 'rol') else ""
        if "PROCESOS" not in rol_user:
            return False, "❌ Permiso denegado: Solo usuarios con rol 'Procesos' pueden eliminar registros."
        
        kanban = session.query(Kanban).filter(Kanban.numero_etiqueta == codigo_k).first()
        if not kanban:
            return False, f"❌ El código {codigo_k} no existe en el sistema."
        
        # 1. Registrar Auditoría
        session.add(LogAuditoria(
            accion="ELIMINACIÓN",
            codigo_k=kanban.numero_etiqueta,
            material=kanban.material,
            medio=kanban.medio,
            almacen_destino=kanban.almacen_destino,
            puesto_destino=kanban.puesto_destino,
            detalle_cambio=f"Registro eliminado por {email_usuario}",
            usuario=email_usuario
        ))
        
        # 2. Registrar Solicitud de Retiro en Tracker Logístico
        count_sol = session.query(func.count(TrackerSolicitud.id)).scalar() or 0
        id_sol = f"SOL-{(count_sol + 1):05d}"
        
        session.add(TrackerSolicitud(
            id_solicitud=id_sol,
            material=kanban.material,
            codigo_k=kanban.numero_etiqueta,
            tipo_kb=kanban.tipo_etiqueta,
            puesto_destino=kanban.puesto_destino,
            medio=kanban.medio,
            cambio="ELIMINACIÓN",
            accion_requerida="RETIRAR DE PUESTO",
            usuario_procesos=email_usuario
        ))
        
        session.delete(kanban)
        session.commit()
        return True, f"✅ Kanban {codigo_k} eliminado exitosamente del sistema."