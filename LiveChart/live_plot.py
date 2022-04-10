import dash
import os
from dash import dcc, html
from dash.dependencies import Input, Output, State
from DataPreprocessing.DataProvider import DataProvider
from DataPreprocessing.data_columns import COINS, HOURLY_COLS
from Plots.plot_utils import *
from Plots.plotly_fig import get_updated_fig
import dash_bootstrap_components as dbc

data_path = os.path.join(os.getcwd(), 'resources.nosync')

coins = COINS
hourly_cols = HOURLY_COLS
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())

resample_radio_options = {k: f' {k} |' for k in resample_keywords}

price_provider = DataProvider(START_DATA_DATE, os.path.join(data_path, 'data'), coins)
hourly_provider = DataProvider(START_DATA_DATE, os.path.join(data_path, 'data_hourly'), hourly_cols)
providers = dict(price_provider=price_provider, hourly_provider=hourly_provider)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.title = 'Live Crypto Market'
app.layout = html.Div([
    html.Div(children=[
        html.H4('Crypto Live Feed by Shushu', style={'padding-right': '5%', 'margin-left': '2%'}),
        dcc.Dropdown(COINS, COINS[0], id='coin-type', clearable=False, style=dict(width='20%')),
        html.Div(id='live-update-text', style={'width': '20%'}),
        html.Div(children=
                 dcc.RadioItems(options=resample_radio_options, value=resample_keywords[2], id='resample-type',
                                inline=True)),
        html.Div(id='live-update-container', children=[
            dbc.Checklist(options=[{"label": "Live Update", "value": 1}], value=[1], id="live-update-button",
                          switch=True)], style={'padding-left': '3%', 'display': 'flex'}),
    ],
        style={'display': 'flex', 'align-items': 'center'},
    ),
    html.Div([
        dcc.Graph(id='live-update-graph', config={'scrollZoom': True, 'displayModeBar': False}),
        dcc.Interval(id='interval-component', interval=UPDATE_INTERVAL_SECONDS * 1000, n_intervals=0)
    ])
])


@app.callback(
    Output('interval-component', 'disabled'),
    [Input('live-update-button', 'value')],
    [State('interval-component', 'disabled')])
def callback_func_start_stop_interval(button, _):
    return len(button) == 0


@app.callback(Output('live-update-text', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('Interval: {0:.2f}'.format(n), style=style),
    ]


@app.callback(Output('interval-component', 'n_intervals'),
              Input('coin-type', 'value'))
def interval_update(_):
    return 0


@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'))
def update_graph_live(n, coin, resample):
    print(n, resample, coin)
    filter_datetime = get_graph_start_datetime(resample)
    fig = get_updated_fig(providers, filter_datetime, resample, coin)
    return fig


if __name__ == '__main__':
    # https://dash.plotly.com/live-updates
    app.run_server(debug=True)
