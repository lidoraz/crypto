# -*- coding: utf-8 -*-

import os
import sys
import pandas as pd
import ccxt  # noqa: E402
from Data.Crypto.symbols import exchange_symbol_pairs

def get_from_exchange():

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
        trades_info = exchange.fetch_orders(symbol, start_time, None)
        if not len(trades):
            continue
        print(symbol, len(trades))
        for i, trade in enumerate(trades):
            trade_info = pd.DataFrame(trades_info).set_index('id').loc[trade['order']]
            trade['type'] = trade_info['type']
            all_trades.append(trade)
            print(i, symbol, trade['datetime'], trade['side'], trade['type'], trade['takerOrMaker'], trade['price'],
                  trade['amount'],
                  trade['cost'])
    print('data)')
    df = pd.DataFrame(all_trades).drop(columns=['info'])
    df.to_csv(f'resources/binance_{start_date}.csv', index=False)


def calc_trade_pct():
    start_date = '2022-05-25'
    df = pd.read_csv(f'resources/binance_{start_date}.csv')  # 27
    buys = df[df['side'] == 'buy']
    sells = df[df['side'] == 'sell']
    # [symbol, sell_buy_price, profit,  sell_price, buy_price, sell_cost, buy_cost, sell_type, sell_dt, buy_dt])
    sells = sells.groupby(['order', 'timestamp', 'datetime', 'symbol', 'type', 'price']).agg(
        {'cost': 'sum', 'amount': 'sum'}).reset_index()
    res = []
    # columns = ['symbol', 'profit', 'pct', 'sell_p', 'buy_p', 'sell_ts', 'buy_ts']
    columns = ['symbol', 'sell_buy_price', 'profit',
                          'sell_p', 'buy_p', 'sell_cost', 'buy_cost', 'sell_type', 'sell_ts', 'buy_ts', ]
    for i, sell in sells.sort_values('timestamp', ascending=False).iterrows():
        symbol = sell['symbol']
        buy_df = buys[(buys['symbol'] == symbol) & (buys['timestamp'] < sell['timestamp'])].sort_values('timestamp',
                                                                                                        ascending=False)
        if not len(buy_df):
            print(f'Buy for {symbol} not found')
            continue
        l_buy = buy_df.iloc[0]
        buy_price = l_buy['price']
        buy_cost = l_buy['cost']
        buy_dt = l_buy['datetime']
        sell_price = sell['price']
        sell_cost = sell['cost']
        sell_dt = sell['datetime']
        sell_type = sell['type']
        profit = sell_cost - buy_cost

        sell_buy_price = (sell_price / buy_price) - 1
        profit = sell_cost - buy_cost
        res.append([symbol, sell_buy_price, profit,  sell_price, buy_price, sell_cost, buy_cost, sell_type, sell_dt, buy_dt])
        # res.append([symbol, profit, pct, sell_price, buy_price, sell_dt, buy_dt])
    df_trades = pd.DataFrame(res, columns=columns)
    # print(df_trades)
    # filter
    # start_date_trade = '2022-05-25T00:00:00Z'
    # df_trades = df_trades[pd.to_datetime(df_trades['buy_ts']) > pd.to_datetime(start_date_trade, utc=True)]

    # print(df_trades)
    df_trades.to_csv(f'resources/trades_from_{start_date}.csv')
    # df_trades.sort_values('profit')
    print('TOTAL SELL/BUY %:', df_trades['sell_buy_price'].sum())


def calc_trade_profit():
    # TODO: not accurate as amount bought and sold can be quite differnet if a coin has been bought multiple twice, but sold once.
    start_date = '2022-05-25'
    df = pd.read_csv(f'all_trades/binance_{start_date}.csv')  # 27
    buys = df[df['side'] == 'buy']
    sells = df[df['side'] == 'sell']
    # buys['cost'].sum() - sells['cost'].sum()
    # trade can be split
    sells = sells.groupby(['timestamp', 'datetime', 'symbol', 'price']).agg(
        {'cost': 'sum', 'amount': 'sum'}).reset_index()
    res = []
    columns = ['symbol', 'profit', 'pct', 'sell_p', 'buy_p', 'sell_ts', 'buy_ts']
    print('-symbol-\tprofit\t--pct--\t--sell_p--\t--buy_p--\t---------sell----------\t---------buy----------')
    for i, sell in sells.sort_values('timestamp', ascending=False).iterrows():
        symbol = sell['symbol']
        buy_df = buys[(buys['symbol'] == symbol) & (buys['timestamp'] < sell['timestamp'])].sort_values('timestamp',
                                                                                                        ascending=False)
        if not len(buy_df):
            print(f'Buy for {symbol} not found')
            continue
        l_buy = buy_df.iloc[0]
        if sell['amount'] != l_buy['amount']:
            print('sell does not have a proper buy trade, skipping...')
            continue
        buy_price = l_buy['price']
        buy_cost = l_buy['cost']
        buy_dt = l_buy['datetime']
        sell_price = sell['price']
        sell_cost = sell['cost']
        sell_dt = sell['datetime']

        profit = sell_cost - buy_cost
        if profit < -5:
            print('WHAT!')
        pct = (sell_cost / buy_cost) - 1
        print(f'{symbol}\t{profit:0.2f}\t{pct:0.2%}\t{sell_price}\t{buy_price}\t{sell_dt}\t{buy_dt}')
        res.append([symbol, profit, pct, sell_price, buy_price, sell_dt, buy_dt])
    df_trades = pd.DataFrame(res, columns=columns)
    print(df_trades)
    # filter
    start_date_trade = '2022-05-26T00:00:00Z'
    df_trades = df_trades[pd.to_datetime(df_trades['buy_ts']) > pd.to_datetime(start_date_trade, utc=True)]
    print(df_trades)
    df_trades.sort_values('profit')
    print('TOTAL PROFIT:', df_trades['profit'].sum())


if __name__ == '__main__':
    # things to do
    # 1. add option to check only on one coin
    # 2. Save trades from exchange into a db or csv (tricky because this is needed to do it every day.

    # get_from_exchange()
    calc_trade_pct()
    # calc_trade_profit()




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
