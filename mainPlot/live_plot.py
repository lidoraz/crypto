import dash
import os
from dash import dcc, html
import dash_daq as daq
from dash.dependencies import Input, Output, State
from cryptoUtils.DataProvider import DataProvider
from cryptoUtils.data_columns import COINS, HOURLY_COLS
from mainPlot.plotly_fig import get_updated_fig
from plot_utils import *

data_path = os.path.join(os.getcwd(), 'resources.nosync')

coins = COINS
hourly_cols = HOURLY_COLS
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())

resample_radio_options = {k: f' {k} |' for k in resample_keywords}

price_provider = DataProvider(start_date=START_DATA_DATE, path=os.path.join(data_path, 'data'), cols=coins)
hourly_provider = DataProvider(start_date=START_DATA_DATE, path=os.path.join(data_path, 'data_hourly'),
                               cols=hourly_cols)
providers = dict(price_provider=price_provider,
                 hourly_provider=hourly_provider)

external_stylesheets = [
    'https://bootswatch.com/5/darkly/bootstrap.css', ]  # 'https://codepen.io/chriddyp/pen/bWLwgP.css'
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
app.layout = html.Div(children=
html.Div([
    html.Div([
        html.H4('Crypto Live Feed by Shushu', style={'padding-right': '5%', 'margin-left': '2%'}),
        # html.H5('Crypto:', style={'float': 'right', 'clear': 'right'}),
        # html.Span('Crypto Live Feed by Shushu', style={'padding-right': '20%', 'margin-left': '2%', 'text-size': '24pt'}),
        dcc.Dropdown(COINS, COINS[0], id='coin-type', clearable=False, style=dict(width='20%')),
        html.Div(id='live-update-text', style={'width': '20%'}),
        html.Div(children=
                 dcc.RadioItems(options=resample_radio_options, value=resample_keywords[2], id='resample-type',
                                inline=True)),
        html.Div(id='live-update-container', children=[
            html.Span('Live Update  '),
            daq.BooleanSwitch(id='live-update-button', on=True, className='dark-theme-control'),
        ], style={'padding-left': '3%', 'display': 'flex'}),
    ],
        style={'display': 'flex', 'align-items': 'center'},
    ),
    html.Div([
        dcc.Graph(id='live-update-graph', config={'scrollZoom': True, 'displayModeBar': False}),
        dcc.Interval(
            id='interval-component',
            interval=UPDATE_INTERVAL_SECONDS * 1000,  # in milliseconds
            n_intervals=0
        )
    ])
]),
    # style=dict(backgroundColor='LightSteelBlue'),
)


# @app.callback(Output('live-update-text', 'children'),
#               Input('interval-component', 'n_intervals'))
# def update_metrics(n):
#     lon, lat, alt = satellite.get_lonlatalt(datetime.datetime.now())
#     style = {'padding': '5px', 'fontSize': '16px'}
#     return [
#         html.Span('Longitude: {0:.2f}'.format(lon), style=style),
#         html.Span('Latitude: {0:.2f}'.format(lat), style=style),
#         html.Span('Altitude: {0:0.2f}'.format(alt), style=style)
#     ]

@app.callback(
    Output('interval-component', 'disabled'),
    [Input('live-update-button', 'on')],
    [State('interval-component', 'disabled')],
)
def callback_func_start_stop_interval(on, _):
    return on


@app.callback(Output('live-update-text', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    style = {'padding': '5px', 'fontSize': '16px'}
    return [
        html.Span('Interval: {0:.2f}'.format(n), style=style),
    ]


@app.callback(Output('interval-component', 'n_intervals'),
              Input('resample-type', 'value'),
              Input('coin-type', 'value'))
def interval_update(resample, coin):  # add other args for additional inputs
    return 0


# @app.callback(Output('live-update-graph', 'figure'),
#               Input('resample-type', 'value'),
# def interval_update(resample, coin):  # add other args for additional inputs

#               Input('coin-type', 'value'))
# Multiple components can update everytime interval gets fired.
# curr_keys = {'resample': '1H', 'coin': 'BTC', 'fig': {}}
# fig_ctx = [{}]

@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'))
def update_graph_live(n, coin, resample):
    print(n, resample, coin)
    # ctx = dash.callback_context
    # for trigger in ctx.triggered:
    #     if trigger['prop_id'] != 'interval-component.n_intervals':
    #         return {}
    # TODO hot fix for traces left in the dash output
    #  https://stackoverflow.com/questions/68691855/plotly-dash-how-to-clear-current-graph-plot-before-updating-from-dropdown-value
    # if curr_keys['resample'] != resample or curr_keys['coin'] != coin:
    #     curr_keys['resample'] = resample
    #     curr_keys['coin'] = coin
    #     return {}
    # print(n, resample, coin)
    # if n % 2 == 0:
    #     return {}
    # satellite = Orbital('TERRA')
    # resample_keywords = ['5Min', '15Min', '1H', '4H', '1D']

    filter_datetime = get_graph_start_datetime(resample)
    fig = get_updated_fig(providers, filter_datetime, resample, coin)

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
