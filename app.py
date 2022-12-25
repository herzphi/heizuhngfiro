from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go

from iotcloudtemp.connect import get_temp_by_hour, get_thing_id, checkboxes_table, revive_connection

client_things, client_properties = revive_connection()
thing_id, properties_unflat = get_thing_id(client_things, client_properties)
properties = [item for sublist in properties_unflat for item in sublist]
df_propids, dict_propid_list = checkboxes_table(properties)


mathjax = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "18rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
    "font-size": "9pt",
}
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

sidebar = html.Div(
    [
        html.H2("Settings", className="display-4"),
        html.Hr(),
        html.P(
            "Do it. Just do it.", className="lead"
        ),
        html.Div(id='current_temperature'),
        dbc.Card(
            [
                daq.ToggleSwitch(
                    value=False,
                    id='toggle-live-offline',
                    label='Live Updates'
                ),
                daq.ToggleSwitch(value=False, id='toggle-mean-date', label='Comparison On/Off'),
                dcc.Checklist(
                    options=dict_propid_list, 
                    value=[dict_propid_list[0]['value']], 
                    id='sensor-checklist',
                    style={"width":"80%","display": "block"},
                    labelStyle={"line-height":"2.1", "padding-left":"5px"},
                    inputStyle={"margin-right":"5px"}
                )
            ],
        ),
    ],
    style=SIDEBAR_STYLE)

content = html.Div(children=[
            html.H1(children='Heizung FiRo'),
            dcc.Graph(
                id='live-update-graph',
            ),
            dcc.Graph(
                id='live-update-graph-stats',
            ),
            dcc.Interval(
                    id='interval-component',
                    interval=10*1000, # in milliseconds
                    n_intervals=0,
                    disabled=True
                )
        ], style=CONTENT_STYLE) 

app.layout = html.Div([sidebar, content])



@app.callback(
    Output('interval-component', 'disabled'),
    Input('toggle-live-offline', 'value')
)
def update_output(value):
    if value:
        value = False
    else:
        value = True
    return value


@app.callback([
    Output('live-update-graph', 'figure'),
    Output('live-update-graph-stats', 'figure'),
    Output('current_temperature', 'children'),
    ],
    [
    Input('interval-component', 'n_intervals'),
    Input('sensor-checklist', 'value'),
    Input('toggle-mean-date', 'value'),
    ]
)
def update_graph_live(n, sensor, datecheck):
    df_data, df_avg = get_temp_by_hour(sensor, client_properties, thing_id, df_propids)
    latest_data, time = df_data.tail(1).value.values[0], \
            df_data.tail(1).time.values[0]
    purpose = df_propids['purpose'].values[0]
    if str(datecheck) == 'True':
        fig = px.line(df_data,
                        x="hour",
                        y="value", 
                        color='date',
                        template='simple_white',
                        title='purpose',
                        labels={
                            "hour": "Hour of the Day",
                            "value": "Temperature in °C",
                            "date": "Date (YYYY-MM-DD)"
                        },
        )
    elif str(datecheck) == 'False':
        fig = px.scatter(
            df_avg, 
            x='hour', 
            y='mean',
            error_y='std',
            color='purpose',
            template='simple_white',
        )
        fig.update_layout(
            xaxis_title_text='Hour of the Day',
            yaxis_title_text='Mean Temperature in °C'
        )
        fig_stats = px.histogram(
            df_data,
            x="value",
            template='simple_white',
        )
        fig_stats.update_layout(
            xaxis_title_text='Temperature in °C'
        )
    return fig, fig_stats, f'T_current = {latest_data:.2f} °C at {time} ({purpose})'


if __name__ == '__main__':
    app.run_server(debug=True)
