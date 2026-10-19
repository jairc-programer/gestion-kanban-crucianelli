import streamlit as st
import pandas as pd
import io
import urllib.parse
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_kanbans_df

# Aplicar estilo visual Enterprise
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📊 Base General de Kanbans")

# Cargar catálogo directamente desde Supabase
df_live = obtener_kanbans_df()

if not df_live.empty:
    # --- INDICADOR DE INACTIVIDAD (> 6 MESES / 180 DÍAS) ---
    fecha_limite = datetime.now() - timedelta(days=180)

    def evaluar_inactividad(fecha_val):
        if pd.isna(fecha_val) or str(fecha_val).strip() in ['-', '', 'nan', 'None']:
            return "🔴 Inactivo (> 6 meses)"
        try:
            dt = pd.to_datetime(fecha_val)
            if hasattr(dt, 'tz') and dt.tz is not None:
                dt = dt.tz_localize(None)
            if dt < fecha_limite:
                return "🔴 Inactivo (> 6 meses)"
            return "🟢 Activo Reciente"
        except Exception:
            return "🔴 Inactivo (> 6 meses)"

    if 'Fecha Modificación' in df_live.columns:
        df_live['Estado de Actividad'] = df_live['Fecha Modificación'].apply(evaluar_inactividad)
        df_live['Última Actualización'] = df_live['Fecha Modificación'].fillna('Sin Fecha')
    else:
        df_live['Estado de Actividad'] = "🔴 Inactivo (> 6 meses)"
        df_live['Última Actualización'] = "Sin Fecha"

    # --- FILTROS DE BÚSQUEDA ---
    with st.container(border=True):
        st.markdown("##### 🔍 Filtros de Búsqueda")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            filtro_k = st.text_input("🔍 Código Kanban:", placeholder="ej. K00000023").strip().upper()
        with c2:
            filtro_mat = st.text_input("🔍 Código Material:", placeholder="ej. CM001462").strip().upper()
        with c3:
            filtro_est = st.selectbox("Status Actividad:", ["TODOS", "🟢 Activo Reciente", "🔴 Inactivo (> 6 meses)"])

    df_filtrado = df_live.copy()

    if filtro_k and 'N° Etiquetas' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['N° Etiquetas'].fillna('').astype(str).str.upper().str.contains(filtro_k)]
        
    if filtro_mat and 'Material' in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado['Material'].fillna('').astype(str).str.upper().str.contains(filtro_mat)]

    if filtro_est != "TODOS":
        df_filtrado = df_filtrado[df_filtrado['Estado de Actividad'] == filtro_est]

    st.caption(f"Mostrando **{len(df_filtrado)}** de **{len(df_live)}** registros totales.")
    
    st.dataframe(df_filtrado, use_container_width=True)
    
    col_dl, col_blank = st.columns([1, 2])
    with col_dl:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, sheet_name="Kanbans CRUCIANELLI", index=False)
        
        st.download_button(
            label="📥 Descargar Tabla (.xlsx)", 
            data=output.getvalue(), 
            file_name="Datos_Kanban_Filtrado.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )

    # --- SECCIÓN DE REIMPRESIÓN DIRECTA DE ETIQUETA ---
    st.markdown("---")
    st.markdown("### 🖨️ Reimpresión de Etiqueta (Brother QL-1110NWB - 103mm x 50mm)")
    
    lista_k_disponibles = sorted(df_live['N° Etiquetas'].dropna().astype(str).unique().tolist()) if 'N° Etiquetas' in df_live.columns else []
    
    if lista_k_disponibles:
        col_sel, col_prev = st.columns([1.2, 2.8])
        
        with col_sel:
            k_seleccionado = st.selectbox("Seleccionar Código Kanban a Reimprimir:", options=lista_k_disponibles)
            st.info("ℹ️ Etiqueta configurada con parámetros SAP MIGO (Movimiento 313) para lectura automática por scanner en planta.")
        
        if k_seleccionado:
            kb_info = df_live[df_live['N° Etiquetas'].astype(str) == k_seleccionado].iloc[0]
            
            k_code = str(kb_info.get('N° Etiquetas', '-')).strip().upper()
            mat_code = str(kb_info.get('Material', '-')).strip().upper()
            tipo_kb_val = str(kb_info.get('Tipo Kanban', 'TARJETA')).strip().upper()
            c_repo_val = str(kb_info.get('Cantidad Reposicion', '-'))
            c_pp_val = str(kb_info.get('Cantidad Punto de Pedido', '-'))
            alm_origen_val = str(kb_info.get('Almacén Origen', kb_info.get('Almacen Origen', '-'))).strip().upper()
            alm_dest_val = str(kb_info.get('Almacén Destino', kb_info.get('Almacen Destino', '-'))).strip().upper()
            puesto_dest = str(kb_info.get('Puesto de trabajo destino', kb_info.get('Puesto Destino', '-'))).strip().upper()

            with col_prev:
                st.markdown("##### 🏷️ Vista Previa de Etiqueta (Format 103x50 mm)")
                
                # Payload codificado para SAP MIGO Movimiento 313
                qr_payload_sap = f"MIGO|313|M:{mat_code}|C:{c_repo_val}|O:{alm_origen_val}|D:{alm_dest_val}|K:{k_code}"
                qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_payload_sap)}&size=140"
                
                linea_pp_html = f"<div><b>Lote Punto Pedido:</b> {c_pp_val}</div>" if tipo_kb_val == "TARJETA" else ""

                # HTML/CSS optimizado para Brother QL-1110NWB (103mm x 50mm)
                html_etiqueta = f"""
                <div id="print_area_103x50" style="
                    width: 380px; 
                    height: 185px; 
                    border: 2px solid #1E222B; 
                    border-radius: 6px; 
                    padding: 8px 12px; 
                    background-color: #FFFFFF; 
                    color: #000000; 
                    font-family: Arial, sans-serif; 
                    box-sizing: border-box;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <!-- CABECERA -->
                    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2b5c8f; padding-bottom: 3px;">
                        <span style="font-size: 14px; font-weight: bold; color: #2b5c8f;">CRUCIANELLI KANBAN</span>
                        <span style="font-size: 13px; font-weight: bold; background-color: #2b5c8f; color: #ffffff; padding: 2px 6px; border-radius: 3px;">{tipo_kb_val}</span>
                    </div>

                    <!-- CUERPO CENTRAL -->
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 4px;">
                        <!-- INFORMACIÓN TÉCNICA -->
                        <div style="text-align: left; font-size: 12px; line-height: 1.35;">
                            <div style="font-size: 15px; font-weight: bold; color: #000000; margin-bottom: 2px;">{k_code}</div>
                            <div><b>Material:</b> <span style="font-size: 13px; font-weight: bold;">{mat_code}</span></div>
                            <div><b>Lote Reposición:</b> <span style="font-size: 12px; font-weight: bold;">{c_repo_val}</span></div>
                            {linea_pp_html}
                            <div><b>Origen:</b> {alm_origen_val} &rarr; <b>Destino:</b> {alm_dest_val}</div>
                            <div><b>Puesto Destino:</b> <span style="font-size: 12px; font-weight: bold; color: #d62828;">{puesto_dest}</span></div>
                        </div>

                        <!-- CÓDIGO QR PARA SAP MIGO -->
                        <div style="text-align: center;">
                            <img src="{qr_url}" width="115" height="115" style="display: block; margin: 0 auto;" />
                            <span style="font-size: 8px; color: #555; font-weight: bold; display: block; margin-top: 1px;">SAP MIGO 313</span>
                        </div>
                    </div>

                    <!-- PIE DE ETIQUETA -->
                    <div style="border-top: 1px dashed #888; padding-top: 2px; font-size: 9px; color: #444; display: flex; justify-content: space-between;">
                        <span>Mov: SAP 313 (Transferencia)</span>
                        <span>103mm x 50mm</span>
                    </div>
                </div>

                <!-- BOTÓN IMPRIMIR -->
                <div style="margin-top: 10px; text-align: left;">
                    <button onclick="imprimirEtiqueta103x50()" style="
                        background-color: #2b5c8f; 
                        color: white; 
                        border: none; 
                        padding: 8px 16px; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-weight: bold; 
                        font-size: 13px;
                    ">
                        🖨️ Imprimir Etiqueta (Brother QL-1110NWB)
                    </button>
                </div>

                <script>
                function imprimirEtiqueta103x50() {{
                    var contenido = document.getElementById('print_area_103x50').outerHTML;
                    var ventana = window.open('', '', 'height=400,width=480');
                    ventana.document.write('<html><head><title>Imprimir Etiqueta {k_code}</title>');
                    ventana.document.write('<style>');
                    ventana.document.write('@page {{ size: 103mm 50mm; margin: 0; }}');
                    ventana.document.write('body {{ font-family: Arial, sans-serif; margin: 0; padding: 5px; display: flex; justify-content: center; align-items: center; }}');
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
                components.html(html_etiqueta, height=270)

else:
    st.info("ℹ️ No se encontraron registros en la base de datos de Supabase.")