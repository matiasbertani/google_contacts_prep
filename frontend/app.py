import dash
import dash_bootstrap_components as dbc

external = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.LITERA]
)
app.title = 'Google Contact Preparation'
server = app.server
