import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import sys
import random

from AStock.sectors import all_etf_longname, get_daily_data, visualize

stock_names = all_etf_longname  # + ta_125

title = 'ETFs'

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])
server = app.server  # needed for deployment
app.title = title

title_html = html.H4(title, style={'padding-right': '5%', 'margin-left': '2%'})

# random_stock_idx = random.randint(0, len(stock_names))
coin_html = html.Div(children=[
    # dcc.Dropdown(stock_names, stock_names[random_stock_idx], id='coin-type', clearable=False,
    #              style=dict(width='120pt')),
    dcc.Input(id='n_months', type='text', placeholder='months', value="48", debounce=True),
], style=dict(display='flex'))
right_portion_html = html.Div(id='right-portion',
                              children=[
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
        # dcc.Input(
        #     id="input_lookahead",
        #     type="number",
        #     value=14,
        #     placeholder="lookahead",
        #     style=dict(width='30pt')),
        right_portion_html],
        style={'display': 'flex', 'align-items': 'center'},
    ),
    html.Div(id='graph-container', children=[
        dcc.Graph(id='live-update-graph', config={'scrollZoom': True,
                                                  # 'modeBarButtonsToRemove': ['toImage', 'select2d', 'lasso2d', 'pan2d',
                                                  #                            'zoom2d', 'autoScale2d'],
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
              Input('n_months', 'value'))
def update_graph_live(n_months):
    try:
        n_months = int(n_months)
    except ValueError():
        return dash.no_update
    # Input('symbol', 'value'),
    print(n_months)
    data = get_daily_data(list(all_etf_longname.keys()), n_months=n_months)
    fig = visualize(data, norm=True)
    fig.update_layout(template="plotly_dark",)
    # text = [html.Span('{} months ago'.format(n_months))]  # {0:.2f} #
    return fig # , text


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
