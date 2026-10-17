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
    st.markdown("### 🖨️ Reimpresión de Etiqueta (Por Rotura / Deterioro)")
    
    lista_k_disponibles = sorted(df_live['N° Etiquetas'].dropna().astype(str).unique().tolist()) if 'N° Etiquetas' in df_live.columns else []
    
    if lista_k_disponibles:
        col_sel, col_prev = st.columns([1.5, 2])
        
        with col_sel:
            k_seleccionado = st.selectbox("Seleccionar Código Kanban a Reimprimir:", options=lista_k_disponibles)
            st.info("ℹ️ Utiliza esta sección cuando necesites reemplazar una etiqueta física deteriorada en planta sin realizar modificaciones en el sistema.")
        
        if k_seleccionado:
            kb_info = df_live[df_live['N° Etiquetas'].astype(str) == k_seleccionado].iloc[0]
            
            k_code = str(kb_info.get('N° Etiquetas', '-')).strip().upper()
            mat_code = str(kb_info.get('Material', '-')).strip().upper()
            tipo_kb_val = str(kb_info.get('Tipo Kanban', 'TARJETA')).strip().upper()
            c_repo_val = str(kb_info.get('Cantidad Reposicion', '-'))
            c_pp_val = str(kb_info.get('Cantidad Punto de Pedido', '-'))
            alm_origen_val = str(kb_info.get('Almacén Origen', '-'))
            puesto_dest = str(kb_info.get('Puesto de trabajo destino', kb_info.get('Puesto Destino', '-'))).strip().upper()

            with col_prev:
                st.markdown("##### 🏷️ Vista Previa e Impresión")
                
                # Payload dinámico para el QR
                if tipo_kb_val == "TARJETA":
                    qr_payload = f"KANBAN|{k_code}|MAT:{mat_code}|REPO:{c_repo_val}|PP:{c_pp_val}|ORIG:{alm_origen_val}|DEST:{puesto_dest}"
                else:
                    qr_payload = f"KANBAN|{k_code}|MAT:{mat_code}|REPO:{c_repo_val}|ORIG:{alm_origen_val}|DEST:{puesto_dest}"
                    
                qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_payload)}&size=120"
                linea_pp_html = f"<p style='margin:2px 0;'><b>Punto Pedido:</b> {c_pp_val}</p>" if tipo_kb_val == "TARJETA" else ""

                html_etiqueta = f"""
                <div id="print_area_db" style="border: 2px solid #2b5c8f; border-radius: 6px; padding: 10px; background-color: #ffffff; color: #000000; font-family: Arial, sans-serif; text-align: center;">
                    <h4 style="margin: 0; color: #2b5c8f; font-size: 15px; font-weight: bold;">CRUCIANELLI KANBAN</h4>
                    <p style="margin: 2px 0; font-size: 14px; font-weight: bold;">{k_code} ({tipo_kb_val})</p>
                    <img src="{qr_url}" width="110" style="margin: 4px 0;" />
                    <div style="text-align: left; font-size: 11px; line-height: 1.25; border-top: 1px dashed #bbb; padding-top: 4px; margin-top: 4px;">
                        <p style="margin: 2px 0;"><b>Material:</b> {mat_code}</p>
                        <p style="margin: 2px 0;"><b>Lote Reposición:</b> {c_repo_val}</p>
                        {linea_pp_html}
                        <p style="margin: 2px 0;"><b>Origen:</b> {alm_origen_val} &rarr; <b>Destino:</b> {puesto_dest}</p>
                    </div>
                </div>
                <div style="text-align: center; margin-top: 8px;">
                    <button onclick="imprimirEtiquetaDB()" style="background-color: #2b5c8f; color: white; border: none; padding: 7px 14px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 13px;">
                        🖨️ Imprimir Etiqueta
                    </button>
                </div>
                <script>
                function imprimirEtiquetaDB() {{
                    var contenido = document.getElementById('print_area_db').innerHTML;
                    var ventana = window.open('', '', 'height=450,width=380');
                    ventana.document.write('<html><head><title>Reimprimir {k_code}</title>');
                    ventana.document.write('<style>body{{font-family:Arial,sans-serif;text-align:center;padding:15px;}}</style>');
                    ventana.document.write('</head><body>');
                    ventana.document.write(contenido);
                    ventana.document.write('</body></html>');
                    ventana.document.close();
                    ventana.focus();
                    setTimeout(function() {{ ventana.print(); ventana.close(); }}, 400);
                }}
                </script>
                """
                components.html(html_etiqueta, height=350)

else:
    st.info("ℹ️ No se encontraron registros en la base de datos de Supabase.")