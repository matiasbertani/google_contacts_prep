from dash import dcc, html

from app import app
from frontend import tab_bases


app.layout = html.Div([

    html.H1('Bases de Google'),

    html.Div(
        dcc.Tabs(
            dcc.Tab(
                    tab_bases.layout,
                    id='base',
                    label='BASES',
                    value='base',
                ),
            id='pestanias', value='base',
        ),
    ),
    ],
    style={'background-image': 'url(/assets/fondo_10.jpg)'},
)

if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8050, debug=True)
