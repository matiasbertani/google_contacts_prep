import base64
import io

from dash import dash_table as dt
from dash import (
    Input,
    Output,
    State,
    dcc,
    html,
)
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd

from backend.google_contacts_data_builder import GoogleContactsDataBuilder
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
                                "Cargar csv",
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
    className='w-100',
)


download_button = html.Div([
    dbc.Button(
        "Descargar",
        id="download-google-bases-button",
        className="ms-auto",
        color='success',
        n_clicks=0,
    ),
    dcc.Download(id="download-google-bases")
])


download_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Area de descarga"), close_button=True),
                dbc.ModalBody([
                    '',
                    html.Br(),
                    download_button,
                ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Cerrar",
                        id="close-backdrop",
                        className="ms-auto",
                        n_clicks=0,
                    )
                ),
            ],
            id="modal-download",
            is_open=False,
            backdrop='static',
        ),
    ]
)

layout = html.Div(

    [
            download_modal,
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

            dbc.Button("Preparar Bases", id='boton-armar-bases', color="danger", className="m-1"),

    ]
)


@app.callback(
    Output('datos-planilla-bases', 'columns'),
    Output('datos-planilla-bases', 'data'),
    Output('drop-razonsocial-bases', 'options'),
    Output('drop-dni-bases', 'options'),
    Output('drop-telefono-masivo-bases', 'options'),
    Output('drop-telefono-otros-bases', 'options'),
    Output('drop-separador-bases', 'options'),

    Input('update-planilla-bases', 'contents'),

    State('update-planilla-bases', 'filename'),
)
def upload_datasheet_for_preparation(content, name):
    global df_base

    if content is None:
        raise PreventUpdate

    _, content_string = content.split(',')
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


@app.callback(
    Output("modal-download", "is_open"),
    Input("boton-armar-bases", "n_clicks"),
    Input("close-backdrop", "n_clicks"),
    State("modal-download", "is_open"),
)
def toggle_modal(click_build: int, click_close: int, is_open: bool):
    if click_build or click_close:
        return not is_open
    return is_open


@app.callback(
    Output("download-google-bases", "data"),

    Input('download-google-bases-button', 'n_clicks'),

    State('drop-razonsocial-bases', 'value'),
    State('drop-dni-bases', 'value'),
    State('drop-telefono-masivo-bases', 'value'),
    State('drop-telefono-otros-bases', 'value'),
    State('drop-separador-bases', 'value'),
)
def build_and_download_datasheet_for_google_contacts(
    click_build_and_download,
    razon_social,
    dni,
    tel_masivos,
    tel_otros,
    separador,
):
    global df_base
    if (
        click_build_and_download and razon_social is not None and dni is not None and tel_masivos is not None and
        tel_otros is not None and separador is not None and df_base is not None
    ):

        builder = GoogleContactsDataBuilder(
            df_base,
            [dni],
            [razon_social],
            tel_masivos,
            tel_otros,
            [separador],
        )
        builder.build_datasheet()
        zip_file = builder.get_results_as_zip_file()
        return dcc.send_bytes(zip_file, "bases google.zip")

    raise PreventUpdate
