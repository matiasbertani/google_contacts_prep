from dash import html
from frontend import tab_bases
from .app import app

app.layout = html.Div([
    html.H1('Google Contact Preparation', className='text-center'),
    html.Div(
        tab_bases.layout,
    ),
])
server = app.server
