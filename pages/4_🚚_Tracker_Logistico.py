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

# Configuración de IP de la rotuladora Brother en la barra lateral
with st.sidebar:
    st.markdown("### 🖨️ Configuración Impresora")
    printer_ip = st.text_input("IP Rotuladora Brother (Wi-Fi):", value="192.168.1.150", help="Dirección IP asignada a la Brother QL-1110NWB en la red de la planta.")

TRACKER_FILE = "tracker_ejecucion.csv"
DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

# Cargar catálogo máster para obtener Lotes de Reposición y Punto de Pedido
dict_cantidades = {}
if os.path.exists(DB_FILE):
    try:
        df_master = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
        for _, r_m in df_master.iterrows():
            k_num = str(r_m.get('N° Etiquetas', '')).strip().upper()
            c_repo = str(r_m.get('Cantidad Reposicion', '-'))
            c_pp = str(r_m.get('Cantidad Punto de Pedido', '-'))
            unidad = str(r_m.get('Unidad Reposicion', 'UN'))
            dict_cantidades[k_num] = {
                'repo': f"{c_repo} {unidad}".strip(),
                'pp': f"{c_pp} {unidad}".strip() if c_pp not in ['-', '0', '0.0', 'nan', ''] else None
            }
    except Exception:
        pass

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
            k_code = str(row.get('Código K', '-')).strip().upper()
            mat_code = str(row.get('Material', '-'))
            action_type = str(row.get('Tipo de Acción', 'ACCIÓN'))
            puesto_dest = str(row.get('Puesto Destino', '-'))
            est_log = str(row.get('Estado Logístico', 'PENDIENTE'))
            
            # Recuperar lotes
            datos_k = dict_cantidades.get(k_code, {'repo': 'Consultar Tabla', 'pp': None})
            lote_repo_str = datos_k['repo']
            lote_pp_str = datos_k['pp']
            
            badge = "🔴" if est_log == "PENDIENTE" else ("🟡" if est_log == "EN PROCESO" else "🟢")
            
            with st.expander(f"{badge} [{action_type}] Código K: {k_code} | Material: {mat_code} | Destino: {puesto_dest} ({est_log})"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Fecha Solicitud:** `{row.get('Fecha Solicitud')}`")
                    st.write(f"**Solicitante:** `{row.get('Usuario Solicitante')}`")
                    det_val = str(row.get('Detalle', row.get('Detalle / Observaciones', '-')))
                    st.markdown(f"**Detalle de Cambios:** `{det_val}`")
                    st.write(f"**Ubicación:** Origen `{row.get('Almacén Origen')}` ➔ Destino `{puesto_dest}`")
                    
                    # --- VISTA E IMPRESIÓN DE ETIQUETA BROTHER (103mm) CON LOTES ---
                    with st.popover("🖨️ Ver / Imprimir Etiqueta Kanban"):
                        st.markdown("### 🏷️ Tarjeta Kanban Crucianelli")
                        qr_data = f"KANBAN|{k_code}|MAT:{mat_code}|DEST:{puesto_dest}|REPO:{lote_repo_str}"
                        qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_data)}&size=160"
                        
                        html_pp = f"<br><strong>Punto de Pedido:</strong> {lote_pp_str}" if lote_pp_str else ""
                        
                        # Maquetado adaptado para impresoras Brother QL (ancho continuo 103mm)
                        html_etiqueta = f"""
                        <div id="print-area-{idx}" style="
                            width: 103mm; 
                            border: 2px solid #000; 
                            padding: 10px; 
                            font-family: Arial, sans-serif; 
                            background-color: #ffffff; 
                            color: #000000;
                            border-radius: 6px;
                            margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000; padding-bottom: 5px;">
                                <span style="font-size: 16px; font-weight: bold;">CRUCIANELLI KANBAN</span>
                                <span style="font-size: 14px; font-weight: bold; background: #000; color: #fff; padding: 2px 6px; border-radius: 3px;">{k_code}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                                <div style="font-size: 13px; line-height: 1.4;">
                                    <strong>Material:</strong> <span style="font-size: 15px; font-weight: bold;">{mat_code}</span><br>
                                    <strong>Origen:</strong> {row.get('Almacén Origen')} | <strong>Destino:</strong> <span style="font-size: 14px; font-weight: bold;">{puesto_dest}</span><br>
                                    <strong>Lote Reposición:</strong> <span style="font-size: 14px; font-weight: bold; color: #2b5c8f;">{lote_repo_str}</span>{html_pp}
                                </div>
                                <div>
                                    <img src="{qr_url}" style="width: 90px; height: 90px;">
                                </div>
                            </div>
                        </div>
                        """
                        
                        components.html(html_etiqueta, height=200)
                        
                        # Botón para enviar por Red Wi-Fi (Socket direct a IP)
                        if st.button("⚡ Imprimir por Red Wi-Fi (IP Brother)", key=f"btn_ip_{idx}", type="primary"):
                            exito, msg = enviar_a_impresora_brother(
                                printer_ip, k_code, mat_code, row.get('Almacén Origen'), puesto_dest, qr_data
                            )
                            if exito:
                                st.success(msg)
                            else:
                                st.warning(f"{msg} Utilice el botón de diálogo de impresión.")

                        # Botón alternativo de impresión del navegador
                        btn_print_html = f"""
                        <script>
                        function imprimirEtiqueta_{idx}() {{
                            var contenido = document.getElementById("print-area-{idx}").outerHTML;
                            var ventana = window.open('', '', 'height=500,width=600');
                            ventana.document.write('<html><head><title>Imprimir Etiqueta {k_code}</title>');
                            ventana.document.write('<style>@page {{ size: 103mm auto; margin: 0; }} body {{ margin: 5px; }}</style>');
                            ventana.document.write('</head><body>');
                            ventana.document.write(contenido);
                            ventana.document.write('</body></html>');
                            ventana.document.close();
                            ventana.focus();
                            setTimeout(function() {{ ventana.print(); ventana.close(); }}, 500);
                        }}
                        </script>
                        <button onclick="imprimirEtiqueta_{idx}()" style="
                            background-color: #555; 
                            color: white; 
                            padding: 6px 12px; 
                            border: none; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            margin-top: 5px; 
                            width: 100%;">
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