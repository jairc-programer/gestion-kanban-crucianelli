import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

def renderizar_tabla_interactiva_tracker(df: pd.DataFrame, es_editable: bool = False):
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configuración de columnas
    gb.configure_default_column(resizable=True, filter=True, sortable=True)
    gb.configure_column("ID_Solicitud", pinned="left", width=120)
    gb.configure_column("Material", pinned="left", width=130)
    
    if es_editable:
        gb.configure_column("Cargado_SAP", editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': ['SI', 'NO']})
        gb.configure_column("Impreso", editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': ['SI', 'NO']})
        gb.configure_column("Estado_Fisico", editable=True, cellEditor='agSelectCellEditor', cellEditorParams={'values': ['Pendiente', 'En Proceso', 'Entregado']})
        gb.configure_column("Observación", editable=True)

    gb.configure_selection(selection_mode="single" if not es_editable else "disabled", use_checkbox=False)
    grid_options = gb.build()

    grid_response = AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED if es_editable else GridUpdateMode.SELECTION_CHANGED,
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        fit_columns_on_grid_load=False,
        theme="alpine-dark",
        height=400
    )
    
    return grid_response