# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import ccxt  # noqa: E402
from Data.Crypto.symbols import exchange_symbol_pairs


def get_from_exchange():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.path.append(root + '/python')

    exchange = ccxt.binance({
        'apiKey': os.environ.get('BINANCE_API'),
        'secret': os.environ.get('BINANCE_SECRET'),
        'enableRateLimit': True,
        # 'options': {
        #     'defaultType': 'spot', // spot, future, margin
        # },
    })
    symbols = sorted([c[1] for c in exchange_symbol_pairs])
    exchange.load_markets()
    day = 24 * 60 * 60 * 1000
    start_date = '2022-05-25'
    start_time = exchange.parse8601(f'{start_date}T00:00:00')
    now = exchange.milliseconds()
    dt_now = pd.to_datetime(now, unit='ms')

    all_trades = []
    for symbol in symbols:
        trades = exchange.fetch_my_trades(symbol, start_time, None)
        if not len(trades):
            continue
        print(symbol, len(trades))
        for i, trade in enumerate(trades):
            all_trades.append(trade)
            print(i, symbol, trade['datetime'], trade['side'], trade['takerOrMaker'], trade['price'], trade['amount'],
                  trade['cost'])
    print('data)')
    df = pd.DataFrame(all_trades).drop(columns=['info'])
    df.to_csv(f'all_trades_{start_date}_{dt_now}.csv', index=False)


def analyize():
    df = pd.read_csv('all_trades_2022-05-25.csv')  # 27
    buys = df[df['side'] == 'buy']
    sells = df[df['side'] == 'sell']
    # trade can be split
    sells = sells.groupby(['timestamp', 'datetime', 'symbol']).agg({'cost': 'sum', 'amount': 'sum'}).reset_index()
    # ------------------------
    #     ---------sell----------
    print('-symbol-\tprofit\t--pct--\t---------sell----------\t---------buy----------')
    for i, sell in sells.sort_values('timestamp', ascending=False).iterrows():
        symbol = sell['symbol']
        buy_df = buys[(buys['symbol'] == symbol) & (buys['timestamp'] < sell['timestamp'])].sort_values('timestamp',
                                                                                                        ascending=False)
        if not len(buy_df):
            print(f'Buy for {symbol} not found')
            continue
        l_buy = buy_df.iloc[0]
        buy_cost = l_buy['cost']
        buy_dt = l_buy['datetime']
        sell_cost = sell['cost']
        sell_dt = sell['datetime']
        profit = sell_cost - buy_cost
        pct = (sell_cost / buy_cost) - 1
        print(f'{symbol}\t{profit:0.2f}\t{pct:0.2%}\t{sell_dt}\t{buy_dt}')


if __name__ == '__main__':
    get_from_exchange()
    analyize()

# while start_time < now:
#     print('------------------------------------------------------------------')
#     print('Fetching trades from', exchange.iso8601(start_time))
#     end_time = start_time + day
#
#     # trades = exchange.fetch_my_trades (symbol, start_time, None, {
#     #     'endTime': end_time,
#     # })
#     trades = exchange.fetch_my_trades (symbol, start_time, None
#     )
#     if len(trades):
#         last_trade = trades[len(trades) - 1]
#         start_time = last_trade['timestamp'] + 1
#         all_trades = all_trades + trades
#     else:
#         start_time = end_time
#
# print('Fetched', len(all_trades), 'trades')
# for i in range(0, len(all_trades)):
#     trade = all_trades[i]
#     # print(i, trade['datetime'], trade['id'], trade['side'], trade['takerOrMaker'], trade['price'], trade['amount'],
#     #       trade['cost'])
#     print (i, trade['datetime'], trade['side'], trade['takerOrMaker'], trade['price'], trade['amount'], trade['cost'])
