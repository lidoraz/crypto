import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime
import json
import sys


from Backtesting.Strategies import All_STRATEGIES, EMAVol, EMATrendSTC, EMABB
from Data.Crypto.ccxt_utils import get_candles_from_db
from Data.Crypto.symbols import exchange_symbol_pairs, DB_PATH
from Plots.plotly_fig import get_updated_fig
from Plots.plot_utils import *
from Utils import Persistence

coins = sorted([c[1].split('/')[0] for c in exchange_symbol_pairs])
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())
resample_keywords_text = [f" {k} | " for k in resample_keywords[:-1]] + [f" {resample_keywords[-1]}"]
default_tf = '1H'
default_coin = 'BTC'

resample_radio_options = dict(
    zip(resample_keywords, resample_keywords_text))  # {k: f' {k} |' for k in resample_keywords}

db_path = DB_PATH
db = Persistence(db_path, check_same_thread=False)

title = 'Crypto Test Strategy'

app = dash.Dash("foo", external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server  # needed for deployment
app.title = title

title_html = html.Div(title, style={'padding-right': '1%', 'margin-left': '2%'})
coin_html = dcc.Dropdown(coins, default_coin, id='coin-type', clearable=False, style=dict(width='60pt'))
live_update_html = html.Div(id='live-update-text', style={'margin': 'auto', 'font-size': 12, 'padding': '5px'},
                            children="")  # 'width': '20%',
resample_selector_html = dcc.RadioItems(options=resample_radio_options, value=default_tf, id='resample-type',
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
        dcc.Input(id="n-data-back", value="1", debounce=True, placeholder='N back', style={'width': '30px'}),
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
                                                  'modeBarButtonsToRemove': ['select2d', 'lasso2d',],
                                                  # 'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'pan2d',
                                                  #                            'zoom2d', 'autoScale2d'],
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


def add_buy_sell_to_fig(df_ohlcv, fig, show_res=False):
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
    # fig.add_vline(df_ohlcv.index[200], row=1, col=1, line_color='white')
    return fig


def get_indicators(strategy=None, strategy_params=None):
    from Indicators import Volume
    strategy = strategy(strategy_params)
    strategy_indicators = [vars(strategy)[v] for v in vars(strategy) if v.startswith('_ind_')]
    main_plot_indicators = [ind for ind in strategy_indicators if ind.location == 'MAIN_PLOT']
    sub_plots = [ind for ind in strategy_indicators if ind not in main_plot_indicators]
    if len(sub_plots) == 0:
        sub_plots.append(Volume())
    return strategy, main_plot_indicators, sub_plots


def choose_strategy(strategy_params_text):
    strategy = None
    strategy_params = None
    if len(strategy_params_text) > 0:
        strategy_params = json.loads(strategy_params_text)
        strategy = All_STRATEGIES[strategy_params['name']]
        print('chosen strategy', strategy)
    return strategy, strategy_params


def get_data_with_adjusted_dt(coin, resample, n_lookback_ratio, start_date, localize=None):
    end_date = None
    lookback_candles = 200
    if len(start_date):
        # in order to fail with indicators, its better to take 200 candles prior to start_date and start date will be a start display
        start_ts = int((pd.to_datetime(start_date) - pd.to_timedelta(resample) * lookback_candles).timestamp())
        end_date = pd.to_datetime(start_date) + INTERVAL_CANDLE_LOOKBACK_TABLE[resample] * n_lookback_ratio
    else:
        time_delta = pd.to_timedelta(resample) * lookback_candles + INTERVAL_CANDLE_LOOKBACK_TABLE[
            resample] * n_lookback_ratio
        start_ts = int((datetime.utcnow() - time_delta).timestamp())
    # Small bug, using utcnow above, will cause empty dataframe if crawler was not working for a while, better solution is to take latest datapoint available in the database instead.
    df_ohlcv = get_candles_from_db(db, coin, resample, start_ts=start_ts, localize=localize)
    if end_date:
        df_ohlcv = df_ohlcv[df_ohlcv.index <= pd.to_datetime(end_date, utc=True)]
        if localize:
            df_ohlcv = df_ohlcv.tz_convert(localize)
    return df_ohlcv


@app.callback(Output('live-update-graph', 'figure'),
              Output('live-update-text', 'children'),
              Output('alert-problem', 'children'),
              Output('alert-problem', 'is_open'),
              Input('start-date', 'value'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'),
              Input('n-data-back', 'value'),
              Input('strategy-params', 'value'))
def update_graph_live(start_date, coin, resample, n_lookback_ratio, strategy_params_text):
    try:
        assert len(n_lookback_ratio)
        n_lookback_ratio = float(n_lookback_ratio)
        assert n_lookback_ratio >= 1
    except ValueError as e:
        n_data_back = 1
    print(start_date, coin, resample)
    t0 = datetime.now()
    try:
        strategy, strategy_params = choose_strategy(strategy_params_text)
    except Exception as e:
        print('JSONDecoder failed..')
        return dash.no_update, dash.no_update, str(repr(e)), True
    " # ------------------------------------------------------------------------------------------------ "

    if not strategy:
        strategy = All_STRATEGIES['S3']
        strategy = All_STRATEGIES['THESTRAT']
        # strategy = EMABB()
        # strategy = EMA3()
        # strategy = ADXRSI()
        strategy_params = {'db': db,
                           "adx_use_smooth": False,
                           "adx_threshold": 20, "max_stop_pct": 0.07, "support_ahead": 10, "risk_reward": 1.5}
        # strategy_params = {"tf": "1H", "ema_slow_lk": 200, "ema_mid_lk": 50, "n_ema_soon": 3,
        #                    "crossed_ma_low_high": True, "adx_use_smooth": False,
        #                    "adx_threshold": 20, "max_stop_pct": 0.07, "support_ahead": 10, "risk_reward": 1.5}
    " # ------------------------------------------------------------------------------------------------ "
    strategy, main_plot_indicators, sub_plots = get_indicators(strategy, strategy_params)
    localize = 'Israel' # None  # 'Israel'
    df = get_data_with_adjusted_dt(coin, resample, n_lookback_ratio, start_date, localize)
    df = strategy.add_indicators(df)
    fig = get_updated_fig(df, main_plot_indicators, sub_plots, xy_limit=False, calc_ind=False)
    show_resistance_supports = True
    fig = add_buy_sell_to_fig(df, fig, show_res=show_resistance_supports)

    time_conv = "%b %d, %H:%M"  # .strftime
    t1 = f'{(datetime.now() - t0).total_seconds():0.2f}'
    text = [html.Div(f'({df.index[0].strftime(time_conv)} => {df.index[-1].strftime(time_conv)}), {t1}s'
                     f'\n{coin}, rows={len(df)}'),
            html.Div(f'{repr(strategy)}')]
    print(f'ready at:{t1}sec')
    return fig, text, None, False


if __name__ == '__main__':
    args = sys.argv[1:]
    print('args:', args)
    if len(args) == 2 and args[0] == '-port':
        app.run_server(port=args[1], host='0.0.0.0')
    else:
        app.run_server(debug=False)  # , dev_tools_ui=True
    # https://dash.plotly.com/live-updates
    # live-updates keep the plot intact:
    # https://stackoverflow.com/questions/63876187/plotly-dash-how-to-show-the-same-selected-area-of-a-figure-between-callbacks

    # app.run_server(debug=True, port=80, host='0.0.0.0' )
