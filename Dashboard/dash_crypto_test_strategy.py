import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import json

from Backtesting.Strategies import All_STRATEGIES, HighChange, EMAVol
from Data.Crypto.ccxt_utils import get_candles_from_db
from Data.Crypto.symbols import exchange_symbol_pairs, DB_PATH
from Plots.plotly_fig import get_updated_fig
from Plots.plot_utils import *
from Utils import Persistence

coins = sorted([c[1].split('/')[0] for c in exchange_symbol_pairs])
coins = ['BTC', 'ETH', 'BNB', 'XRP', 'ADA', 'SOL', 'DOGE', 'SHIB']
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())
resample_keywords_text = [f" {k} | " for k in resample_keywords[:-1]] + [f" {resample_keywords[-1]}"]
resample_radio_options = dict(
    zip(resample_keywords, resample_keywords_text))  # {k: f' {k} |' for k in resample_keywords}

db_path = DB_PATH
db = Persistence(db_path, check_same_thread=False)

title = 'Crypto Test Strategy'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server  # needed for deployment
app.title = title

title_html = html.Div(title, style={'padding-right': '5%', 'margin-left': '2%'})
coin_html = dcc.Dropdown(coins, 'BTC', id='coin-type', clearable=False, style=dict(width='60pt'))
live_update_html = html.Div(id='live-update-text', style={'margin': 'auto'}, children="")  # 'width': '20%',
resample_selector_html = dcc.RadioItems(options=resample_radio_options, value=resample_keywords[0], id='resample-type',
                                        inline=True)
right_portion_html = html.Div(id='right-portion',
                              children=[html.Div(resample_selector_html)],
                              style={'width': '30%'})
alert_html = dbc.Alert(
    "Warning! selected data could not be fetched",
    id="alert-problem",
    is_open=False,
    duration=3000,
    color="warning",
    style=dict(position='fixed', padding=20)
)
app.layout = html.Div([
    html.Div(children=[
        title_html,
        html.Div([coin_html,
                  dcc.Input(id='start-date', placeholder='start_date', value="", debounce=True,
                            )],
                 style={'display': 'flex'}),
        dcc.Input(
            id="strategy-params",
            value="",
            debounce=True,
            # wrap='wrap',
            placeholder="strategy_params",
            style={'width': '90%', 'height': '50px', 'text-size': '4px'},
        ),
        # html.Button('Submit', id='json-button', n_clicks=0),
        alert_html,
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


def get_indicators(strategy=None):
    from Indicators import Volume
    if not strategy:
        strategy = EMAVol()
        # strategy = HighChange({"pct": 0.015, "vol_pct": 1.15})

    strategy_indicators = [vars(strategy)[v] for v in vars(strategy) if v.startswith('_ind_')]
    main_plot_indicators_names = ('BB', 'SUPPORT_RESISTANCE', 'SMA', 'EMA')
    main_plot_indicators = [ind for ind in strategy_indicators if ind.name in main_plot_indicators_names]
    sub_plots = [ind for ind in strategy_indicators if ind not in main_plot_indicators]
    if len(sub_plots) == 0:
        sub_plots.append(Volume())
    return strategy, main_plot_indicators, sub_plots


def add_buy_sell_to_fig(df_ohlcv, strategy, fig, show_res=False):
    df_ohlcv = strategy.add_indicators(df_ohlcv)
    # return fig
    buy_locations = df_ohlcv['BUY_ALGO'][df_ohlcv['BUY_ALGO']].index
    sell_locations = df_ohlcv['SELL_ALGO'][df_ohlcv['SELL_ALGO']].index
    print_cols = ['resistance', 'support']
    print(f'Total buy_locations={len(buy_locations)}, sell_locations={len(sell_locations)}')
    for buy_loc in buy_locations:
        if show_res:
            support_res_lines = df_ohlcv.loc[buy_loc][print_cols]
            support_res_pct = (support_res_lines / df_ohlcv.loc[buy_loc]['close']).apply(lambda x: f'{x:.2%}')
            print('BUY:', buy_loc, support_res_pct.to_dict(), support_res_lines.to_dict())
        fig.add_vline(buy_loc, row=1, col=1, line_color='green', opacity=0.4)
    for sell_loc in sell_locations:
        if show_res:
            support_res_lines = df_ohlcv.loc[sell_loc][print_cols]
            support_res_pct = (support_res_lines / df_ohlcv.loc[sell_loc]['close']).apply(lambda x: f'{x:.2%}')
            print('SELL:', sell_loc, support_res_pct.to_dict(), support_res_lines.to_dict())
        fig.add_vline(sell_loc, row=1, col=1, line_color='red', opacity=0.4)
    return fig


@app.callback(Output('live-update-graph', 'figure'),
              Output('live-update-text', 'children'),
              Output('alert-problem', 'children'),
              Output('alert-problem', 'is_open'),
              Input('start-date', 'value'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'),
              Input('strategy-params', 'value'))
def update_graph_live(start_date, coin, resample, strategy_params_text):
    strategy = None
    end_date = None
    print(start_date, coin, resample)
    t0 = datetime.now()
    try:
        if len(strategy_params_text) > 0:
            strategy_params = json.loads(strategy_params_text)
            strategy = All_STRATEGIES[strategy_params['name']](strategy_params)
            print('chosen strategy', strategy)
    except Exception as e:
        print('JSONDecoder failed..')
        return dash.no_update, dash.no_update, str(repr(e)), True
    if len(start_date):
        start_ts = int(pd.to_datetime(start_date).timestamp())
        end_date = pd.to_datetime(start_date) + INTERVAL_CANDLE_LOOKBACK_TABLE[resample]
    else:
        start_ts = int((datetime.utcnow() - INTERVAL_CANDLE_LOOKBACK_TABLE[resample]).timestamp())
    df_ohlcv = get_candles_from_db(db, coin, resample, start_ts=start_ts)
    if end_date:
        df_ohlcv = df_ohlcv[df_ohlcv.index <= pd.to_datetime(end_date, utc=True).tz_convert('Israel')]

    strategy, main_plot_indicators, sub_plots = get_indicators(strategy)
    fig = get_updated_fig(df_ohlcv, main_plot_indicators, sub_plots, xy_limit=False)
    fig = add_buy_sell_to_fig(df_ohlcv, strategy, fig, show_res=True)

    time_conv = "%b %d, %H:%M"  # .strftime
    t1 = f'{(datetime.now() - t0).total_seconds():0.2f}'
    text = [html.Div(f'({df_ohlcv.index[0].strftime(time_conv)} => {df_ohlcv.index[-1].strftime(time_conv)}), {t1}s'
                     f'\n{coin}, rows={len(df_ohlcv)}'),
            html.Div(f'{repr(strategy)}')]
    print(f'ready at:{t1}sec')
    return fig, text, None, False


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
