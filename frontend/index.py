from dash import html
from frontend import tab_bases
from .app import app

app.layout = html.Div([
    html.H1('Google Contact Preparation'),
    html.Div(
        tab_bases.layout,
    ),
])
