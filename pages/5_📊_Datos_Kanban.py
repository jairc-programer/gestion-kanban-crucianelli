import streamlit as st
import pandas as pd
import io
import urllib.parse
import streamlit.components.v1 as components
from datetime import datetime
from utils.style import aplicar_estilo_enterprise, formatear_fecha_arg, obtener_ahora_arg
from src.services.db_service import obtener_kanbans_df, obtener_auditoria_df

# Aplicar estilo visual Enterprise
aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("📊 Base General de Kanbans")

# Cargar catálogo máster e historial de auditoría directamente desde Supabase
df_live = obtener_kanbans_df()
df_aud = obtener_auditoria_df()

if not df_live.empty:
    ahora_actual = obtener_ahora_arg().replace(tzinfo=None)

    # --- 1. DETERMINAR FECHA DE ALTA (CREACIÓN INICIAL) ---
    dict_fechas_alta = {}
    if not df_aud.empty and 'Código K' in df_aud.columns and 'Fecha y Hora' in df_aud.columns:
        # Agrupar auditoría por Código K y obtener el evento más antiguo (Creación / Primer registro)
        aud_ordenado = df_aud.sort_values(by='Fecha y Hora', ascending=True)
        dict_fechas_alta = aud_ordenado.groupby('Código K')['Fecha y Hora'].first().to_dict()

    def obtener_fecha_alta(row):
        k_code = str(row.get('N° Etiquetas', '')).strip().upper()
        if k_code in dict_fechas_alta:
            return dict_fechas_alta[k_code]
        # Respaldo: Si no tiene historial previo, la fecha de alta coincide con su fecha registrada
        return row.get('Fecha Modificación', None)

    df_live['Fecha de Alta'] = df_live.apply(obtener_fecha_alta, axis=1)

    # --- 2. LÓGICA DE CLASIFICACIÓN TIPO SEMÁFORO SEGÚN INACTIVIDAD ---
    def evaluar_inactividad(fecha_val):
        if pd.isna(fecha_val) or str(fecha_val).strip() in ['-', '', 'nan', 'None', 'NaT']:
            return "🔴 Inactivo (> 6 meses)"
        try:
            dt = pd.to_datetime(fecha_val)
            if hasattr(dt, 'tz') and dt.tz is not None:
                dt = dt.tz_localize(None)
            
            dias_transcurridos = (ahora_actual - dt).days

            if dias_transcurridos <= 90:
                return "🟢 Activo Reciente (<= 3 meses)"
            elif 90 < dias_transcurridos <= 180:
                return "🟡 Moderado (3 a 6 meses)"
            else:
                return "🔴 Inactivo (> 6 meses)"
        except Exception:
            return "🔴 Inactivo (> 6 meses)"

    if 'Fecha Modificación' in df_live.columns:
        df_live['Estado de Actividad'] = df_live['Fecha Modificación'].apply(evaluar_inactividad)
        df_live['Última Modificación'] = df_live['Fecha Modificación'].apply(formatear_fecha_arg)
        df_live['Fecha de Alta'] = df_live['Fecha de Alta'].apply(formatear_fecha_arg)
        
        # Eliminar columna duplicada antigua
        if 'Última Actualización' in df_live.columns:
            df_live.drop(columns=['Última Actualización'], inplace=True)
        if 'Fecha Modificación' in df_live.columns:
            df_live.drop(columns=['Fecha Modificación'], inplace=True)
    else:
        df_live['Estado de Actividad'] = "🔴 Inactivo (> 6 meses)"
        df_live['Última Modificación'] = "Sin Fecha"
        df_live['Fecha de Alta'] = "Sin Fecha"

    # --- FILTROS DE BÚSQUEDA ---
    with st.container(border=True):
        st.markdown("##### 🔍 Filtros de Búsqueda")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            filtro_k = st.text_input("🔍 Código Kanban:", placeholder="ej. K00000023").strip().upper()
        with c2:
            filtro_mat = st.text_input("🔍 Código Material:", placeholder="ej. CM001462").strip().upper()
        with c3:
            filtro_est = st.selectbox(
                "Status Actividad:", 
                [
                    "TODOS", 
                    "🟢 Activo Reciente (<= 3 meses)", 
                    "🟡 Moderado (3 a 6 meses)", 
                    "🔴 Inactivo (> 6 meses)"
                ]
            )

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
            st.info("ℹ️ Etiqueta adaptada al ancho completo del papel autoadhesivo de 103mm x 50mm.")
        
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
                st.markdown("##### 🏷️ Vista Previa de Etiqueta (103mm x 50mm)")
                
                # Payload codificado para SAP MIGO Movimiento 313
                qr_payload_sap = f"MIGO|313|M:{mat_code}|C:{c_repo_val}|O:{alm_origen_val}|D:{alm_dest_val}|K:{k_code}"
                qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_payload_sap)}&size=150"
                
                linea_pp_html = f"<div><b>Lote Punto Pedido:</b> {c_pp_val}</div>" if tipo_kb_val == "TARJETA" else ""

                # HTML/CSS optimizado para ocupación total del área de impresión (103x50mm)
                html_etiqueta = f"""
                <div id="print_area_103x50" style="
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
                        <span style="font-size: 13px; font-weight: 900; color: #000000; letter-spacing: 0.3px;">TALLERES METALÚRGICOS CRUCIANELLI</span>
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
                    <button onclick="imprimirEtiqueta103x50()" style="
                        background-color: #d62828; 
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
                    var ventana = window.open('', '', 'height=400,width=500');
                    ventana.document.write('<html><head><title>Etiqueta {k_code}</title>');
                    ventana.document.write('<style>');
                    ventana.document.write('@page {{ size: 103mm 50mm; margin: 0mm; }}');
                    ventana.document.write('html, body {{ margin: 0; padding: 0; width: 103mm; height: 50mm; overflow: hidden; background: #ffffff; display: flex; align-items: center; justify-content: center; }}');
                    ventana.document.write('#print_area_103x50 {{ width: 100% !important; height: 100% !important; border: none !important; }}');
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

else:
    st.info("ℹ️ No se encontraron registros en la base de datos de Supabase.")