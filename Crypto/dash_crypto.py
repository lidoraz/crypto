# import dash
# from dash import dcc, html
# from dash.dependencies import Input, Output, State
# from DataProcessing.data_utils import get_data_providers, get_crypto_olhcv
# from DataProcessing.data_utils import adjust_plot_start_datetime
# from DataProcessing.data_consts import *
# from Plots.plot_utils import *
# from Plots.plotly_fig import get_updated_fig
# import dash_bootstrap_components as dbc
# from datetime import datetime
#
# coins = COINS
# hourly_cols = HOURLY_COLS
# resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())
# resample_keywords_text = [f" {k} | " for k in resample_keywords[:-1]] + [f" {resample_keywords[-1]}"]
# resample_radio_options = dict(
#     zip(resample_keywords, resample_keywords_text))  # {k: f' {k} |' for k in resample_keywords}
#
# providers = get_data_providers()
# #
# title = 'Crypto Live Feed'
#
# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
#                 meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
# server = app.server  # needed for deployment
# app.title = title
#
# title_html = html.H4(title, style={'padding-right': '5%', 'margin-left': '2%'})
# coin_html = dcc.Dropdown(COINS, COINS[0], id='coin-type', clearable=False, style=dict(width='60pt'))
# live_update_html = html.Div(id='live-update-text', style={'margin': 'auto'}, children="")  # 'width': '20%',
# resample_selector_html = dcc.RadioItems(options=resample_radio_options, value=resample_keywords[2], id='resample-type',
#                                         inline=True)
# # https://dash-bootstrap-components.opensource.faculty.ai/docs/components/input/ # RadioItems and Checklist
# # disabled toggle: "disabled": True in options dict
# # on toggle: set value=[1] in order to make it on when page loads
# live_update_switch_html = dbc.Checklist(options=[{"label": "Live Update", "value": 1}], value=[1],
#                                         id="live-update-button", switch=True)
#
# right_portion_html = html.Div(id='right-portion',
#                               children=[html.Div(resample_selector_html),
#                                         html.Div(id='live-switch-update-container',
#                                                  children=live_update_switch_html,
#                                                  style={'padding-left': '3%'})],
#                               # style={'display': 'flex', 'width': '40%'}
#                               )
#
# app.layout = html.Div([
#     html.Div(children=[
#         title_html,
#         coin_html,
#         dcc.Input(
#             id="input_lookahead",
#             type="number",
#             value=14,
#             placeholder="lookahead",
#             style=dict(width='30pt')),
#         live_update_html,
#         right_portion_html],
#         style={'display': 'flex', 'align-items': 'center'},
#     ),
#     html.Div(id='graph-container', children=[
#         dcc.Graph(id='live-update-graph', config={'scrollZoom': True,
#                                                   'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'pan2d',
#                                                                              'zoom2d', 'autoScale2d'],
#                                                   'displaylogo': False},
#                   style={'width': 'auto', 'height': '93vh'}
#                   # TODO important https://stackoverflow.com/questions/46287189/how-can-i-change-the-size-of-my-dash-graph
#                   ),
#         # https://stackoverflow.com/questions/68188107/how-to-add-create-a-custom-loader-with-dash-plotly
#         dcc.Loading(
#             id="loading-2",
#             children=[html.Div([html.Div(id="loading-output-2")])],
#             type="circle",
#             loading_state={}
#         ),
#         dcc.Interval(id='interval-component', interval=INTERVAL_UPDATE_SECONDS * 1000, n_intervals=0)
#     ], style=dict(display="None")
#              )  # style=dict(height='100vh')
# ])
#
#
# @app.callback(
#     Output('interval-component', 'disabled'),
#     [Input('live-update-button', 'value')],
#     [State('interval-component', 'disabled')])
# def callback_func_start_stop_interval(button, _):
#     return len(button) == 0
#
#
# @app.callback(Output('live-update-text', 'children'),
#               Input('interval-component', 'n_intervals'))
# def update_metrics(n):
#     style = {'padding': '5px', 'fontSize': '16px'}
#     return [
#         html.Span('Interval: {0:.2f}'.format(n), style=style),
#     ]
#
#
# @app.callback(Output('interval-component', 'n_intervals'),
#               Input('coin-type', 'value'))
# def interval_update(_):
#     return 0
#
#
# # show graph only when ready to display, to avoid blank white figure
# @app.callback(Output('graph-container', 'style'),
#               Input('live-update-graph', 'figure'))
# def show_graph_when_loaded(figure):
#     # print("show_graph_when_loaded", figure)
#     if figure is None:
#         return {'display': 'None'}
#     else:
#         return None
#
#
# def _adjust_input_lookahead(input_lookahead):
#     if input_lookahead is None:
#         input_lookahead = 14
#     return max(min(input_lookahead, 100), 3)
#
#
# @app.callback(Output('live-update-graph', 'figure'),
#               Input('interval-component', 'n_intervals'),
#               Input('coin-type', 'value'),
#               Input('resample-type', 'value'),
#               Input('input_lookahead', 'value'))
# def update_graph_live(n, coin, resample, input_lookahead):
#     t0 = datetime.now()
#     print(n, coin, resample, input_lookahead)
#     filter_datetime = adjust_plot_start_datetime(resample)
#     input_lookahead = _adjust_input_lookahead(input_lookahead)
#     df_ohlcv = get_crypto_olhcv(coin, resample, providers, filter_datetime, is_volume_hourto=True)
#     fig = get_updated_fig(df_ohlcv, lookahead=input_lookahead, xy_limit=True)
#     t1 = (datetime.now() - t0).total_seconds()
#     print(f'ready at:{round(t1, 2)}sec')
#     return fig
#
#
# import sys
#
# if __name__ == '__main__':
#     args = sys.argv[1:]
#     print('args:', args)
#     if len(args) == 2 and args[0] == '-port':
#         app.run_server(port=args[1], host='0.0.0.0')
#     else:
#         app.run_server(debug=True)
#     # https://dash.plotly.com/live-updates
#     # live-updates keep the plot intact:
#     # https://stackoverflow.com/questions/63876187/plotly-dash-how-to-show-the-same-selected-area-of-a-figure-between-callbacks
#
#     # app.run_server(debug=True, port=80, host='0.0.0.0' )
