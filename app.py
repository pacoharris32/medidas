import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output, dash_table
from dash.dash_table.Format import Group 

# Variable global para el total de acuíferos (se inicializa a 0 y se actualiza después de la carga)
TOTAL_AQUIFERS = 0

# ----------------------------------------------------
# 1. CARGA Y PREPARACIÓN DE DATOS (MELT Y FILTRADO)
# ----------------------------------------------------

# !!! ATENCIÓN: Reemplaza 'data25.xlsx' con el nombre/ruta real de tu archivo.
ARCHIVO_DATOS = 'data25.xlsx'

# Definimos nombres internos seguros para las columnas transformadas
COL_STATE_NAME = 'NOM_EDO'
COL_AQUIFER_NAME = 'NOM_ACUIF'
COL_YEAR = 'AÑO' # Nuevo nombre de columna después del melt
COL_LEVEL = 'NIVEL_FREATICO' # Nuevo nombre de columna para el valor de la medición (PNE)
COL_MEASURE = 'CONTEO_MEDICIONES' # Columna auxiliar para el conteo de la tabla

try:
    df_raw = pd.read_excel(ARCHIVO_DATOS)
    
    # 1. Identificar columnas fijas (NOM_EDO, NOM_ACUIF) y columnas de valor (PNE_XXXX)
    id_vars = [COL_STATE_NAME, COL_AQUIFER_NAME] 
    value_vars = [col for col in df_raw.columns if col.startswith('PNE_')]
    
    # 2. Realizar la operación MELT (Unpivot) para transformar el formato ancho a largo
    df_datos = pd.melt(
        df_raw,
        id_vars=id_vars,
        value_vars=value_vars,
        var_name=COL_YEAR, 
        value_name=COL_LEVEL
    )

    # 3. ⭐️ CORRECCIÓN DE LIMPIEZA DE DATOS ⭐️
    # Eliminar filas donde el nivel freático, el estado o el acuífero sean nulos (NaN)
    df_datos = df_datos.dropna(subset=[COL_LEVEL, COL_STATE_NAME, COL_AQUIFER_NAME])

    # 4. ⭐️ CONVERSIÓN A STRING ⭐️
    # Aseguramos que los nombres de estado y acuífero sean siempre strings para el Dropdown
    df_datos[COL_STATE_NAME] = df_datos[COL_STATE_NAME].astype(str)
    df_datos[COL_AQUIFER_NAME] = df_datos[COL_AQUIFER_NAME].astype(str)

    # 5. Limpiar la columna de AÑO: Convertir 'PNE_2020' a '2020'
    df_datos[COL_YEAR] = df_datos[COL_YEAR].str.replace('PNE_', '')
    df_datos[COL_YEAR] = df_datos[COL_YEAR].astype(str)
    
    # 6. Crear la columna de conteo de mediciones
    df_datos[COL_MEASURE] = 1 
    
    # ⭐️ ACTUALIZACIÓN: Calcular el número total de acuíferos en todo el archivo
    TOTAL_AQUIFERS = df_datos[COL_AQUIFER_NAME].nunique()
    
except FileNotFoundError:
    print(f"Error: Asegúrate de que '{ARCHIVO_DATOS}' esté en la misma carpeta o usa la ruta correcta.")
    # DataFrame de ejemplo (adaptado al formato LONG/MELT) para asegurar que la app corra
    data = {
        COL_YEAR: ['2020', '2020', '2021', '2021', '2020', '2021'],
        COL_STATE_NAME: ['Aguascalientes', 'Aguascalientes', 'Baja California', 'Baja California', 'Aguascalientes', 'Baja California'],
        COL_AQUIFER_NAME: ['EL LLANO', 'VALLE DE AGUASCALIENTES', 'VALLE DE MEXICALI', 'LLANOS DEL BERRENDO', 'EL LLANO', 'VALLE DE MEXICALI'],
        COL_LEVEL: [10.5, 20.1, 30.2, 40.0, 5.7, 25.9],
        COL_MEASURE: [1, 1, 1, 1, 1, 1] 
    }
    df_datos = pd.DataFrame(data)
    # Si falla la carga, calcular el total basado en los datos de ejemplo
    TOTAL_AQUIFERS = df_datos[COL_AQUIFERS].nunique()
# ----------------------------------------------------
# 2. INICIALIZACIÓN DE LA APLICACIÓN DASH
# ----------------------------------------------------

app = Dash(__name__)

