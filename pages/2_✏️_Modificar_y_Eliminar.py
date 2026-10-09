import streamlit as st
import pandas as pd
import os

if 'usuario' not in st.session_state or not st.session_state['usuario']:
    st.stop()

DB_FILE = "TablaZ.xlsx"
SHEET_NAME = "Kanbans CRUCIANELLI"

st.subheader("✏️ Modificar / 🗑️ Eliminar Kanban")

if os.path.exists(DB_FILE):
    df_live = pd.read_excel(DB_FILE, sheet_name=SHEET_NAME)
    
    col_mod, col_del = st.columns([2, 1])
    
    with col_mod:
        st.markdown("##### Modificar Registro")
        busqueda = st.text_input("Buscar por Material o Código K:").strip().upper()
        if busqueda:
            res = df_live[(df_live['Material'].astype(str).str.contains(busqueda)) | (df_live['N° Etiquetas'].astype(str).str.contains(busqueda))]
            if not res.empty:
                sel = st.selectbox("Seleccione Kanban:", res['N° Etiquetas'] + " - " + res['Material'])
                k_code = sel.split(" - ")[0]
                row = res[res['N° Etiquetas'] == k_code].iloc[0]
                
                n_cant = st.number_input("Nueva Cantidad Reposición", value=float(row['Cantidad Reposicion']))
                if st.button("Guardar Cambios"):
                    idx = df_live[df_live['N° Etiquetas'] == k_code].index[0]
                    df_live.loc[idx, 'Cantidad Reposicion'] = n_cant
                    with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                        df_live.to_excel(writer, sheet_name=SHEET_NAME, index=False)
                    st.success("Kanban modificado correctamente.")
                    st.rerun()

    with col_del:
        st.markdown("##### Eliminar Registro")
        k_del = st.text_input("Código K a eliminar:")
        if st.button("Eliminar", type="primary") and k_del:
            df_del = df_live[df_live['N° Etiquetas'] != k_del]
            with pd.ExcelWriter(DB_FILE, engine='openpyxl') as writer:
                df_del.to_excel(writer, sheet_name=SHEET_NAME, index=False)
            st.success(f"Código {k_del} eliminado.")
            st.rerun()