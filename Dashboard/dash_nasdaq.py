import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import sys
from Plots.plotly_fig import get_updated_fig
from Data.Nasdaq.yahoo_finance import get_from_yfinance_now
from Data.Nasdaq.data_utils import resample_ohlcv_higher_1d
from Data.Nasdaq.symbols import nasdq_100, ta_125
import random

stock_names = nasdq_100  # + ta_125
intervals = [('1', '1min'),
             ('5', '5min'),
             ('15', '15min'),
             ('H', '1h'),
             ('D', '1D'),
             ('W', '7D'),
             ('M', '30D'),
             ('Y', '365D')]

interval_names = [d[0] for d in intervals]
interval_values = [d[1] for d in intervals]

interval_names_str = [f" {k} | " for k in interval_names[:-1]] + [f" {interval_names[-1]}"]
interval_radio_options = dict(zip(interval_values, interval_names_str))

title = 'Nasdaq'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server  # needed for deployment
app.title = title

title_html = html.H4(title, style={'padding-right': '5%', 'margin-left': '2%'})

random_stock_idx = random.randint(0, len(stock_names))
coin_html = html.Div(children=[
    dcc.Dropdown(stock_names, stock_names[random_stock_idx], id='coin-type', clearable=False,
                 style=dict(width='120pt')),
    dcc.Input(id='coin-type-free', type='text', placeholder='custom (try S.NY)', value="")
], style=dict(display='flex'))
# live_update_html = html.Div(id='live-update-text', style={'margin': 'auto'}, children="")  # 'width': '20%',
interval_selector_html = dcc.RadioItems(options=interval_radio_options, value=interval_values[4], id='interval-type',
                                        inline=True)
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/input/ # RadioItems and Checklist
# disabled toggle: "disabled": True in options dict
# on toggle: set value=[1] in order to make it on when page loads
# live_update_switch_html = dbc.Checklist(options=[{"label": "Live Update", "value": 1}], value=[1],
#                                         id="live-update-button", switch=True)

right_portion_html = html.Div(id='right-portion',
                              children=[
                                  html.Div(interval_selector_html),
                                  html.Div(id='live-update-text', children="", style={"margin-left": "auto"}),
                                  dbc.Alert(
                                      "Warning! selected data could not be fetched",
                                      id="alert-problem",
                                      is_open=False,
                                      duration=3000,
                                      color="warning",
                                      style=dict(position='fixed', padding=0)
                                  )
                              ],
                              style={'display': 'flex', 'width': '40%'}
                              )

app.layout = html.Div([
    html.Div(children=[
        title_html,
        coin_html,
        dcc.Input(
            id="input_lookahead",
            type="number",
            value=14,
            placeholder="lookahead",
            style=dict(width='30pt')),
        # live_update_html,
        right_portion_html],
        style={'display': 'flex', 'align-items': 'center'},
    ),
    html.Div(id='graph-container', children=[
        dcc.Graph(id='live-update-graph', config={'scrollZoom': True,
                                                  'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'pan2d',
                                                                             'zoom2d', 'autoScale2d'],
                                                  'displaylogo': False},
                  style={'width': 'auto', 'height': '93vh'}
                  # TODO important https://stackoverflow.com/questions/46287189/how-can-i-change-the-size-of-my-dash-graph
                  ),
        # https://stackoverflow.com/questions/68188107/how-to-add-create-a-custom-loader-with-dash-plotly
        dcc.Loading(
            id="loading-2",
            children=[html.Div([html.Div(id="loading-output-2")])],
            type="circle",
            loading_state={}
        ),
        # dcc.Interval(id='interval-component', interval=INTERVAL_UPDATE_SECONDS * 1000, n_intervals=0)
    ], style=dict(display="None")
             )  # style=dict(height='100vh')
])


# @app.callback(
#     Output('interval-component', 'disabled'),
#     [Input('live-update-button', 'value')],
#     [State('interval-component', 'disabled')])
# def callback_func_start_stop_interval(button, _):
#     return len(button) == 0


# @app.callback(Output('live-update-text', 'children'),
#               Input('interval-component', 'n_intervals'))
# def update_metrics(n):
#     style = {'padding': '5px', 'fontSize': '16px'}
#     return [
#         html.Span('Interval: {0:.2f}'.format(n), style=style),
#     ]

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
              Output('alert-problem', 'is_open'),
              Input('coin-type', 'value'),
              Input('coin-type-free', 'value'),
              Input('interval-type', 'value'),
              Input('input_lookahead', 'value'))
def update_graph_live(symbol, symbol_free, tf, input_lookahead):
    print(symbol, symbol_free, tf, input_lookahead)
    if symbol_free:
        symbol = symbol_free
    try:
        df_ohlcv = get_from_yfinance_now(symbol, tf, tz='Israel')
        if not len(df_ohlcv):
            raise ValueError('df empty')
    except Exception as e:
        print('Could not get from yfianance', e, repr(e), )
        # raise dash.exceptions.PreventUpdate # raising PreventUpdate will prevent any update,
        # dash.no_update just does not update this part if not needed
        return dash.no_update, dash.no_update, True
    tf_name = interval_names[interval_values.index(tf)]

    if pd.to_timedelta(tf).days > 1:
        interval_set = '1' + tf_name
        df_ohlcv = resample_ohlcv_higher_1d(df_ohlcv, interval_set)
        print('resampled to:', interval_set)
    fig = get_updated_fig(df_ohlcv, lookahead=14, xy_limit=False)

    text = [html.Span('{}'.format(df_ohlcv.attrs['company_name']))]  # {0:.2f} #
    return fig, text, False


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