# Opciones iniciales para el filtro de Año (ordenadas descendentemente)
opciones_anio_raw = [{'label': i, 'value': i} for i in df_datos[COL_YEAR].unique()]
opciones_anio = sorted(opciones_anio_raw, key=lambda x: x['value'], reverse=True)

# ----------------------------------------------------
# 3. DISEÑO DEL LAYOUT DE LA APLICACIÓN
# ----------------------------------------------------

app.layout = html.Div(style={'padding': '20px'}, children=[
    
    # CONTENEDOR DE MÉTRICAS GLOBALES/FILTRADAS
    html.Div(style={'textAlign': 'center', 'marginBottom': '20px'}, children=[
        
        # Métrica 1: Contador de Acuíferos (Inicia mostrando el Total Global)
        html.Div(
            id='contador-acuiferos',
            style={
                'fontSize': '24px',
                'fontWeight': 'bold',
                'color': '#007bff'
            },
            children=f'Número Total de Acuíferos en el Archivo: {TOTAL_AQUIFERS}' 
        ),
        
        # ⭐️ NUEVA MÉTRICA 2: Contador de Mediciones
        html.Div(
            id='contador-mediciones',
            style={
                'fontSize': '18px',
                'fontWeight': 'normal',
                'color': '#555'
            },
            # Inicialmente vacío, se llenará con el primer callback de actualización
            children='' 
        ),
    ]),
    
    # CONTENEDOR DE FILTROS
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '30px'}, children=[
        
        # Filtro de Año
        html.Div(style={'flex': 1}, children=[
            html.Label('Selecciona el Año:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='filtro-anio',
                options=opciones_anio,
                value=opciones_anio[0]['value'] if opciones_anio else None, # Valor por defecto: el año más reciente
                placeholder="Selecciona un Año",
                clearable=False
            )
        ]),
        
        # Filtro de Estado
        html.Div(style={'flex': 1}, children=[
            html.Label('Selecciona el Estado:', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='filtro-estado',
                placeholder="Selecciona un Estado",
                clearable=False
            )
        ]),
        
        # Filtro de Acuífero
        html.Div(style={'flex': 1}, children=[
            html.Label('Selecciona el Acuífero (Opcional):', style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='filtro-acuifero',
                placeholder="Selecciona un Acuífero",
                clearable=True
            )
        ]),
    ]),
    
    html.Hr(),
    
    # TABLA CENTRAL DE RESULTADOS
    html.Div(
        id='tabla-resultados',
        children=dash_table.DataTable(
            id='tabla-principal',
            # IDs de columna simplificados y finales
            columns=[
                {"name": "Estado", "id": "Estado"},
                {"name": "ACUÍFERO", "id": "ACUÍFERO"},
                {"name": "Pozos Medidos", "id": "Pozos Medidos"}, 
            ],
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
        )
    )
])

# ----------------------------------------------------
# 4. FUNCIONES DE CALLBACK
# ----------------------------------------------------

# CALLBACK 1: Actualiza las opciones del Filtro de Estado basado en el Año seleccionado
@app.callback(
    Output('filtro-estado', 'options'),
    Output('filtro-estado', 'value'),
    Input('filtro-anio', 'value')
)
def set_estados_options(selected_anio):
    if selected_anio is None:
        return [], None
    
    df_filtrado_por_anio = df_datos[df_datos[COL_YEAR] == selected_anio]
    
    # Obtenemos las opciones únicas 
    opciones = [{'label': i, 'value': i} for i in df_filtrado_por_anio[COL_STATE_NAME].unique()]
    
    # Añadir la opción 'TODOS' para el Estado y la seleccionamos por defecto
    opciones.insert(0, {'label': 'TODOS', 'value': 'TODOS_SELECTION'})
    
    valor_inicial = 'TODOS_SELECTION'
    
    return opciones, valor_inicial

