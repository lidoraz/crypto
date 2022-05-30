import pandas as pd
import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output


def discrete_background_color_bins(df, n_bins=5, columns='all'):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = df_numeric_columns.max().max()
    df_min = df_numeric_columns.min().min()
    ranges = [
        ((df_max - df_min) * i) + df_min for i in bounds
    ]
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        backgroundColor = colorlover.scales[str(n_bins)]['div']['RdYlGn'][i - 1]
        color = 'white' if i > len(bounds) / 2. else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                            '{{{column}}} >= {min_bound}' +
                            (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': backgroundColor,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '60px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': backgroundColor,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(round(min_bound, 2), style={'paddingLeft': '2px'})
            ])
        )

    return (styles, html.Div(legend, style={'padding': '5px 0 5px 0'}))


import dash_bootstrap_components as dbc

import sqlite3

# con = sqlite3.connect("/Users/lidorazulay/Downloads/trade_orders.db")
# sql = "select * from orders order by ts desc"
# df = pd.read_sql_query(sql, con)
df = pd.read_csv('/Users/lidorazulay/Documents/DS/crypto/Analytics/resources/trades_from_2022-05-25.csv')
PAGE_SIZE = 80

from dash.dash_table import DataTable, FormatTemplate

money = FormatTemplate.money(4)
percentage = FormatTemplate.percentage(2)
app = dash.Dash(__name__,
                # external_stylesheets=[dbc.themes.CYBORG],
                meta_tags=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}])

# 'symbol', 'sell_buy_price', 'profit',
#                           'sell_p', 'buy_p', 'sell_cost', 'buy_cost', 'sell_type', 'sell_ts', 'buy_ts',
columns = [
    # dict(name='Unnamed: 0', id='Unnamed: 0'),
    dict(name='symbol', id='symbol'),
    dict(name='sell_buy_price', id='sell_buy_price', type='numeric', format=percentage),
    dict(name='profit', id='profit', type='numeric', format=money),
    dict(name='sell_p', id='sell_p', type='numeric', format=money),
    dict(name='buy_p', id='buy_p', type='numeric', format=money),
    dict(name='sell_cost', id='sell_cost', type='numeric', format=money),
    dict(name='buy_cost', id='buy_cost', type='numeric', format=money),
    dict(name='sell_type', id='sell_type'),
    dict(name='sell_ts', id='sell_ts', type='datetime'),
    dict(name='buy_ts', id='buy_ts', type='datetime'),
]
# columns = [{"name": i, "id": i} for i in df.columns]  # sorted(df.columns)]
app = dash.Dash(__name__)

(styles, legend) = discrete_background_color_bins(df, columns=['sell_buy_price'])

app.layout = html.Div([
    dcc.Input(value='', id='filter-input', placeholder='Filter (sql like)', debounce=True, style=dict(width='450px')),
    html.Div(legend, style={'float': 'right'}),
    dash_table.DataTable(
        id='datatable-paging',
        columns=columns,
        page_current=0,
        page_size=PAGE_SIZE,
        page_action='custom',

        sort_action='custom',
        sort_mode='single',
        style_data_conditional=styles,
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


@app.callback(
    Output('datatable-paging', 'data'),
    [Input('datatable-paging', 'page_current'),
     Input('datatable-paging', 'page_size'),
     Input('datatable-paging', 'sort_by'),
     Input('filter-input', 'value')])
def update_table(page_current, page_size, sort_by, filter_string):
    # Filter
    dff = df
    if len(filter_string):
        dff = df.query(filter_string)
    # dff = df[df.apply(lambda row: row.str.contains(filter_string, regex=False).any(), axis=1)]
    # Sort if necessary
    if len(sort_by):
        dff = dff.sort_values(
            sort_by[0]['column_id'],
            ascending=sort_by[0]['direction'] == 'asc',
            inplace=False
        )

    return dff.iloc[
           page_current * page_size:(page_current + 1) * page_size
           ].to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=True, port=8060)
