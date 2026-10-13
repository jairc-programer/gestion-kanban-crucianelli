import socket

PRINTER_PORT = 9100

def enviar_a_impresora_brother(ip_impresora, codigo_k, material, origen, destino, qr_data):
    """
    Envía comandos de texto/etiqueta directamente a la impresora Brother QL-1110NWB por la red (Puerto 9100 TCP).
    """
    try:
        etiqueta_raw = f"""
================================
     CRUCIANELLI KANBAN
================================
CODIGO K: {codigo_k}
MATERIAL: {material}
ORIGEN  : {origen}
DESTINO : {destino}
--------------------------------
DATA    : {qr_data}
================================
\x0c"""
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(4)
            s.connect((ip_impresora.strip(), PRINTER_PORT))
            s.sendall(etiqueta_raw.encode('utf-8'))
            
        return True, "✅ Orden enviada exitosamente a la impresora Brother."
    except socket.timeout:
        return False, "❌ Tiempo agotado: Compruebe la IP de la rotuladora en la red."
    except Exception as e:
        return False, f"❌ Error de red: {str(e)}"