from dash import html
import pandas as pd
from time import time


def calc_trade_pct(raw_trades):
    t0 = time()
    # Smart calc trade, it will combine buys into one sell.
    df = raw_trades
    buys = df[df['side'] == 'buy']
    sells = df[df['side'] == 'sell']
    # [symbol, sell_buy_price, profit,  sell_price, buy_price, sell_cost, buy_cost, sell_type, sell_dt, buy_dt])
    sells = sells.groupby(['order_id', 'ts', 'dt', 'symbol', 'type', 'price']).agg(
        {'cost': 'sum', 'amount': 'sum'}).reset_index()
    res = []
    columns = ['symbol', 'sell_buy_price', 'profit',
               'sell_p', 'buy_p', 'sell_cost', 'buy_cost', 'sell_type', 'is_comb', 'sell_dt', 'buy_dt']
    sells = sells.sort_values('ts', ascending=False)
    for i, sell in sells.iterrows():
        symbol = sell['symbol']
        # calc previous sell ts
        previous_sell_ts = 0
        previous_sells = sells[(sells.symbol == symbol) & (sells.ts < sell.ts)]
        if len(previous_sells):
            previous_sell_ts = previous_sells['ts'].max()
        # filter out buys, we always sell all of it so can filter with previous sell_ts
        buy_df = buys[(buys['symbol'] == symbol) & (buys['ts'] < sell['ts']) & (buys['ts'] > previous_sell_ts)].sort_values('ts', ascending=False)
        if not len(buy_df):
            print(f'Buy for {symbol} not found')
            continue
        l_buy = buy_df.iloc[0]
        is_combined = False
        if l_buy['amount'] < sell['amount']:
            amount_before = l_buy['amount']
            combined_buy = buy_df.groupby('symbol').agg(dict(dt='first', price='mean', cost='sum', amount='sum')).reset_index()
            assert len(combined_buy) == 1
            l_buy = combined_buy.iloc[0]
            is_combined = True
            print(f"{symbol} Combined {len(buy_df)} buy into one total: buy_before={amount_before}, buy_after={l_buy['amount']}, sell={sell['amount']}")
        buy_price = l_buy['price']
        buy_cost = l_buy['cost']
        buy_dt = l_buy['dt']
        sell_price = sell['price']
        sell_cost = sell['cost']
        sell_dt = sell['dt']
        sell_type = sell['type']
        profit = sell_cost - buy_cost

        sell_buy_price = (sell_price / buy_price) - 1
        res.append(
            [symbol, sell_buy_price, profit, sell_price, buy_price, sell_cost, buy_cost, sell_type, is_combined, sell_dt, buy_dt])
        # res.append([symbol, profit, pct, sell_price, buy_price, sell_dt, buy_dt])
    df_trades = pd.DataFrame(res, columns=columns)
    # remove the timezone from dt by slicing
    df_trades['sell_dt'] = pd.to_datetime(df_trades['sell_dt'].str.slice(0, -5), utc=False)
    df_trades['buy_dt'] = pd.to_datetime(df_trades['buy_dt'].str.slice(0, -5), utc=False)
    t1 = time()
    print('TOTAL SELL/BUY %:', df_trades['sell_buy_price'].sum(), f'time= {t1-t0:0.2f}sec')
    return df_trades


def discrete_background_color_bins(df, n_bins=10, columns='all'):
    import colorlover
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    if columns == 'all':
        if 'id' in df:
            df_numeric_columns = df.select_dtypes('number').drop(['id'], axis=1)
        else:
            df_numeric_columns = df.select_dtypes('number')
    else:
        df_numeric_columns = df[columns]
    df_max = 0.2  # df_numeric_columns.max().max()
    df_min = -0.2  # df_numeric_columns.min().min()
    ranges = [((df_max - df_min) * i) + df_min for i in bounds]
    ranges[0] = -1
    ranges[-1] = 1
    styles = []
    legend = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        bg_color = colorlover.scales[str(n_bins)]['div']['RdYlGn'][i - 1]
        color = 'white' if i == 1 or i == len(bounds)-1 else 'inherit'

        for column in df_numeric_columns:
            styles.append({
                'if': {
                    'filter_query': (
                            '{{{column}}} >= {min_bound}' +
                            (' && {{{column}}} < {max_bound}' if (i < len(bounds) - 1) else '')
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    'column_id': column
                },
                'backgroundColor': bg_color,
                'color': color
            })
        legend.append(
            html.Div(style={'display': 'inline-block', 'width': '35px'}, children=[
                html.Div(
                    style={
                        'backgroundColor': bg_color,
                        'borderLeft': '1px rgb(50, 50, 50) solid',
                        'height': '10px'
                    }
                ),
                html.Small(f'{round(min_bound * 100)}%', style={'paddingLeft': '2px'}) if i > 1 else html.Small('%:')
            ])
        )
    return styles, html.Div(legend, style={'padding': '5px 0 5px 0'})
