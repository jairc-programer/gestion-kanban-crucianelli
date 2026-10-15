import re
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Kanban, LogAuditoria, TrackerSolicitud, Usuario, RolUsuario
from src.database.connection import get_db_session

def obtener_siguiente_codigo_k_transaccional(db: Session) -> str:
    """
    Escanea la base de datos de Supabase y obtiene el siguiente número K 
    correlativo disponible sin duplicar códigos existentes.
    """
    # Consultar todos los números de etiqueta existentes
    registros = db.query(Kanban.numero_etiqueta).all()
    
    numeros_usados = set()
    for (k_code,) in registros:
        if k_code:
            match = re.search(r'\d+', str(k_code))
            if match:
                numeros_usados.add(int(match.group(0)))
                
    # Buscar el primer número disponible partiendo de 1
    siguiente_num = 1
    while siguiente_num in numeros_usados:
        siguiente_num += 1
        
    return f"K{siguiente_num:08d}"

def crear_nuevo_kanban(datos: dict, usuario_email: str) -> tuple[bool, str]:
    with get_db_session() as db:
        # 1. Validar si ya existe la combinación Material + Puesto Destino
        existente = db.query(Kanban).filter(
            func.lower(Kanban.material) == datos['material'].strip().lower(),
            func.lower(Kanban.puesto_destino) == datos['puesto_destino'].strip().lower()
        ).first()
        
        if existente:
            return False, f"Ya existe el Kanban {existente.numero_etiqueta} asignado al material {datos['material']} en el puesto {datos['puesto_destino']}."
        
        # 2. Generar el código K correlativo único
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
        
        # Confirmar la transacción en la BD remota
        db.commit()
        
    return True, f"Kanban {codigo_k} creado exitosamente."

def eliminar_kanban_seguro(codigo_k: str, email_usuario: str) -> tuple[bool, str]:
    with get_db_session() as session:
        user = session.query(Usuario).filter(func.lower(Usuario.email) == email_usuario.strip().lower()).first()
        
        rol_user = str(user.rol).upper() if user and hasattr(user, 'rol') else ""
        if "PROCESOS" not in rol_user:
            return False, "❌ Permiso denegado: Solo usuarios con rol 'Procesos' pueden eliminar registros."
        
        kanban = session.query(Kanban).filter(Kanban.numero_etiqueta == codigo_k).first()
        if not kanban:
            return False, f"❌ El código {codigo_k} no existe en el sistema."
        
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
        
        session.delete(kanban)
        session.commit()
        return True, f"✅ Kanban {codigo_k} eliminado exitosamente del sistema."