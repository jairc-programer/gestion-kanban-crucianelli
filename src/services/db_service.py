import pandas as pd
import os
from src.database.connection import get_connection

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

def sincronizar_desde_archivos_iniciales():
    """Volca el catálogo inicial con sus VALORES REALES de TablaZ.xlsx a Supabase."""
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

        # Si la tabla está vacía, migramos los datos reales
        if count == 0 and os.path.exists(DB_FILE):
            print("Iniciando migración limpia de datos reales a Supabase...")
            df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
            
            # Normalización de encabezados del DataFrame
            cols_map = {str(c).strip(): c for c in df.columns}
            
            def get_val(row_data, col_names, default=""):
                for cn in col_names:
                    for real_col in df.columns:
                        if cn.lower() == str(real_col).strip().lower():
                            val = row_data[real_col]
                            if pd.notna(val):
                                return val
                return default

            registros_a_insertar = []
            for _, r in df.iterrows():
                # Extraer VALORES REALES
                k_code = str(get_val(r, ['N° Etiquetas', 'N° Etiqueta', 'codigo_k', 'numero_etiqueta'])).strip().upper()
                if not k_code or k_code == 'NAN' or not k_code.startswith('K'):
                    continue
                
                mat = str(get_val(r, ['Material', 'material'])).strip().upper()
                if not mat or mat == 'NAN':
                    continue

                p_dest = str(get_val(r, ['Puesto de trabajo destino', 'Puesto Destino', 'puesto_destino'])).strip().upper()
                alm_orig = str(get_val(r, ['Almacén Origen', 'Almacen Origen', 'almacen_origen'], 'L010')).strip()
                alm_dest = str(get_val(r, ['Almacen Destino', 'Almacén Destino', 'almacen_destino'], 'P140')).strip()
                p_orig = str(get_val(r, ['Puesto trabajo Origen', 'Puesto Origen', 'puesto_origen'], '-')).strip()
                med = str(get_val(r, ['Medio', 'medio'], 'SIN MEDIO DEFINIDO')).strip()
                t_kanban = str(get_val(r, ['Tipo Kanban', 'tipo_kanban'], 'TARJETA')).strip()
                t_etiq = str(get_val(r, ['Tipo Etiqueta', 'tipo_etiqueta'], 'KE')).strip()
                centro_val = str(get_val(r, ['Centro', 'centro'], 'A110')).strip()
                
                try: c_repo = float(get_val(r, ['Cantidad Reposicion', 'Cantidad Reposición', 'cantidad_reposicion'], 0.0))
                except: c_repo = 0.0
                
                try: c_pp = float(get_val(r, ['Cantidad Punto de Pedido', 'cantidad_punto_pedido'], 0.0))
                except: c_pp = 0.0
                
                try: t_dias = int(get_val(r, ['Tiempo preparación abast. (en días)', 'Tiempo preparacion', 'tiempo_preparacion_dias'], 1))
                except: t_dias = 1

                un_repo = str(get_val(r, ['Unidad Reposicion', 'Unidad Reposición', 'unidad_reposicion'], 'UN')).strip()
                usr_mod = str(get_val(r, ['Usuario Modificación', 'Usuario Modificacion', 'usuario_modificacion'], 'Sistema')).strip()

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
                print("✅ Sincronización exitosa de valores reales a Supabase.")
                
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