# CALLBACK 2: Actualiza las opciones del Filtro de Acuífero
@app.callback(
    Output('filtro-acuifero', 'options'),
    Output('filtro-acuifero', 'value'),
    Input('filtro-anio', 'value'),
    Input('filtro-estado', 'value')
)
def set_acuiferos_options(selected_anio, selected_estado):
    if selected_anio is None or selected_estado is None:
        if selected_estado != 'TODOS_SELECTION':
            return [], None

    # Filtrar el DF por Año
    df_filtrado = df_datos[df_datos[COL_YEAR] == selected_anio].copy()
    
    # Aplicar filtro de Estado solo si no es 'TODOS_SELECTION'
    if selected_estado != 'TODOS_SELECTION':
        df_filtrado = df_filtrado[df_filtrado[COL_STATE_NAME] == selected_estado]
    
    # Obtenemos las opciones únicas de Acuífero
    opciones = [{'label': i, 'value': i} for i in df_filtrado[COL_AQUIFER_NAME].unique()]
    
    # Usamos el string seguro para 'TODOS'
    opciones.insert(0, {'label': 'TODOS', 'value': 'TODOS_SELECTION'})
    
    # Dejamos la selección de Acuífero en 'TODOS' por defecto
    return opciones, 'TODOS_SELECTION' 

# CALLBACK 3: Actualiza las dos Métricas (Acuíferos y Mediciones) y la Tabla de Resultados
@app.callback(
    Output('contador-acuiferos', 'children'),
    Output('contador-mediciones', 'children'), # ⭐️ Nuevo Output para Mediciones
    Output('tabla-principal', 'data'),
    Input('filtro-anio', 'value'),
    Input('filtro-estado', 'value'),
    Input('filtro-acuifero', 'value')
)
def update_table_and_metric(anio_sel, estado_sel, acuifero_sel):
    
    if anio_sel is None:
        # Si no hay año seleccionado, se retorna el total global y se reinicia la tabla
        return f'Número Total de Acuíferos en el Archivo: {TOTAL_AQUIFERS}', '', []

    # 1. Aplicar filtro de Año (siempre obligatorio)
    df_final = df_datos[df_datos[COL_YEAR] == anio_sel].copy()
    
    # 2. Aplicar filtro de Estado
    if estado_sel != 'TODOS_SELECTION':
        df_final = df_final[df_final[COL_STATE_NAME] == estado_sel]
    
    # 3. Aplicar filtro de Acuífero
    if acuifero_sel != 'TODOS_SELECTION':
        df_final = df_final[df_final[COL_AQUIFER_NAME] == acuifero_sel]

    # ----------------------------------------------------
    # Generación de la Métrica: Contador de Acuíferos Únicos FILTRADOS
    # ----------------------------------------------------
    numero_acuiferos_medidos = df_final[COL_AQUIFER_NAME].nunique()
    total_mediciones = df_final[COL_MEASURE].sum() # ⭐️ Suma de todas las mediciones

    estado_display = estado_sel if estado_sel != 'TODOS_SELECTION' else 'TODOS'
    acuifero_display = acuifero_sel if acuifero_sel != 'TODOS_SELECTION' else 'TODOS'

    # Formato con comas
    acuiferos_formateado = f"{numero_acuiferos_medidos:,}"
    mediciones_formateado = f"{total_mediciones:,}"

    texto_metrica_acuiferos = (
        f"Acuíferos Filtrados (Año={anio_sel}, Estado={estado_display}, Acuífero={acuifero_display}): "
        f"{acuiferos_formateado}"
    )

    # ⭐️ NUEVO TEXTO DE MÉTRICA
    texto_metrica_mediciones = f"Total de Mediciones Mostradas: {mediciones_formateado}"

    # ----------------------------------------------------
    # Generación de la Tabla: Agrupar para sumar CONTEO_MEDICIONES
    # ----------------------------------------------------
    
    if df_final.empty:
        return texto_metrica_acuiferos, texto_metrica_mediciones, []
        
    df_tabla = df_final.groupby([COL_STATE_NAME, COL_AQUIFER_NAME]).agg(
        Pozos_Medidos=(COL_MEASURE, 'sum')
    ).reset_index()
    
    # Renombrar para que coincidan con los IDs de la tabla en el layout
    df_tabla.rename(columns={
        COL_STATE_NAME: "Estado", 
        COL_AQUIFER_NAME: "ACUÍFERO",
        'Pozos_Medidos': "Pozos Medidos" 
    }, inplace=True)
    
    datos_tabla = df_tabla.to_dict('records')
    
    # Retorna ambas métricas y los datos de la tabla
    return texto_metrica_acuiferos, texto_metrica_mediciones, datos_tabla

# ----------------------------------------------------
# 5. EJECUTAR LA APLICACIÓN
# ----------------------------------------------------

if __name__ == '__main__':
    # Usar use_reloader=False para evitar trazas de error confusas durante la depuración
    app.run_server(debug=True, use_reloader=False) 
