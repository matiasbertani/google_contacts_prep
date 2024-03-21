import os
import dash
import dash_bootstrap_components as dbc

# Could see any file (even nested in subdirectory) within this path
assets_path = os.getcwd() + '/frontend/assets'

external = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA],
    assets_folder=assets_path,
)
app.title = 'Google Contact Preparation'
