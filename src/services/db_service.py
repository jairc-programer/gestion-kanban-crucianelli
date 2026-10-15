import pandas as pd
import os
from src.database.connection import get_connection

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

def sincronizar_desde_archivos_iniciales():
    """Volca el catálogo inicial de TablaZ.xlsx a Supabase si la tabla está vacía o tiene menos de 10 registros."""
    conn = get_connection()
    cursor = conn.cursor()
    is_pg = "psycopg2" in str(type(conn))
    
    try:
        cursor.execute("SELECT COUNT(*) FROM kanbans")
        row = cursor.fetchone()
        
        if is_pg and isinstance(row, dict):
            count = row.get('count', 0)
        elif isinstance(row, (tuple, list)):
            count = row[0]
        else:
            count = 0

        # Si en Supabase hay menos de 10 registros, poblamos con el catálogo del Excel
        if count < 10 and os.path.exists(DB_FILE):
            df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
            
            registros_a_insertar = []
            for _, r in df.iterrows():
                k_code = str(r.get('N° Etiquetas', r.get('N° Etiqueta', r.get('codigo_k', '')))).strip().upper()
                if not k_code or k_code == 'NAN' or not k_code.startswith('K'):
                    continue
                
                mat = str(r.get('Material', '')).strip().upper()
                if not mat or mat == 'NAN':
                    continue

                p_dest = str(r.get('Puesto de trabajo destino', r.get('Puesto Destino', ''))).strip().upper()
                alm_orig = str(r.get('Almacén Origen', r.get('Almacen Origen', 'L010'))).strip()
                alm_dest = str(r.get('Almacen Destino', r.get('Almacén Destino', 'P140'))).strip()
                p_orig = str(r.get('Puesto trabajo Origen', r.get('Puesto Origen', '-'))).strip()
                med = str(r.get('Medio', 'SIN MEDIO DEFINIDO')).strip()
                t_kanban = str(r.get('Tipo Kanban', 'TARJETA')).strip()
                t_etiq = str(r.get('Tipo Etiqueta', 'KE')).strip()
                centro_val = str(r.get('Centro', 'A110')).strip()
                
                try: c_repo = float(r.get('Cantidad Reposicion', r.get('Cantidad Reposición', 0.0)))
                except: c_repo = 0.0
                
                try: c_pp = float(r.get('Cantidad Punto de Pedido', 0.0))
                except: c_pp = 0.0
                
                try: t_dias = int(r.get('Tiempo preparación abast. (en días)', r.get('Tiempo preparacion', 1)))
                except: t_dias = 1

                un_repo = str(r.get('Unidad Reposicion', r.get('Unidad Reposición', 'UN'))).strip()
                usr_mod = str(r.get('Usuario Modificación', r.get('Usuario Modificacion', 'Sistema'))).strip()

                registros_a_insertar.append((
                    k_code, t_etiq, t_kanban, med, mat, centro_val,
                    alm_orig, alm_dest, p_orig, p_dest,
                    c_repo, un_repo, c_pp, t_dias, usr_mod
                ))

            if registros_a_insertar:
                if is_pg:
                    query = """
                    INSERT INTO kanbans (
                        numero_etiqueta, tipo_etiqueta, tipo_kanban, medio, material, centro,
                        almacen_origen, almacen_destino, puesto_origen, puesto_destino,
                        cantidad_reposicion, unidad_reposicion, cantidad_punto_pedido,
                        tiempo_preparacion_dias, fecha_modificacion, usuario_modificacion
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    ON CONFLICT (numero_etiqueta) DO NOTHING;
                    """
                else:
                    query = """
                    INSERT OR IGNORE INTO kanbans (
                        numero_etiqueta, tipo_etiqueta, tipo_kanban, medio, material, centro,
                        almacen_origen, almacen_destino, puesto_origen, puesto_destino,
                        cantidad_reposicion, unidad_reposicion, cantidad_punto_pedido,
                        tiempo_preparacion_dias, fecha_modificacion, usuario_modificacion
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?);
                    """

                cursor.executemany(query, registros_a_insertar)
                conn.commit()
                
    except Exception as e:
        print("Error al sincronizar catálogo inicial:", e)
    finally:
        conn.close()

def obtener_kanbans_df():
    """Consulta el catálogo unificado directamente desde Supabase."""
    sincronizar_desde_archivos_iniciales()
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM kanbans ORDER BY id ASC", conn)
    conn.close()
    
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
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM tracker_solicitudes ORDER BY id DESC", conn)
    conn.close()
    
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
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM logs_auditoria ORDER BY fecha_hora DESC", conn)
    conn.close()
    
    df.rename(columns={
        'fecha_hora': 'Fecha y Hora',
        'usuario': 'Usuario',
        'accion': 'Acción',
        'codigo_k': 'Código K',
        'material': 'Material',
        'detalle_cambio': 'Detalle de Cambios'
    }, inplace=True)
    return df