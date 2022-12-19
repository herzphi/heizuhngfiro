from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import dash_daq as daq
import plotly.express as px

from iotcloudtemp.connect import get_temp_by_hour, get_connection

properties, thing_id, client_properties = get_connection()

name_props, id_props = ([] for i in range(2))
for i in range(len(properties)):
    name_props.append(properties[i].name)
    id_props.append(properties[i].id)

mathjax = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.4/MathJax.js?config=TeX-MML-AM_CHTML'
app = Dash(__name__)

server = app.server

app.layout = html.Div(children=[
    html.H1(children='Heizung FiRo'),
    #html.Div(id='toggle-info'),
    daq.ToggleSwitch(
        value=False,
        id='toggle-live-offline',
        label='Live Updates'
    ),
    dcc.Dropdown(name_props, id='sensor-dropdown'),
    html.Table(className='table_info',
    children=[
        html.Tr(
        [
            html.Td(
                dcc.Markdown('''$T_{current} =$''', mathjax=True)
            ),
            html.Td(
                html.Div(id='current_temperature')
            ),
        ]),
        html.Tr([
            html.Td(
                dcc.Markdown('''$T_{mean} =$''', mathjax=True)
            ),
            html.Td(
                html.Div(id='mean_temperature')
            )
        ]),
        html.Tr([
            html.Td(
                dcc.Markdown('''$T_{max} =$''', mathjax=True)
            ),
            html.Td(
                html.Div(id='max_temperature')
            ),
        ]),
        html.Tr([
            html.Td(
                dcc.Markdown('''$T_{min} =$''', mathjax=True)
            ),
            html.Td(
                html.Div(id='min_temperature')
            ),
        ])
    ]),
    html.Table([
        html.Tr([
            html.Td(
                dcc.Graph(id='live-update-graph'),
                style={'width':'80%'}
            )
        ]),
    ]),
    dcc.Interval(
            id='interval-component',
            interval=10*1000, # in milliseconds
            n_intervals=0,
            disabled=True
        )
]) 





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
    Output('current_temperature', 'children'),
    Output('mean_temperature', 'children'),
    Output('max_temperature', 'children'),
    Output('min_temperature', 'children'),
    ],
    [
    Input('interval-component', 'n_intervals'),
    Input('sensor-dropdown', 'value')
    ]
)
def update_graph_live(n):
    df_data = get_temp_by_hour(properties, client_properties, thing_id)
    latest_data, time, date = df_data.tail(1).value.values[0], \
        df_data.tail(1).time.values[0], df_data.tail(1).date.values[0]
    fig = px.line(df_data,
                    x="hour", 
                    y="value", 
                    color='date',
                    template='simple_white',
                    labels={
                        "hour": "Hour of the Day",
                        "value": "Temperature in °C",
                        "date": "Date (YYYY-MM-DD)"
                    },
    )
    #fig.update_layout(showlegend=False)
    values_series = df_data['value']
    mean_T, std_T = values_series.mean(), values_series.std()
    max_T = values_series.max()
    min_T = values_series.min()
    min_t_time = df_data[df_data['value']==min_T]['hour'].values[0]
    if min_t_time<13:
        ampm = 'am'
    else:
        min_t_time = 'pm'

    return fig, f'{latest_data:.2f} °C at {time}', \
        f'({mean_T:.1f} ± {std_T:.1f}) °C', f'{max_T:.1f} °C', \
            f'{min_T:.1f} °C at {min_t_time:.0f} {ampm}'


if __name__ == '__main__':
    app.run_server(debug=True)
