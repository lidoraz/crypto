import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from DataProcessing.data_utils import get_data_providers
from DataProcessing.data_utils import adjust_plot_start_datetime
from DataProcessing.data_consts import *
from Plots.plot_utils import *
from Plots.plotly_fig import get_updated_fig
import dash_bootstrap_components as dbc

coins = COINS
hourly_cols = HOURLY_COLS
resample_keywords = list(INTERVAL_CANDLE_LOOKBACK_TABLE.keys())
resample_radio_options = {k: f' {k} |' for k in resample_keywords}

providers = get_data_providers()
#
title = 'Crypto Live Feed'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])
server = app.server  # needed for deployment
app.title = title

title_html = html.H4(title, style={'padding-right': '5%', 'margin-left': '2%'})
coin_html = html.Div(dcc.Dropdown(COINS, COINS[0], id='coin-type', clearable=False),
                     style=dict(width='6%'))
live_update_html = html.Div(id='live-update-text', style={'margin': 'auto'}, children="")  # 'width': '20%',
resample_selector_html = dcc.RadioItems(options=resample_radio_options, value=resample_keywords[2], id='resample-type',
                                        inline=True)
# https://dash-bootstrap-components.opensource.faculty.ai/docs/components/input/ # RadioItems and Checklist
# disabled toggle: "disabled": True in options dict
# on toggle: set value=[1] in order to make it on when page loads
live_update_switch_html = dbc.Checklist(options=[{"label": "Live Update", "value": 1}], value=[1],
                                        id="live-update-button", switch=True)

right_portion_html = html.Div(id='right-portion',
                              children=[html.Div(resample_selector_html),
                                        html.Div(id='live-switch-update-container',
                                                 children=live_update_switch_html,
                                                 style={'padding-left': '3%'})],
                              style={'display': 'flex', 'width': '40%'})

app.layout = html.Div([
    html.Div(children=[
        title_html,
        coin_html,
        live_update_html,
        right_portion_html],
        style={'display': 'flex', 'align-items': 'center'},
    ),
    html.Div(id='graph-container', children=[
        dcc.Graph(id='live-update-graph', config={'scrollZoom': True, 'displayModeBar': False}, ),
        dcc.Interval(id='interval-component', interval=INTERVAL_UPDATE_SECONDS * 1000, n_intervals=0)
    ], style=dict(display="None")
             )  # style=dict(height='100vh')
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


# show graph only when ready to display, to avoid blank white figure
@app.callback(Output('graph-container', 'style'),
              Input('live-update-graph', 'figure'))
def show_graph_when_loaded(figure):
    # print("show_graph_when_loaded", figure)
    if figure is None:
        return {'display': 'None'}
    else:
        return None


@app.callback(Output('live-update-graph', 'figure'),
              Input('interval-component', 'n_intervals'),
              Input('coin-type', 'value'),
              Input('resample-type', 'value'))
def update_graph_live(n, coin, resample):
    print(n, coin, resample)
    filter_datetime = adjust_plot_start_datetime(resample)
    keep_with_interval = True  # move this

    fig = get_updated_fig(providers, filter_datetime, resample, coin, xy_limit=True)

    # used to keep figure with changes when this function is triggered.
    # can add option for figure to be limited with XY when interval==0, after that this function will be disabled.
    # if keep_with_interval:
    #     fig.update_layout({'uirevision': f'foo'}) # {coin}{resample}
    # fig.update_layout(height=110)
    # print('fig:::', fig.layout.figure.layout.xaxis.range)
    return fig


if __name__ == '__main__':
    # https://dash.plotly.com/live-updates
    # live-updates keep the plot intact:
    # https://stackoverflow.com/questions/63876187/plotly-dash-how-to-show-the-same-selected-area-of-a-figure-between-callbacks
    app.run_server(debug=True)
