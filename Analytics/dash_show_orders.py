import pandas as pd
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output

from Analytics.dash_utils import calc_trade_pct
from Analytics.dash_utils import discrete_background_color_bins
from Analytics.binance_fetch_all_trades import get_table
from Analytics.binance_fetch_all_trades import update_orders_table



import dash_bootstrap_components as dbc

# raw_trades = get_table()
# df = calc_trade_pct(raw_trades)
PAGE_SIZE = 20

from dash.dash_table import DataTable, FormatTemplate

money = FormatTemplate.money(3)
percentage = FormatTemplate.percentage(2)
app = dash.Dash(__name__,
                # external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])

# 'symbol', 'sell_buy_price', 'profit',
#                           'sell_p', 'buy_p', 'sell_cost', 'buy_cost', 'sell_type', 'sell_ts', 'buy_ts',
columns = [
    dict(name='symbol', id='symbol'),
    dict(name='sell_buy_price', id='sell_buy_price', type='numeric', format=percentage),
    dict(name='profit', id='profit', type='numeric', format=money),
    dict(name='sell_p', id='sell_p', type='numeric', format=money),
    dict(name='buy_p', id='buy_p', type='numeric', format=money),
    dict(name='sell_cost', id='sell_cost', type='numeric', format=money),
    dict(name='buy_cost', id='buy_cost', type='numeric', format=money),
    dict(name='sell_type', id='sell_type'),
    dict(name='is_comb', id='is_comb'),
    dict(name='sell_dt', id='sell_dt', type='datetime'),
    dict(name='buy_dt', id='buy_dt', type='datetime'),
]

app.layout = html.Div([
    html.Div(children=[dcc.Input(id='filter-input', placeholder='Filter (sql like)', debounce=True,
                                 value="buy_dt > '2022-05-27'",
                                 style=dict(width='450px')),
                       html.Div(children=[], id='middle-text'),
                       html.Button(children=html.Span("Update table"), id='update-table', n_clicks=0),
                       dcc.ConfirmDialog(id='update-confirm',
                                         message='Are you sure?'),
                       dcc.Loading(id='update-loading'),
                       html.Div(id='legend-holder', children="", style={'float': 'right'})],
             style={'display': 'flex', 'justify-content': 'space-between'}),
    dash_table.DataTable(
        id='datatable-paging',
        columns=columns,
        page_current=0,
        page_size=PAGE_SIZE,
        page_action='custom',

        sort_action='custom',
        sort_mode='single',
        style_data_conditional=None,
        style_header={
            'font-family': 'ui-monospace',
            'backgroundColor': 'rgb(30, 30, 30)',
            'color': 'white'
        },
        style_data={
            'font-family': 'ui-monospace',
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white'
        },
        sort_by=[]

    )
])


# @app.callback(Output("update-loading", "children"), Input('update-confirm', 'submit_n_clicks'))
# def input_triggers_spinner(submit_n_clicks):
#     import time
#     if submit_n_clicks:
#         time.sleep(1)
#         return ""
#     else:
#         return dash.no_update


@app.callback(
    Output('update-confirm', 'displayed'),
    Input('update-table', 'n_clicks'))
def display_confirm(n_clicks):
    if n_clicks == 1:
        return True
    return False


@app.callback(
    Output("update-loading", "children"),
    Output('update-table', 'children'),
    Input('update-confirm', 'submit_n_clicks'))
def handle_update(submit_n_clicks):
    import time
    if submit_n_clicks == 1:
        print('update-table', submit_n_clicks)
        n_added = update_orders_table()
        # n_added = 4
        # time.sleep(5)
        print('Finished!', n_added)
        return "", html.A(html.Button(f'Found {n_added} new records, Click to refresh'), href='/')
    return dash.no_update, dash.no_update


@app.callback(
    Output('datatable-paging', 'data'),
    Output('datatable-paging', 'style_data_conditional'),
    Output('legend-holder', 'children'),
    Output('middle-text', 'children'),
    [Input('datatable-paging', 'page_current'),
     Input('datatable-paging', 'page_size'),
     Input('datatable-paging', 'sort_by'),
     Input('filter-input', 'value')])
def update_table_view(page_current, page_size, sort_by, filter_string):
    # Filter
    raw_trades = get_table()
    dff = calc_trade_pct(raw_trades)
    if len(filter_string):
        dff = dff.query(filter_string)
    if len(sort_by):
        dff = dff.sort_values(
            sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=False
        )
    (styles, legend) = discrete_background_color_bins(dff, columns=['sell_buy_price'])
    text_dt = f"from={dff['buy_dt'].min()}, to={dff['sell_dt'].max()}"
    text_agg = f"sell_buy_price= {dff['sell_buy_price'].sum() :0.2%}, profit= {dff['profit'].sum(): 0.2f}, (profits corrected)"
    wrapped_text = html.Div(children=[text_dt, html.Br(), text_agg], style={'font-family': 'ui-monospace'})
    showed_rows = dff.iloc[page_current * page_size:(page_current + 1) * page_size].to_dict('records')
    return showed_rows, styles, legend, wrapped_text


if __name__ == '__main__':
    app.run_server(debug=True, port=8060)
