import pandas as pd
import os
from src.database.connection import get_connection

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"
AUDITORIA_FILE = "historial_auditoria.csv"
TRACKER_FILE = "tracker_ejecucion.csv"

def sincronizar_desde_archivos_iniciales():
    """Carga los datos iniciales desde los archivos si la BD está vacía."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check Kanbans
    cursor.execute("SELECT COUNT(*) FROM kanbans")
    if cursor.fetchone()[0] == 0 and os.path.exists(DB_FILE):
        try:
            df = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
            for _, r in df.iterrows():
                k_code = str(r.get('N° Etiquetas', '')).strip().upper()
                if not k_code or k_code == 'NAN':
                    continue
                cursor.execute("""
                INSERT OR IGNORE INTO kanbans (
                    codigo_k, tipo_etiqueta, tipo_kanban, medio, material, centro,
                    almacen_origen, almacen_destino, puesto_origen, puesto_destino,
                    cantidad_reposicion, unidad_reposicion, cantidad_punto_pedido,
                    dias_abastecimiento, fecha_modificacion, usuario_modificacion
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
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
                    str(r.get('Fecha Modificación', '-')),
                    str(r.get('Usuario Modificación', 'Sistema'))
                ))
            conn.commit()
        except Exception as e:
            print("Error migrando Excel inicial:", e)

    # Check Auditoria
    cursor.execute("SELECT COUNT(*) FROM auditoria")
    if cursor.fetchone()[0] == 0 and os.path.exists(AUDITORIA_FILE):
        try:
            df_aud = pd.read_csv(AUDITORIA_FILE)
            for _, r in df_aud.iterrows():
                cursor.execute("""
                INSERT INTO auditoria (fecha_hora, usuario, accion, codigo_k, material, detalle)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    str(r.get('Fecha y Hora', '-')),
                    str(r.get('Usuario', '-')),
                    str(r.get('Acción', '-')),
                    str(r.get('Código K', '-')),
                    str(r.get('Material', '-')),
                    str(r.get('Detalle de Cambios', '-'))
                ))
            conn.commit()
        except Exception as e:
            print("Error migrando Auditoría inicial:", e)

    # Check Tracker
    cursor.execute("SELECT COUNT(*) FROM tracker")
    if cursor.fetchone()[0] == 0 and os.path.exists(TRACKER_FILE):
        try:
            df_trk = pd.read_csv(TRACKER_FILE)
            for _, r in df_trk.iterrows():
                cursor.execute("""
                INSERT INTO tracker (
                    fecha_solicitud, usuario_solicitante, tipo_accion, codigo_k, material,
                    almacen_origen, puesto_destino, detalle, estado_logistico, estado_sap,
                    fecha_sap, usuario_sap, estado_impresion, fecha_impresion, usuario_impresion,
                    estado_puesto, fecha_puesto, usuario_puesto, fecha_ejecucion, usuario_logistica
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(r.get('Fecha Solicitud', '-')),
                    str(r.get('Usuario Solicitante', '-')),
                    str(r.get('Tipo de Acción', '-')),
                    str(r.get('Código K', '-')),
                    str(r.get('Material', '-')),
                    str(r.get('Almacén Origen', '-')),
                    str(r.get('Puesto Destino', '-')),
                    str(r.get('Detalle', '-')),
                    str(r.get('Estado Logístico', 'PENDIENTE')),
                    str(r.get('Estado SAP', 'PENDIENTE')),
                    str(r.get('Fecha SAP', '-')),
                    str(r.get('Usuario SAP', '-')),
                    str(r.get('Estado Impresion', 'PENDIENTE')),
                    str(r.get('Fecha Impresion', '-')),
                    str(r.get('Usuario Impresion', '-')),
                    str(r.get('Estado Puesto', 'PENDIENTE')),
                    str(r.get('Fecha Puesto', '-')),
                    str(r.get('Usuario Puesto', '-')),
                    str(r.get('Fecha Ejecución Logística', '-')),
                    str(r.get('Usuario Logística', '-'))
                ))
            conn.commit()
        except Exception as e:
            print("Error migrando Tracker inicial:", e)

    conn.close()

def obtener_kanbans_df():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM kanbans", conn)
    conn.close()
    
    # Renombrar columnas para compatibilidad total con la UI
    df.rename(columns={
        'codigo_k': 'N° Etiquetas',
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
        'dias_abastecimiento': 'Tiempo preparación abast. (en días)',
        'fecha_modificacion': 'Fecha Modificación',
        'usuario_modificacion': 'Usuario Modificación'
    }, inplace=True)
    return df