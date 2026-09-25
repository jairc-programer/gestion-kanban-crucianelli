# ==========================================
# FUNCIÓN PARA REINICIAR HISTORIALES (MODO PRODUCCIÓN)
# ==========================================
def limpiar_historiales_de_prueba():
    # Reiniciar Historial de Cambios
    df_empty_log = pd.DataFrame(columns=LOG_COLUMNS)
    df_empty_log.to_csv(LOG_FILE, index=False)
    
    # Reiniciar Tracker Logístico
    df_empty_tracker = pd.DataFrame(columns=TRACKER_COLUMNS)
    df_empty_tracker.to_csv(TRACKER_FILE, index=False)

# --- Dentro de la pestaña '📜 Historial Auditoría' ---
tab_historial = obtener_tab("📜 Historial Auditoría")
if tab_historial:
    with tab_historial:
        st.subheader("📜 Historial Completo de Modificaciones")
        st.dataframe(cargar_logs().sort_values(by="Fecha_Hora", ascending=False), use_container_width=True)
        
        # Módulo de purga solo para roles con permiso (Procesos)
        if rol_actual == "Procesos":
            st.markdown("---")
            with st.expander("⚠️ Zona de Mantenimiento / Puesta a Cero (Producción)"):
                st.warning("Esta acción eliminará todos los registros de prueba de Auditoría y Tracker Logístico para el arranque oficial.")
                if st.button("🔴 Borrar Historiales de Prueba", type="primary"):
                    limpiar_historiales_de_prueba()
                    st.success("✅ Historiales y Tracker limpiados correctamente. ¡El sistema está listo para el lunes!")
                    st.rerun()
