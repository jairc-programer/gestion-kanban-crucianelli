import pandas as pd
from src.database.connection import get_engine

def obtener_kanbans_df():
    """Consulta la tabla 'kanbans' en Supabase a través del engine SQLAlchemy."""
    engine = get_engine()
    query = "SELECT * FROM kanbans WHERE numero_etiqueta LIKE 'K%%' ORDER BY id ASC"
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    
    # Renombrar columnas para la interfaz de Streamlit
    df.rename(columns={
        'numero_etiqueta': 'N° Etiquetas',
        'tipo_etiqueta': 'Tipo Etiqueta',
        'tipo_kanban': 'Tipo Kanban',
        'medio': 'Medio',
        'material': 'Material',
        'centro': 'Centro',
        'almacen_origen': 'Almacén Origen',
        'almacen_destino': 'Almacen Destino',
        'puesto_origen': 'Puesto trabajo Origen',
        'puesto_destino': 'Puesto de trabajo destino',
        'cantidad_reposicion': 'Cantidad Reposicion',
        'unidad_reposicion': 'Unidad Reposicion',
        'cantidad_punto_pedido': 'Cantidad Punto de Pedido',
        'tiempo_preparacion_dias': 'Tiempo preparación abast. (en días)',
        'fecha_modificacion': 'Fecha Modificación',
        'usuario_modificacion': 'Usuario Modificación'
    }, inplace=True)
    return df

def obtener_tracker_df():
    """Consulta la tabla 'tracker_solicitudes' en Supabase para la Página 4."""
    engine = get_engine()
    query = "SELECT * FROM tracker_solicitudes ORDER BY id DESC"
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    
    df.rename(columns={
        'id_solicitud': 'ID Solicitud',
        'fecha_solicitud': 'Fecha Solicitud',
        'usuario_procesos': 'Usuario Solicitante',
        'codigo_k': 'Código K',
        'material': 'Material',
        'puesto_destino': 'Puesto Destino',
        'medio': 'Medio',
        'cambio': 'Tipo de Acción',
        'accion_requerida': 'Acción Requerida',
        'cargado_sap': 'Estado SAP',
        'impreso': 'Estado Impresion',
        'estado_fisico': 'Estado Puesto',
        'fecha_finalizacion': 'Fecha Ejecución Logística'
    }, inplace=True)
    return df

def obtener_auditoria_df():
    """Consulta la tabla 'logs_auditoria' en Supabase para la Página 6."""
    engine = get_engine()
    query = "SELECT * FROM logs_auditoria ORDER BY fecha_hora DESC"
    
    with engine.connect() as conn:
        df = pd.read_sql_query(query, conn)
    
    df.rename(columns={
        'fecha_hora': 'Fecha y Hora',
        'usuario': 'Usuario',
        'accion': 'Acción',
        'codigo_k': 'Código K',
        'material': 'Material',
        'detalle_cambio': 'Detalle de Cambios'
    }, inplace=True)
    return df