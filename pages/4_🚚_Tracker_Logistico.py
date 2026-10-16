import streamlit as st
import pandas as pd
import urllib.parse
from utils.style import aplicar_estilo_enterprise
from src.services.db_service import obtener_tracker_df

aplicar_estilo_enterprise()

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

st.subheader("🚚 Tracker de Ejecución Logística")

with st.sidebar:
    st.markdown("### 🖨️ Configuración Impresora")
    printer_ip = st.text_input("IP Rotuladora Brother (Wi-Fi):", value="192.168.1.150", help="Dirección IP asignada a la Brother QL-1110NWB en la red de la planta.")

df_trk = obtener_tracker_df()

if df_trk.empty:
    st.info("ℹ️ No hay tareas ni solicitudes pendientes registradas en el Tracker Logístico.")
else:
    # Sanitizar columnas de estado
    if 'Estado SAP' not in df_trk.columns: df_trk['Estado SAP'] = 'NO'
    if 'Estado Impresion' not in df_trk.columns: df_trk['Estado Impresion'] = 'NO'
    if 'Estado Puesto' not in df_trk.columns: df_trk['Estado Puesto'] = 'Pendiente'

    def calcular_estado_general(row):
        sap = str(row.get('Estado SAP', '')).upper() == 'SI'
        imp = str(row.get('Estado Impresion', '')).upper() == 'SI'
        pst = str(row.get('Estado Puesto', '')).upper() in ['OK', 'COMPLETADO', 'SI']
        
        c = sum([sap, imp, pst])
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
            k_code = str(row.get('Código K', '-')).strip().upper()
            mat_code = str(row.get('Material', '-')).strip().upper()
            action_type = str(row.get('Tipo de Acción', 'ACCIÓN')).strip().upper()
            puesto_dest = str(row.get('Puesto Destino', '-')).strip().upper()
            est_gen = str(row.get('Estado General', 'PENDIENTE'))
            solicitante = str(row.get('Usuario Solicitante', 'Sistema'))
            f_sol = str(row.get('Fecha Solicitud', '-'))

            badge = "🔴" if est_gen == "PENDIENTE" else ("🟡" if est_gen == "EN PROCESO" else "🟢")

            with st.expander(f"{badge} [{action_type}] Código K: {k_code} | Material: {mat_code} | Destino: {puesto_dest} ({est_gen})"):
                c1, c2 = st.columns([2, 1])
                with c1:
                    st.write(f"**Fecha Solicitud:** `{f_sol}`")
                    st.write(f"**Solicitante:** `{solicitante}`")
                    st.write(f"**Acción Requerida:** `{row.get('Acción Requerida', '-')}`")
                    st.write(f"**Medio Físico:** `{row.get('Medio', '-')}`")
                    st.write(f"**Puesto Destino:** `{puesto_dest}`")
                
                with c2:
                    st.markdown("##### 🏷️ Etiqueta Kanban")
                    qr_data = f"KANBAN|{k_code}|MAT:{mat_code}|DEST:{puesto_dest}"
                    qr_url = f"https://quickchart.io/qr?text={urllib.parse.quote(qr_data)}&size=140"
                    st.image(qr_url, width=140)