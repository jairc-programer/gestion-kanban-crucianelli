import pandas as pd
import os
from src.database.connection import get_connection

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

def sincronizar_desde_archivos_iniciales():
    """Mantiene la base de datos sincronizada si estuviera vacía."""
    conn = get_connection()
    cursor = conn.cursor()
    is_pg = "psycopg2" in str(type(conn))
    param = "%s" if is_pg else "?"
    
    try:
        # Validar si hay registros en la tabla kanbans
        cursor.execute("SELECT COUNT(*) FROM kanbans")
        row = cursor.fetchone()
        count = row['count'] if is_pg and isinstance(row, dict) else row[0]

        if count == 0 and os.path.exists(DB_FILE):
            df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
            for _, r in df.iterrows():
                k_code = str(r.get('N° Etiquetas', '')).strip().upper()
                if not k_code or k_code == 'NAN':
                    continue
                
                query = f"""
                INSERT INTO kanbans (
                    numero_etiqueta, tipo_etiqueta, tipo_kanban, medio, material, centro,
                    almacen_origen, almacen_destino, puesto_origen, puesto_destino,
                    cantidad_reposicion, unidad_reposicion, cantidad_punto_pedido,
                    tiempo_preparacion_dias, fecha_modificacion, usuario_modificacion
                ) VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, NOW(), {param})
                """ if is_pg else f"""
                INSERT OR IGNORE INTO kanbans (
                    numero_etiqueta, tipo_etiqueta, tipo_kanban, medio, material, centro,
                    almacen_origen, almacen_destino, puesto_origen, puesto_destino,
                    cantidad_reposicion, unidad_reposicion, cantidad_punto_pedido,
                    tiempo_preparacion_dias, fecha_modificacion, usuario_modificacion
                ) VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, datetime('now'), {param})
                """
                
                cursor.execute(query, (
                    k_code,
                    str(r.get('Tipo Etiqueta', 'KE')),
                    str(r.get('Tipo Kanban', 'TARJETA')),
                    str(r.get('Medio', 'SIN MEDIO DEFINIDO')),
                    str(r.get('Material', '')).strip().upper(),
                    str(r.get('Centro', 'A110')),
                    str(r.get('Almacén Origen', 'L010')),
                    str(r.get('Almacen Destino', 'P140')),
                    str(r.get('Puesto trabajo Origen', '-')),
                    str(r.get('Puesto de trabajo destino', '')).strip().upper(),
                    float(r.get('Cantidad Reposicion', 0.0)),
                    str(r.get('Unidad Reposicion', 'UN')),
                    float(r.get('Cantidad Punto de Pedido', 0.0)),
                    int(r.get('Tiempo preparación abast. (en días)', 1)),
                    str(r.get('Usuario Modificación', 'Sistema'))
                ))
            conn.commit()
    except Exception as e:
        print("Error en sincronizar_desde_archivos_iniciales:", e)
    finally:
        conn.close()

def obtener_kanbans_df():
    """Obtiene el DataFrame de Kanbans directamente desde Supabase/PostgreSQL o SQLite."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM kanbans", conn)
    conn.close()
    
    # Mapeo universal de campos de la BD a la interfaz visual de Streamlit
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