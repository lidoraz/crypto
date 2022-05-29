import os
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(root)
print(root)

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import sys

from Dashboard.Plots.plot_utils import INTERVAL_CANDLE_LOOKBACK_TABLE
from Data.Crypto.ccxt_utils import get_candles_from_db
from Data.Crypto.symbols import exchange_symbol_pairs, DB_PATH
from Dashboard.Plots.plotly_fig import get_updated_fig
from Dashboard.Plots.plot_utils import *
from Utils import Persistence

coins = sorted([c[1].split('/')[0] for c in exchange_symbol_pairs])
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())
resample_keywords_text = [f" {k} | " for k in resample_keywords[:-1]] + [f" {resample_keywords[-1]}"]
resample_radio_options = dict(
    zip(resample_keywords, resample_keywords_text))  # {k: f' {k} |' for k in resample_keywords}

db_path = DB_PATH
db = Persistence(db_path, check_same_thread=False)

live_update = False
print(f'live_update = {live_update}')
title = 'Crypto Live Feed'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server  # needed for deployment
app.title = title

title_html = html.H4(title, style={'padding-right': '5%', 'margin-left': '2%'})
coin_html = dcc.Dropdown(coins, 'BTC', id='coin-type', clearable=False, style=dict(width='60pt'))
live_update_html = html.Div(id='live-update-text', style={'margin': 'auto'}, children="")  # 'width': '20%',
resample_selector_html = dcc.RadioItems(options=resample_radio_options, value=resample_keywords[2], id='resample-type',
                                        inline=True)
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/input/ # RadioItems and Checklist
live_update_switch_html = dbc.Switch(id="live-update-button", label="Live Update", value=live_update)

right_portion_html = html.Div(id='right-portion',
                              children=[html.Div(resample_selector_html),
                                        dcc.Slider(0.00, 0.5, step=0.01, marks={'0': 'ts-line(current)', '0.5': 'half'},
                                                   id='ts-slider', value=0.00),
                                        dcc.Slider(10, 200, step=10,
                                                   marks={'10': 'lookback(10)', '100': '100', '200': 'lookback(200)'},
                                                   id='ts-slider-lookahead', value=100)],
                              style={'width': '30%'}
                              )
app.layout = html.Div([
    html.Div(children=[
        title_html,
        html.Div([coin_html,
                  dcc.Input(
                      id="input_lookahead",
                      type="number",
                      value=14,
                      placeholder="lookahead",
                      style=dict(width='30pt')),
                  dcc.Input(id='start-date', placeholder='start_date', value="", debounce=True)],
                 style={'display': 'flex'}
                 ),

        live_update_html,
        right_portion_html],
        style={'display': 'flex', 'align-items': 'center'},
    ),
    html.Div(id='graph-container', children=[
        dcc.Graph(id='live-update-graph', config={'scrollZoom': True,
                                                  'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'pan2d',
                                                                             'zoom2d', 'autoScale2d'],
                                                  'displaylogo': False},
                  style={'width': 'auto', 'height': '85vh'}
                  # TODO important https://stackoverflow.com/questions/46287189/how-can-i-change-the-size-of-my-dash-graph
                  ),
        # https://stackoverflow.com/questions/68188107/how-to-add-create-a-custom-loader-with-dash-plotly
        dcc.Loading(
            id="loading-2",
            children=[html.Div([html.Div(id="loading-output-2")])],
            type="circle",
            loading_state={}
        ),
    ], style=dict(display="None")
             )  # style=dict(height='100vh')
])


# show graph only when ready to display, to avoid blank white figure
@app.callback(Output('graph-container', 'style'),
              Input('live-update-graph', 'figure'))
def show_graph_when_loaded(figure):
    # print("show_graph_when_loaded", figure)
    if figure is None:
        return {'display': 'None'}
    else:
        return None


def _adjust_input_lookahead(input_lookahead):
    if input_lookahead is None:
        input_lookahead = 14
    return max(min(input_lookahead, 100), 3)


@app.callback(Output('live-update-graph', 'figure'),
              Output('live-update-text', 'children'),
              Input('start-date', 'value'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'),
              Input('ts-slider-lookahead', 'value'),
              Input('ts-slider', 'value'))
def update_graph_live(start_date, coin, resample, lookback_length, ts_pct):
    t0 = datetime.now()
    end_date = None
    print(start_date, coin, resample, lookback_length)
    if len(start_date):
        start_ts = int(pd.to_datetime(start_date).timestamp())
        end_date = pd.to_datetime(start_date) + INTERVAL_CANDLE_LOOKBACK_TABLE[resample]
    else:
        start_ts = int((datetime.utcnow() - INTERVAL_CANDLE_LOOKBACK_TABLE[resample]).timestamp())
    df_ohlcv = get_candles_from_db(db, coin, resample, start_ts=start_ts)
    if end_date:
        df_ohlcv = df_ohlcv[df_ohlcv.index <= pd.to_datetime(end_date, utc=True).tz_convert('Israel')]
    # latest_ts = pd.to_datetime(df_ohlcv.attrs['curr_ts_db'], unit='s', utc=True).tz_convert('Israel')
    # line_lookahead_val = int(line_lookahead * len(df_ohlcv))
    ts_val = -int(ts_pct * len(df_ohlcv)) - 1
    # df_ohlcv = get_candles_from_ccxt(coin, '1D')

    from Indicators import SupportResistanceLines2, Volume, RSI, SMA
    main_plot_indicators = [SMA(7, color='orange'), SMA(25, color='purple'), SMA(100, color='cyan'),
                            SupportResistanceLines2(lookback_length=lookback_length, plot_index=ts_val)]
    sub_plots = [Volume(), RSI(14)]
    fig = get_updated_fig(df_ohlcv, main_plot_indicators, sub_plots, xy_limit=False)

    t1 = (datetime.now() - t0).total_seconds()
    plot_index_ts = df_ohlcv.index[ts_val]
    fig.add_vline(plot_index_ts, line_color='white')
    print(f'ready at:{t1:0.2f}sec')
    t1_str = f'{t1:0.2f}'
    text = [
        html.Span(
            f'{t1_str}s, {df_ohlcv.index[ts_val]} | {len(df_ohlcv)}, {coin}, lk={lookback_length}, sup_relative={ts_val}')]
    return fig, text


# @app.callback(Output('interval-component', 'n_intervals'),
#               Input('live-update-button', 'value'),
#               Input('clock-component', 'n_intervals'),
#               Input('interval-component', 'n_intervals'))
# def clock_update(live_button, clock, interval):
#     if not live_button:
#         return interval
#     time_sec = datetime.now().second
#     print('clock_update', clock, time_sec, interval)
#     if time_sec in [10, 20, 30, 40, 50]:  # 10:  #
#         return interval + 1
#     return interval


import sys

if __name__ == '__main__':

    args = sys.argv[1:]
    print('args:', args)
    if len(args) == 2 and args[0] == '-port':
        app.run_server(port=args[1], host='0.0.0.0')
    else:
        app.run_server(debug=True)
    # https://dash.plotly.com/live-updates
    # live-updates keep the plot intact:
    # https://stackoverflow.com/questions/63876187/plotly-dash-how-to-show-the-same-selected-area-of-a-figure-between-callbacks

    # app.run_server(debug=True, port=80, host='0.0.0.0' )
