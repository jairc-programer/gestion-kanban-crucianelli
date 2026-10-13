import socket
import urllib.request
import io
from PIL import Image

# Configuración por defecto de la impresora Brother QL-1110NWB en la red
DEFAULT_PRINTER_IP = "192.168.1.150"  # Reemplazar por la IP fija de la impresora en la red
PRINTER_PORT = 9100

def enviar_a_impresora_brother(ip_impresora, codigo_k, material, origen, destino, qr_data):
    """
    Envía comandos de impresión o texto directamente a la impresora Brother por el puerto 9100 TCP.
    """
    try:
        # Comando básico en lenguaje ESC/P de Brother o datos raw para puerto 9100
        zpl_or_raw = f"""
        CRUCIANELLI KANBAN
        ------------------------------
        CODIGO K: {codigo_k}
        MATERIAL: {material}
        ORIGEN  : {origen}
        DESTINO : {destino}
        ------------------------------
        {qr_data}
        """
        
        # Conexión socket directo por la red Wi-Fi/LAN
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)  # Timeout de 5 segundos
            s.connect((ip_impresora, PRINTER_PORT))
            s.sendall(zpl_or_raw.encode('utf-8'))
            
        return True, "✅ Orden de impresión enviada correctamente a la rotuladora Brother."
    except socket.timeout:
        return False, "❌ Tiempo de espera agotado: No se pudo conectar a la IP de la impresora."
    except Exception as e:
        return False, f"❌ Error de conexión de red: {str(e)}"