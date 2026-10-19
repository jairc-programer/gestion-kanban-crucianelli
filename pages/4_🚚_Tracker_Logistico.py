import streamlit as st
import pandas as pd
import urllib.parse
import streamlit.components.v1 as components
from utils.style import aplicar_estilo_enterprise, formatear_fecha_arg, obtener_ahora_arg
from src.services.db_service import obtener_tracker_df, obtener_kanbans_df
from src.database.connection import get_db_session
from src.database.models import TrackerSolicitud

aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("🚚 Tracker de Ejecución Logística")

# Cargar tablas de referencia desde Supabase
df_trk = obtener_tracker_df()
df_kb = obtener_kanbans_df()

if df_trk.empty:
    st.info("ℹ️ No hay tareas ni solicitudes pendientes registradas en el Tracker Logístico.")
else:
    def es_si(val):
        return str(val).strip().upper() in ['SI', 'OK', 'COMPLETADO', 'TRUE', '1']

    def calcular_estado_general(row):
        c_sap = es_si(row.get('Estado SAP', 'NO'))
        c_imp = es_si(row.get('Estado Impresion', 'NO'))
        c_pst = es_si(row.get('Estado Puesto', 'Pendiente'))
        
        c = sum([c_sap, c_imp, c_pst])
        if c == 3:
            return "COMPLETADO"
        elif c > 0:
            return "EN PROCESO"
        return "PENDIENTE"

    df_trk['Estado General'] = df_trk.apply(calcular_estado_general, axis=1)

    estado_filter = st.radio("Filtrar por Estado:", ["TODOS", "PENDIENTES", "COMPLETADOS"], horizontal=True)

    if estado_filter == "PENDIENTES":
        df_show = df_trk[df_trk['Estado General'].isin(['PENDIENTE', 'EN PROCESO'])]
    elif estado_filter == "COMPLETADOS":
        df_show = df_trk[df_trk['Estado General'] == 'COMPLETADO']
    else:
        df_show = df_trk.copy()

    st.markdown("##### 📋 Tareas Solicitadas por Procesos")
    
    if df_show.empty:
        st.info("ℹ️ No se encontraron tareas para el filtro seleccionado.")
    else:
        for idx, row in df_show.iterrows():
            sol_id = str(row.get('ID Solicitud', f"row_{idx}"))
            k_code = str(row.get('Código K', '-')).strip().upper()
            mat_code = str(row.get('Material', '-')).strip().upper()
            action_type = str(row.get('Tipo de Acción', 'ACCIÓN')).strip().upper()
            puesto_dest = str(row.get('Puesto Destino', '-')).strip().upper()
            est_gen = str(row.get('Estado General', 'PENDIENTE'))
            solicitante = str(row.get('Usuario Solicitante', 'Sistema'))
            
            # Formatear la fecha a zona horaria de Argentina
            f_sol = formatear_fecha_arg(row.get('Fecha Solicitud'))

            # Cruce dinámico con la base máster para extraer especificaciones técnicas
            kb_match = df_kb[df_kb['N° Etiquetas'].fillna('').astype(str).str.upper() == k_code] if not df_kb.empty else pd.DataFrame()
            
            if not kb_match.empty:
                info_kb = kb_match.iloc[0]
                tipo_kb_val = str(info_kb.get('Tipo Kanban', 'TARJETA')).strip().upper()
                c_repo_val = str(info_kb.get('Cantidad Reposicion', '-'))
                c_pp_val = str(info_kb.get('Cantidad Punto de Pedido', '-'))
                alm_origen_val = str(info_kb.get('Almacén Origen', info_kb.get('Almacen Origen', '-'))).strip().upper()
                alm_dest_val = str(info_kb.get('Almacén Destino', info_kb.get('Almacen Destino', '-'))).strip().upper()
            else:
                tipo_kb_val = "TARJETA"
                c_repo_val = "-"
                c_pp_val = "-"
                alm_origen_val = "-"
                alm_dest_val = "-"

            st_sap = es_si(row.get('Estado SAP'))
            st_imp = es_si(row.get('Estado Impresion'))
            st_pst = es_si(row.get('Estado Puesto'))

            badge = "🔴" if est_gen == "PENDIENTE" else ("🟡" if est_gen == "EN PROCESO" else "🟢")

            with st.expander(f"{badge} [{action_type}] Código K: {k_code} | Material: {mat_code} | Destino: {puesto_dest} ({est_gen})"):
                c1, c_checks, c2 = st.columns([1.8, 1.8, 1.4])
                
                # --- DATOS DE LA SOLICITUD ---
                with c1:
                    st.write(f"**Fecha Solicitud:** `{f_sol}`")
                    st.write(f"**Solicitante:** `{solicitante}`")
                    st.write(f"**Acción Requerida:** `{row.get('Acción Requerida', '-')}`")
                    st.write(f"**Medio Físico:** `{row.get('Medio', '-')}`")
                    st.write(f"**Almacén Origen:** `{alm_origen_val}`")
                    st.write(f"**Puesto Destino:** `{puesto_dest}`")
                    st.write(f"**Lote Reposición:** `{c_repo_val}`")
                    if tipo_kb_val == "TARJETA":
                        st.write(f"**Punto Pedido:** `{c_pp_val}`")
                
                # --- CONTROLES DE VERIFICACIÓN / CHECKS ---
                with c_checks:
                    st.markdown("##### ⚙️ Acciones Logística")
                    
                    # 1. Check Carga en SAP
                    chk1 = st.checkbox("1. Carga en SAP", value=st_sap, key=f"sap_{sol_id}_{idx}")
                    if chk1 != st_sap:
                        with get_db_session() as db:
                            t_sol = db.query(TrackerSolicitud).filter(TrackerSolicitud.id_solicitud == sol_id).first()
                            if t_sol:
                                t_sol.cargado_sap = "SI" if chk1 else "NO"
                                db.commit()
                        st.toast(f"✅ Estado SAP actualizado para {k_code}", icon="💾")
                        st.rerun()

                    # 2. Check Impresión de Etiqueta
                    chk2 = st.checkbox("2. Etiqueta Impresa", value=st_imp, key=f"imp_{sol_id}_{idx}")
                    if chk2 != st_imp:
                        with get_db_session() as db:
                            t_sol = db.query(TrackerSolicitud).filter(TrackerSolicitud.id_solicitud == sol_id).first()
                            if t_sol:
                                t_sol.impreso = "SI" if chk2 else "NO"
                                t_sol.fecha_impresion = obtener_ahora_arg() if chk2 else None
                                db.commit()
                        st.toast(f"✅ Estado Impresión actualizado para {k_code}", icon="🖨️")
                        st.rerun()

                    # 3. Check Ubicación física en Puesto
                    chk3 = st.checkbox("3. Kanban en Puesto Destino", value=st_pst, key=f"pst_{sol_id}_{idx}")
                    if chk3 != st_pst:
                        with get_db_session() as db:
                            t_sol = db.query(TrackerSolicitud).filter(TrackerSolicitud.id_solicitud == sol_id).first()
                            if t_sol:
                                t_sol.estado_fisico = "OK" if chk3 else "Pendiente"
                                t_sol.fecha_finalizacion = obtener_ahora_arg() if chk3 else None
                                db.commit()
                        st.toast(f"✅ Ubicación física registrada para {k_code}", icon="📍")
                        st.rerun()

                # --- TARJETA ETIQUETA E IMPRESIÓN DIRECTA (NUEVO FORMATO ESTÁNDAR 103x50mm) ---
                with c2:
                    st.markdown("##### 🏷️ Etiqueta Kanban (103x50 mm)")
                    
                    # Payload codificado para SAP MIGO Movimiento 313
                    qr_payload_sap = f"MIGO|313|M:{mat_code}|C:{c_repo_val}|O:{alm_origen_val}|D:{alm_dest_val}|K:{k_code}"
                    qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_payload_sap)}&size=150"

                    linea_pp_html = f"<div><b>Lote Punto Pedido:</b> {c_pp_val}</div>" if tipo_kb_val == "TARJETA" else ""
                    
                    html_etiqueta = f"""
                    <div id="print_area_{idx}" style="
                        width: 385px; 
                        height: 180px; 
                        border: 2px solid #000000; 
                        border-radius: 4px; 
                        padding: 8px 12px; 
                        background-color: #FFFFFF; 
                        color: #000000; 
                        font-family: Arial, sans-serif; 
                        box-sizing: border-box;
                        display: flex;
                        flex-direction: column;
                        justify-content: space-between;
                    ">
                        <!-- CABECERA INSTITUCIONAL -->
                        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #000000; padding-bottom: 4px;">
                            <span style="font-size: 12px; font-weight: 900; color: #000000; letter-spacing: 0.3px;">TALLERES METALÚRGICOS CRUCIANELLI</span>
                            <span style="font-size: 11px; font-weight: bold; border: 1px solid #000000; color: #000000; padding: 2px 6px; border-radius: 3px;">{tipo_kb_val}</span>
                        </div>

                        <!-- CUERPO PRINCIPAL -->
                        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 6px;">
                            <!-- INFORMACIÓN TÉCNICA -->
                            <div style="text-align: left; font-size: 13px; line-height: 1.4;">
                                <div style="font-size: 18px; font-weight: bold; color: #000000; margin-bottom: 3px;">{k_code}</div>
                                <div><b>Material:</b> <span style="font-size: 14px; font-weight: bold;">{mat_code}</span></div>
                                <div><b>Lote Reposición:</b> <span style="font-size: 13px; font-weight: bold;">{c_repo_val}</span></div>
                                {linea_pp_html}
                                <div><b>Origen:</b> {alm_origen_val} &rarr; <b>Destino:</b> {alm_dest_val}</div>
                                <div><b>Puesto Destino:</b> <span style="font-size: 13px; font-weight: bold;">{puesto_dest}</span></div>
                            </div>

                            <!-- CÓDIGO QR PARA LECTOR DE SAP -->
                            <div style="text-align: center; margin-right: 5px;">
                                <img src="{qr_url}" width="125" height="125" style="display: block; margin: 0 auto;" />
                            </div>
                        </div>
                    </div>

                    <!-- BOTÓN IMPRIMIR -->
                    <div style="margin-top: 10px; text-align: left;">
                        <button onclick="imprimirEtiqueta_{idx}()" style="
                            background-color: #d62828; 
                            color: white; 
                            border: none; 
                            padding: 8px 16px; 
                            border-radius: 4px; 
                            cursor: pointer; 
                            font-weight: bold; 
                            font-size: 13px;
                        ">
                            🖨️ Imprimir Etiqueta
                        </button>
                    </div>

                    <script>
                    function imprimirEtiqueta_{idx}() {{
                        var contenido = document.getElementById('print_area_{idx}').outerHTML;
                        var ventana = window.open('', '', 'height=400,width=500');
                        ventana.document.write('<html><head><title>Etiqueta {k_code}</title>');
                        ventana.document.write('<style>');
                        ventana.document.write('@page {{ size: 103mm 50mm; margin: 0mm; }}');
                        ventana.document.write('html, body {{ margin: 0; padding: 0; width: 103mm; height: 50mm; overflow: hidden; background: #ffffff; display: flex; align-items: center; justify-content: center; }}');
                        ventana.document.write('#print_area_{idx} {{ width: 100% !important; height: 100% !important; border: none !important; }}');
                        ventana.document.write('</style>');
                        ventana.document.write('</head><body>');
                        ventana.document.write(contenido);
                        ventana.document.write('</body></html>');
                        ventana.document.close();
                        ventana.focus();
                        setTimeout(function() {{ ventana.print(); ventana.close(); }}, 400);
                    }}
                    </script>
                    """
                    components.html(html_etiqueta, height=250)