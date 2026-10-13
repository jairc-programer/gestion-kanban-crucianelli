import pandas as pd
import os
from datetime import datetime

try:
    from zoneinfo import ZoneInfo
    ARG_TZ = ZoneInfo('America/Argentina/Buenos_Aires')
except ImportError:
    import pytz
    ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

LOG_FILE = "historial_cambios.csv"
TRACKER_FILE = "tracker_ejecucion.csv"

def obtener_fecha_hora_actual():
    return datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")

def registrar_auditoria(fecha_hora, usuario, accion, codigo_k, material, detalle):
    log_entry = {
        'Fecha y Hora': fecha_hora,
        'Usuario': usuario,
        'Acción': accion,
        'Código K': codigo_k,
        'Material': material,
        'Detalle de Cambios': detalle
    }
    df_log = pd.DataFrame([log_entry])
    if os.path.exists(LOG_FILE):
        df_log.to_csv(LOG_FILE, mode='a', header=False, index=False)
    else:
        df_log.to_csv(LOG_FILE, mode='w', header=True, index=False)

def registrar_tracker_logistica(fecha_hora, usuario, accion, codigo_k, material, origen, destino, detalle):
    tracker_entry = {
        'Fecha Solicitud': fecha_hora,
        'Usuario Solicitante': usuario,
        'Tipo de Acción': accion,
        'Código K': codigo_k,
        'Material': material,
        'Almacén Origen': origen,
        'Puesto Destino': destino,
        'Detalle': detalle,
        'Estado Logístico': 'PENDIENTE',
        'Estado SAP': 'PENDIENTE',
        'Fecha SAP': '-',
        'Usuario SAP': '-',
        'Estado Impresion': 'PENDIENTE',
        'Fecha Impresion': '-',
        'Usuario Impresion': '-',
        'Estado Puesto': 'PENDIENTE',
        'Fecha Puesto': '-',
        'Usuario Puesto': '-',
        'Fecha Ejecución Logística': '-',
        'Usuario Logística': '-'
    }
    df_trk = pd.DataFrame([tracker_entry])
    if os.path.exists(TRACKER_FILE):
        df_trk.to_csv(TRACKER_FILE, mode='a', header=False, index=False)
    else:
        df_trk.to_csv(TRACKER_FILE, mode='w', header=True, index=False)