import dash
import os
from dash import dcc, html
from dash.dependencies import Input, Output
from cryptoUtils.DataProvider import DataProvider
from cryptoUtils.data_columns import COINS, HOURLY_COLS
from LiveChart.LivePlotSeperate.plotly_fig_seperated import get_updated_fig
from LiveChart.plot_utils import *

data_path = os.path.join(os.getcwd(), 'resources')

coins = COINS
hourly_cols = HOURLY_COLS
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())

price_provider = DataProvider(start_date=START_DATA_DATE, path=os.path.join(data_path, 'data'), cols=coins)
hourly_provider = DataProvider(start_date=START_DATA_DATE, path=os.path.join(data_path, 'data_hourly'),
                               cols=hourly_cols)
providers = dict(price_provider=price_provider,
                 hourly_provider=hourly_provider)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div(style=dict(backgroundColor='LightSteelBlue'), children=
html.Div([
    html.H4('Crypto Live Feed'),
    # html.Div(id='live-update-text'),
    html.Div([
        dcc.Dropdown(COINS, COINS[0], id='coin-type', clearable=False, style=dict(width='40%')),
        dcc.Dropdown(resample_keywords, resample_keywords[-3], id='resample-type', clearable=False,
                     style=dict(width='40%'))],
        style=dict(width='50%', display='flex')),  # {'width': '30vh'}

    dcc.Graph(id='live-update-graph'),
    dcc.Interval(
        id='interval-component',
        interval=UPDATE_INTERVAL_SECONDS * 1000,  # in milliseconds
        n_intervals=0
    )
])
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
              # Input('interval-component', 'n_intervals'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'))
def update_graph_live(coin, resample):
    print(resample, coin)
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
