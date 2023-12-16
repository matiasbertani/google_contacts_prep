
import base64
import io
import time

from dash import dcc, html
from dash import dash_table as dt
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

import pandas as pd
from backend.google_contacts_data_builder import GoogleContactsDataBuilder
from flask import send_file
from frontend.app import app

df_base = None
card_planilla_bases = dbc.Card(
    [
        dbc.CardBody(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Spinner(
                                html.Div(id="subir-planilla-bases"),
                                color="light",
                                size='md',
                                spinnerClassName='my-0'),
                            width=2
                        )
                    ],
                    className="card-title"
                ),

                dbc.Row([

                    dbc.Col(
                        dcc.Upload(
                            dbc.Button(
                                "SUBIR PLANILLA",
                                id='boton-subir-planilla-base',
                                color="primary",
                                className="m-1",
                            ),
                            id='update-planilla-bases',
                            multiple=False
                        ),
                        width=4,
                    ),
                ]),
                dt.DataTable(
                    id='datos-planilla-bases',
                    style_table={
                        'width': '60',
                        'overflowX': 'scroll',
                        'maxHeight': '250px',
                        'overflowY': 'scroll'
                    },
                ),
            ]
        ),
    ],
    color='transparent',
    className='w-100'
    # style={"width": "1rem"},
)

layout = html.Div(

    # input group que te deje  :
    # 1- Subir la planillay verla en un recuadro
    # 2- Elegir en un dropdown la col de nombre, dni
    # 3-  elegir la columna de masivo
    # 4- elegir la columnna o columnas de otros telefono
    [
            card_planilla_bases,
            dbc.InputGroup(
                [
                    dbc.InputGroupText("RAZON SOCIAL"),

                    dcc.Dropdown(
                            id='drop-razonsocial-bases',
                            options=[],
                            style={'width': '200px'},
                            value='Razon Social',
                            placeholder='Ingrese el NOmbre y apellido',
                    ),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText("DNI: "),
                    dcc.Dropdown(
                                id='drop-dni-bases',
                                options=[],
                                value='Mat. Unica',
                                style={'width': '200px'},
                                placeholder='Seleccione un la columna dni',
                    ),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dcc.Dropdown(
                        id='drop-telefono-masivo-bases',
                        value=['Telefono_1'],
                        multi=True,
                        style={'width': '400px'},
                        className='w-100'
                    ),
                    dbc.InputGroupText("TELEFONOS MASIVOS"),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dcc.Dropdown(
                        id='drop-telefono-otros-bases',
                        multi=True,
                        value=[f'Telefono_{i}' for i in range(2, 10)],
                        style={'width': '400px'}
                        ),
                    dbc.InputGroupText("OTROS TELEFONOS"),
                ],
                className="mb-3",
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupText("SEPARAR POR: "),
                    dcc.Dropdown(
                        id='drop-separador-bases',
                        options=[],
                        value='Ejecutivo',
                        placeholder='Separador',
                        style={'width': '200px'}
                    ),
                ],
                className="mb-3",
            ),

            dbc.Button("ARMAR BASES", id='boton-armar-bases', color="danger", className="m-1"),
            dbc.Spinner(html.Div(id="loading-armar-bases")),

            html.A(
                'Download Zip',
                id='download-zip',
                download="Bases Google.zip",
                href="",
                target="_blank",
                n_clicks=0,
                hidden='hidden'
            )

    ]
)


@app.callback(
    [
        Output('datos-planilla-bases', 'columns'),
        Output('datos-planilla-bases', 'data'),
        Output('drop-razonsocial-bases', 'options'),
        Output('drop-dni-bases', 'options'),
        Output('drop-telefono-masivo-bases', 'options'),
        Output('drop-telefono-otros-bases', 'options'),
        Output('drop-separador-bases', 'options'),

    ],

    [Input('update-planilla-bases', 'contents')],
    [
        State('update-planilla-bases', 'filename'),
        State('update-planilla-bases', 'last_modified')
    ])
def Cargar_Planilla_Bases(content, name, date):
    """Carga planilla en variable de manera temporal"""
    global df_base
    if content is not None:
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in name:
                df = pd.read_csv(io.BytesIO(decoded), encoding='latin_1', sep=';', dtype=str)

            elif 'xls' in name:
                # Assume that the user uploaded an excel file
                df = pd.read_excel(io.BytesIO(decoded))
            df_base = df.copy()
        except Exception as e:
            print(e)
        opciones_drop = [{'label': str(i), 'value': str(i)} for i in df_base.columns.dropna().unique()]
        col_tabla = [{'name': i, 'id': i} for i in df.columns]
        data_tabla = df_base.to_dict('records')

        return col_tabla, data_tabla, opciones_drop, opciones_drop, opciones_drop, opciones_drop, opciones_drop

    else:
        raise PreventUpdate


@app.callback(
    [
        Output('loading-armar-bases', 'children'),
        Output('download-zip', 'hidden')
    ],
    [
        Input('boton-armar-bases', 'n_clicks')
    ],

    [
        State('drop-razonsocial-bases', 'value'),
        State('drop-dni-bases', 'value'),
        State('drop-telefono-masivo-bases', 'value'),
        State('drop-telefono-otros-bases', 'value'),
        State('drop-separador-bases', 'value'),
    ])
def Boton_Armar_Planilla(n_clicks, razon_social, dni, tel_masivos, tel_otros, separador):
    """Guarda la planilla en el EJECUTIVO (Navegador) selecionado"""
    global df_base
    if (
        n_clicks and razon_social is not None and dni is not None and tel_masivos is not None and
        tel_otros is not None and separador is not None and df_base is not None
    ):

        time.sleep(1)

        builder = GoogleContactsDataBuilder(
            df_base,
            [dni],
            [razon_social],
            tel_masivos,
            tel_otros,
            [separador]
        )
        builder.build_datasheet()
        return "Variables Cargadas con exito", False

    raise PreventUpdate


@app.callback(
    Output('download-zip', 'href'),
    [Input('download-zip', 'n_clicks')])
def generate_report_url(n_clicks):
    return '/resultados temporales/'


@app.server.route('/resultados temporales/')
def generate_report_url_2():
    return send_file(
        './resultados temporales/Bases Google.zip',
        attachment_filename='Bases Google.zip',
        as_attachment=True,
        cache_timeout=0
    )
