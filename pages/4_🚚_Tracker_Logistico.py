import streamlit as st
import pandas as pd
import os
import urllib.parse
from datetime import datetime
import streamlit.components.v1 as components
from utils.printer import enviar_a_impresora_brother

try:
    from zoneinfo import ZoneInfo
    ARG_TZ = ZoneInfo('America/Argentina/Buenos_Aires')
except ImportError:
    import pytz
    ARG_TZ = pytz.timezone('America/Argentina/Buenos_Aires')

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("🚚 Tracker de Ejecución Logística")

# Configuración de IP de la rotuladora Brother en la barra lateral o sección
with st.sidebar:
    st.markdown("### 🖨️ Configuración Impresora")
    printer_ip = st.text_input("IP Rotuladora Brother (Wi-Fi):", value="192.168.1.150", help="Dirección IP asignada a la Brother QL-1110NWB en la red de la planta.")

TRACKER_FILE = "tracker_ejecucion.csv"

if os.path.exists(TRACKER_FILE):
    df_trk = pd.read_csv(TRACKER_FILE, dtype=str)
    
    if 'Detalle / Observaciones' in df_trk.columns and 'Detalle' not in df_trk.columns:
        df_trk['Detalle'] = df_trk['Detalle / Observaciones']

    cols_defaults = {
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
        'Usuario Logística': '-',
        'Detalle': 'Sin Detalle'
    }
    
    for col, default_val in cols_defaults.items():
        if col not in df_trk.columns:
            df_trk[col] = default_val
        else:
            df_trk[col] = df_trk[col].fillna(default_val)
            
    for col in df_trk.columns:
        df_trk[col] = df_trk[col].astype(str)

    estado_filter = st.radio("Filtrar por Estado:", ["TODOS", "PENDIENTES", "COMPLETADOS"], horizontal=True)
    
    def obtener_estado_general(r):
        s_sap = str(r.get('Estado SAP', '')).strip().upper() == 'OK'
        s_imp = str(r.get('Estado Impresion', '')).strip().upper() == 'OK'
        s_pst = str(r.get('Estado Puesto', '')).strip().upper() == 'OK'
        
        count = sum([s_sap, s_imp, s_pst])
        if count == 3:
            return "COMPLETADO"
        elif count > 0:
            return "EN PROCESO"
        else:
            return "PENDIENTE"

    df_trk['Estado Logístico'] = df_trk.apply(obtener_estado_general, axis=1)

    if estado_filter == "PENDIENTES":
        df_show = df_trk[df_trk['Estado Logístico'].isin(['PENDIENTE', 'EN PROCESO'])]
    elif estado_filter == "COMPLETADOS":
        df_show = df_trk[df_trk['Estado Logístico'] == 'COMPLETADO']
    else:
        df_show = df_trk.copy()

    st.markdown("##### 📋 Tareas Solicitadas por Procesos")
    
    if df_show.empty:
        st.info("No se encontraron tareas para el filtro seleccionado.")
    else:
        for idx, row in df_show.iterrows():
            k_code = str(row.get('Código K', '-'))
            mat_code = str(row.get('Material', '-'))
            action_type = str(row.get('Tipo de Acción', 'ACCIÓN'))
            puesto_dest = str(row.get('Puesto Destino', '-'))
            est_log = str(row.get('Estado Logístico', 'PENDIENTE'))
            
            badge = "🔴" if est_log == "PENDIENTE" else ("🟡" if est_log == "EN PROCESO" else "🟢")
            
            with st.expander(f"{badge} [{action_type}] Código K: {k_code} | Material: {mat_code} | Destino: {puesto_dest} ({est_log})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Fecha Solicitud:** `{row.get('Fecha Solicitud')}`")
                    st.write(f"**Solicitante:** `{row.get('Usuario Solicitante')}`")
                    det_val = str(row.get('Detalle', row.get('Detalle / Observaciones', '-')))
                    st.markdown(f"**Detalle de Cambios:** `{det_val}`")
                    st.write(f"**Ubicación:** Origen `{row.get('Almacén Origen')}` ➔ Destino `{puesto_dest}`")
                    
                    # --- POPUP CON OPCIONES DE IMPRESIÓN ---
                    with st.popover("🖨️ Imprimir Etiqueta Kanban"):
                        st.markdown("### 🏷️ Tarjeta Kanban Crucianelli")
                        qr_data = f"KANBAN|{k_code}|MAT:{mat_code}|DEST:{puesto_dest}"
                        qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_data)}&size=160"
                        
                        # Vista previa de etiqueta
                        st.image(qr_url, caption=f"QR {k_code}", width=130)
                        
                        # 1. Botón para enviar por Red Wi-Fi (Socket direct a IP)
                        if st.button("⚡ Imprimir por Red Wi-Fi (IP Brother)", key=f"btn_ip_{idx}", type="primary"):
                            exito, msg = enviar_a_impresora_brother(
                                printer_ip, k_code, mat_code, row.get('Almacén Origen'), puesto_dest, qr_data
                            )
                            if exito:
                                st.success(msg)
                            else:
                                st.warning(f"{msg} Utilice el botón alternativo de diálogo de impresión.")

                        # 2. Botón alternativo de impresión del navegador
                        btn_print_html = f"""
                        <script>
                        function imprimirEtiqueta_{idx}() {{
                            var contenido = `
                            <div style="width: 103mm; border: 2px solid #000; padding: 10px; font-family: Arial; background: #fff; color: #000;">
                                <h3>CRUCIANELLI KANBAN - {k_code}</h3>
                                <p><strong>Material:</strong> {mat_code}</p>
                                <p><strong>Origen:</strong> {row.get('Almacén Origen')} | <strong>Destino:</strong> {puesto_dest}</p>
                                <img src="{qr_url}" style="width: 100px;">
                            </div>`;
                            var ventana = window.open('', '', 'height=500,width=600');
                            ventana.document.write('<html><head><style>@page {{ size: 103mm auto; margin: 0; }}</style></head><body>');
                            ventana.document.write(contenido);
                            ventana.document.write('</body></html>');
                            ventana.document.close();
                            ventana.focus();
                            setTimeout(function() {{ ventana.print(); ventana.close(); }}, 500);
                        }}
                        </script>
                        <button onclick="imprimirEtiqueta_{idx}()" style="background-color: #555; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; margin-top: 5px; width: 100%;">
                            🌐 Imprimir vía Diálogo de Navegador
                        </button>
                        """
                        components.html(btn_print_html, height=45)

                with col2:
                    usr_log = st.session_state['usuario']['email']
                    now_str = datetime.now(ARG_TZ).strftime("%Y-%m-%d %H:%M:%S")
                    
                    sap_ok = (str(row.get('Estado SAP')).upper() == 'OK')
                    check_sap = st.checkbox("💻 Carga en Sistema SAP realizada", value=sap_ok, key=f"sap_chk_{idx}")
                    
                    imp_ok = (str(row.get('Estado Impresion')).upper() == 'OK')
                    check_imp = st.checkbox("🖨️ Impresión y etiqueta pegada", value=imp_ok, key=f"imp_chk_{idx}")

                    pst_ok = (str(row.get('Estado Puesto')).upper() == 'OK')
                    check_pst = st.checkbox("📍 Llevado al puesto de trabajo destino", value=pst_ok, key=f"pst_chk_{idx}")
                    
                    if check_sap != sap_ok or check_imp != imp_ok or check_pst != pst_ok:
                        df_trk.loc[idx, 'Estado SAP'] = 'OK' if check_sap else 'PENDIENTE'
                        df_trk.loc[idx, 'Fecha SAP'] = now_str if check_sap else '-'
                        df_trk.loc[idx, 'Usuario SAP'] = usr_log if check_sap else '-'
                        
                        df_trk.loc[idx, 'Estado Impresion'] = 'OK' if check_imp else 'PENDIENTE'
                        df_trk.loc[idx, 'Fecha Impresion'] = now_str if check_imp else '-'
                        df_trk.loc[idx, 'Usuario Impresion'] = usr_log if check_imp else '-'

                        df_trk.loc[idx, 'Estado Puesto'] = 'OK' if check_pst else 'PENDIENTE'
                        df_trk.loc[idx, 'Fecha Puesto'] = now_str if check_pst else '-'
                        df_trk.loc[idx, 'Usuario Puesto'] = usr_log if check_pst else '-'

                        nuevo_est = obtener_estado_general(df_trk.loc[idx])
                        df_trk.loc[idx, 'Estado Logístico'] = nuevo_est
                        
                        if nuevo_est == "COMPLETADO":
                            df_trk.loc[idx, 'Fecha Ejecución Logística'] = now_str
                            df_trk.loc[idx, 'Usuario Logística'] = usr_log
                        else:
                            df_trk.loc[idx, 'Fecha Ejecución Logística'] = '-'
                            df_trk.loc[idx, 'Usuario Logística'] = '-'

                        df_trk.to_csv(TRACKER_FILE, index=False)
                        st.toast(f"Estado actualizado a: {nuevo_est}", icon="💾")
                        st.rerun()

                st.caption(f"SAP: {df_trk.loc[idx, 'Estado SAP']} | Impresión: {df_trk.loc[idx, 'Estado Impresion']} | En Puesto: {df_trk.loc[idx, 'Estado Puesto']}")

    st.markdown("---")
    st.dataframe(df_show, use_container_width=True)

else:
    st.info("No hay solicitudes registradas aún en el Tracker Logístico.")