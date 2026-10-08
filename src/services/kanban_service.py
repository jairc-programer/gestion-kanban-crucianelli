from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Kanban, LogAuditoria, TrackerSolicitud, Usuario, RolUsuario
from src.database.connection import get_db_session

def obtener_siguiente_codigo_k_transaccional(db: Session) -> str:
    """
    Obtiene el siguiente código K realizando un bloqueo seguro a nivel de consulta
    para prevenir condiciones de carrera entre múltiples usuarios.
    """
    ultimos_kanbans = db.query(Kanban.numero_etiqueta).all()
    max_num = 0
    for (k_code,) in ultimos_kanbans:
        if k_code.startswith("K") and k_code[1:].isdigit():
            num = int(k_code[1:])
            if num > max_num:
                max_num = num
    
    nuevo_num = max_num + 1
    return f"K{nuevo_num:08d}"

def crear_nuevo_kanban(datos: dict, usuario_email: str) -> tuple[bool, str]:
    with get_db_session() as db:
        # Validación de duplicados
        existente = db.query(Kanban).filter(
            Kanban.material == datos['material'],
            Kanban.puesto_destino == datos['puesto_destino']
        ).first()
        
        if existente:
            return False, f"Ya existe el Kanban {existente.numero_etiqueta} para el material {datos['material']} en el puesto {datos['puesto_destino']}."
        
        codigo_k = obtener_siguiente_codigo_k_transaccional(db)
        
        nuevo_kb = Kanban(
            numero_etiqueta=codigo_k,
            tipo_etiqueta=datos['tipo_etiqueta'],
            tipo_kanban=datos['tipo_kanban'],
            medio=datos['medio'],
            material=datos['material'],
            centro=datos['centro'],
            almacen_origen=datos['almacen_origen'],
            almacen_destino=datos['almacen_destino'],
            puesto_origen=datos['puesto_origen'],
            puesto_destino=datos['puesto_destino'],
            cantidad_reposicion=datos['cantidad_reposicion'],
            unidad_reposicion=datos['unidad_reposicion'],
            cantidad_punto_pedido=datos['cantidad_punto_pedido'],
            tiempo_preparacion_dias=datos['tiempo_preparacion_dias'],
            usuario_modificacion=usuario_email
        )
        db.add(nuevo_kb)
        
        # Auditoría transaccional unificada
        db.add(LogAuditoria(
            accion="CREACIÓN",
            codigo_k=codigo_k,
            material=datos['material'],
            medio=datos['medio'],
            almacen_destino=datos['almacen_destino'],
            puesto_destino=datos['puesto_destino'],
            detalle_cambio="Creación inicial de registro",
            usuario=usuario_email
        ))
        
        # Tracker logístico
        count_sol = db.query(func.count(TrackerSolicitud.id)).scalar()
        id_sol = f"SOL-{(count_sol + 1):05d}"
        
        db.add(TrackerSolicitud(
            id_solicitud=id_sol,
            material=datos['material'],
            codigo_k=codigo_k,
            tipo_kb=datos['tipo_etiqueta'],
            puesto_destino=datos['puesto_destino'],
            medio=datos['medio'],
            cambio="CÓDIGO NUEVO",
            accion_requerida="ARMAR PEDIDO",
            usuario_procesos=usuario_email
        ))
        
    return True, f"Kanban {codigo_k} creado exitosamente."

def eliminar_kanban_seguro(codigo_k: str, email_usuario: str) -> tuple[bool, str]:
    with get_db_session() as session:
        # 1. Validar si el usuario existe y su rol
        user = session.query(Usuario).filter(Usuario.email == email_usuario).first()
        
        # Permitir borrado únicamente a PROCESOS
        if not user or user.rol != RolUsuario.PROCESOS:
            return False, "❌ Permiso denegado: Solo usuarios con rol 'Procesos' o Administrador pueden eliminar registros."
        
        # 2. Buscar el registro Kanban
        kanban = session.query(Kanban).filter(Kanban.numero_etiqueta == codigo_k).first()
        if not kanban:
            return False, f"❌ El código {codigo_k} no existe en el sistema."
        
        # 3. Auditoría previa al borrado
        log = LogAuditoria(
            accion="ELIMINACIÓN",
            codigo_k=kanban.numero_etiqueta,
            material=kanban.material,
            medio=kanban.medio,
            almacen_destino=kanban.almacen_destino,
            puesto_destino=kanban.puesto_destino,
            detalle_cambio=f"Registro eliminado por {email_usuario}",
            usuario=email_usuario
        )
        session.add(log)
        
        # 4. Borrar registro
        session.delete(kanban)
        return True, f"✅ Kanban {codigo_k} eliminado exitosamente del sistema."