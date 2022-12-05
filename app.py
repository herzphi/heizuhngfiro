#!/usr/bin/python3.7
print("Content-Type: text/html")


from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

from iotcloudtemp.connect import get_temp_by_hour

app = Dash('Test')


app.layout = html.Div(children=[
    html.H1(children='Philipps HeidelBude'),
    html.Div(id='current_temperature'),
    dcc.RadioItems(options=[
            {'label': 'Live Updates', 'value': 'False'},
            {'label': 'Stop Live Updates', 'value': 'True'},
        ],
        value='False',
        id='radio-live-offline'
   ),
    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
            id='interval-component',
            interval=10*1000, # in milliseconds
            n_intervals=0,
            disabled=False
        )
]) 


@app.callback(Output('interval-component', 'disabled'),
              Input('radio-live-offline', 'value')
)
def update_interval(value):
    if value=='False':
        value = False
    else:
        value = True
    return value


@app.callback([Output('live-update-graph', 'figure'),
Output('current_temperature', 'children')],
              Input('interval-component', 'n_intervals'))
def update_graph_live(n):
    df_data = get_temp_by_hour()
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
    return fig, f'T = {latest_data:.2f} °C at {time} ({date})'


if __name__ == '__main__':
    app.run_server(debug=True)
