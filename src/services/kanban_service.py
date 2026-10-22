import re
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Kanban, LogAuditoria, TrackerSolicitud, Usuario, RolUsuario
from src.database.connection import get_db_session
from utils.style import obtener_ahora_arg

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
        ahora_arg = obtener_ahora_arg()
        
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
        
        # 4. Registrar en Logs de Auditoría con hora Argentina
        db.add(LogAuditoria(
            accion="CREACIÓN",
            codigo_k=codigo_k,
            material=datos['material'].strip().upper(),
            medio=datos['medio'],
            almacen_destino=datos['almacen_destino'],
            puesto_destino=datos['puesto_destino'].strip().upper(),
            detalle_cambio="Creación inicial de registro en Supabase",
            usuario=usuario_email,
            fecha_hora=ahora_arg
        ))
        
        # 5. Registrar en Tracker de Solicitudes con hora Argentina
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
            usuario_procesos=usuario_email,
            fecha_solicitud=ahora_arg
        ))
        
        db.commit()
        
    return True, f"Kanban {codigo_k} creado exitosamente."

def modificar_kanban_existente(codigo_k: str, datos: dict, usuario_email: str) -> tuple[bool, str]:
    """Modifica un Kanban existente, actualiza la auditoría y envía la tarea al Tracker Logístico."""
    with get_db_session() as db:
        kb = db.query(Kanban).filter(Kanban.numero_etiqueta == codigo_k).first()
        if not kb:
            return False, f"❌ El Kanban {codigo_k} no existe en el sistema."
        
        ahora_arg = obtener_ahora_arg()
        
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
        kb.fecha_modificacion = ahora_arg
        
        # 1. Registrar Auditoría
        db.add(LogAuditoria(
            accion="MODIFICACIÓN",
            codigo_k=codigo_k,
            material=kb.material,
            medio=kb.medio,
            almacen_destino=kb.almacen_destino,
            puesto_destino=kb.puesto_destino,
            detalle_cambio=datos.get('detalle_cambio', "Modificación de parámetros Kanban"),
            usuario=usuario_email,
            fecha_hora=ahora_arg
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
            usuario_procesos=usuario_email,
            fecha_solicitud=ahora_arg
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
        
        ahora_arg = obtener_ahora_arg()
        
        # 1. Registrar Auditoría
        session.add(LogAuditoria(
            accion="ELIMINACIÓN",
            codigo_k=kanban.numero_etiqueta,
            material=kanban.material,
            medio=kanban.medio,
            almacen_destino=kanban.almacen_destino,
            puesto_destino=kanban.puesto_destino,
            detalle_cambio=f"Registro eliminado por {email_usuario}",
            usuario=email_usuario,
            fecha_hora=ahora_arg
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
            usuario_procesos=email_usuario,
            fecha_solicitud=ahora_arg
        ))
        
        session.delete(kanban)
        session.commit()
        return True, f"✅ Kanban {codigo_k} eliminado exitosamente del sistema."

def modificar_kanbans_masivo_desde_df(df_carga: pd.DataFrame, usuario_email: str) -> tuple[int, int, list]:
    """
    Procesa un DataFrame para actualización masiva de Kanbans.
    Retorna: (total_exitos, total_errores, lista_detalles_error)
    """
    exitos = 0
    errores = 0
    detalles_error = []
    
    mapeo_columnas = {
        'n° etiquetas': 'numero_etiqueta',
        'código k': 'numero_etiqueta',
        'codigo k': 'numero_etiqueta',
        'tipo etiqueta': 'tipo_etiqueta',
        'tipo kanban': 'tipo_kanban',
        'medio': 'medio',
        'material': 'material',
        'centro': 'centro',
        'almacén origen': 'almacen_origen',
        'almacen origen': 'almacen_origen',
        'almacén destino': 'almacen_destino',
        'almacen destino': 'almacen_destino',
        'puesto trabajo origen': 'puesto_origen',
        'puesto de trabajo origen': 'puesto_origen',
        'puesto trabajo destino': 'puesto_destino',
        'puesto de trabajo destino': 'puesto_destino',
        'cantidad reposicion': 'cantidad_reposicion',
        'cantidad reposición': 'cantidad_reposicion',
        'unidad reposicion': 'unidad_reposicion',
        'unidad reposición': 'unidad_reposicion',
        'cantidad punto de pedido': 'cantidad_punto_pedido',
        'tiempo preparación abast. (en días)': 'tiempo_preparacion_dias',
        'tiempo preparacion abast. (en dias)': 'tiempo_preparacion_dias'
    }

    cols_normalizadas = {str(col).strip().lower(): col for col in df_carga.columns}
    
    col_k_excel = None
    for k_alias in ['n° etiquetas', 'código k', 'codigo k']:
        if k_alias in cols_normalizadas:
            col_k_excel = cols_normalizadas[k_alias]
            break

    if not col_k_excel:
        return 0, len(df_carga), ["❌ No se encontró la columna 'N° Etiquetas' o 'Código K' en el archivo cargado."]

    ahora_arg = obtener_ahora_arg()

    with get_db_session() as db:
        count_sol = db.query(func.count(TrackerSolicitud.id)).scalar() or 0

        for idx, row in df_carga.iterrows():
            k_code = str(row.get(col_k_excel, '')).strip().upper()
            if not k_code or k_code in ['NAN', 'NONE', '-']:
                continue

            kb = db.query(Kanban).filter(Kanban.numero_etiqueta == k_code).first()
            if not kb:
                errores += 1
                detalles_error.append(f"Fila {idx+2}: El Código K '{k_code}' no existe en Supabase.")
                continue

            try:
                for col_orig, col_orm in mapeo_columnas.items():
                    if col_orig in cols_normalizadas:
                        val = row.get(cols_normalizadas[col_orig])
                        if pd.notna(val) and str(val).strip() not in ['', 'nan', 'None']:
                            val_str = str(val).strip()
                            if col_orm in ['cantidad_reposicion', 'cantidad_punto_pedido']:
                                setattr(kb, col_orm, float(val_str))
                            elif col_orm == 'tiempo_preparacion_dias':
                                setattr(kb, col_orm, int(float(val_str)))
                            elif col_orm in ['material', 'puesto_destino', 'almacen_origen', 'almacen_destino']:
                                setattr(kb, col_orm, val_str.upper())
                            else:
                                setattr(kb, col_orm, val_str)

                kb.usuario_modificacion = usuario_email
                kb.fecha_modificacion = ahora_arg

                # 1. Auditoría
                db.add(LogAuditoria(
                    accion="MODIFICACIÓN MASIVA",
                    codigo_k=k_code,
                    material=kb.material,
                    medio=kb.medio,
                    almacen_destino=kb.almacen_destino,
                    puesto_destino=kb.puesto_destino,
                    detalle_cambio=f"Actualización masiva vía archivo Excel por {usuario_email}",
                    usuario=usuario_email,
                    fecha_hora=ahora_arg
                ))

                # 2. Solicitud en Tracker Logístico
                count_sol += 1
                id_sol = f"SOL-{count_sol:05d}"
                db.add(TrackerSolicitud(
                    id_solicitud=id_sol,
                    material=kb.material,
                    codigo_k=k_code,
                    tipo_kb=kb.tipo_etiqueta,
                    puesto_destino=kb.puesto_destino,
                    medio=kb.medio,
                    cambio="MODIFICACIÓN MASIVA",
                    accion_requerida="REVISAR Y REUBICAR",
                    usuario_procesos=usuario_email,
                    fecha_solicitud=ahora_arg
                ))

                exitos += 1

            except Exception as e:
                errores += 1
                detalles_error.append(f"Fila {idx+2} ({k_code}): Error de formato ({str(e)})")

        db.commit()

    return exitos, errores, detalles_error