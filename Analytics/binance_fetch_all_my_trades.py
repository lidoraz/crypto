import os
import pandas as pd
import ccxt
from Data.Crypto.symbols import exchange_symbol_pairs
from tqdm import tqdm
from time import time


def get_from_exchange(start_dt):
    exchange = ccxt.binance({
        'apiKey': os.environ.get('BINANCE_API'),
        'secret': os.environ.get('BINANCE_SECRET'),
        'enableRateLimit': True,
        # 'options': {
        #     'defaultType': 'spot', // spot, future, margin
        # },
    })
    start_time = exchange.parse8601(start_dt)
    symbols = sorted([c[1] for c in exchange_symbol_pairs])
    exchange.load_markets()

    all_trades = []
    for symbol in tqdm(symbols):
        trades = exchange.fetch_my_trades(symbol, start_time, None)
        trades_info = exchange.fetch_orders(symbol, start_time, None)
        if not len(trades):
            continue
        for i, trade in enumerate(trades):
            trade_info = pd.DataFrame(trades_info).set_index('id').loc[trade['order']]
            trade['type'] = trade_info['type']
            all_trades.append(trade)
            # print(i, symbol, trade['datetime'], trade['side'], trade['type'], trade['takerOrMaker'], trade['price'], trade['amount'], trade['cost'])
    if not len(all_trades):
        return None
    df = pd.DataFrame(all_trades).drop(columns=['info'])
    renames = dict(timestamp='ts', datetime='dt', order='order_id')
    df = df.rename(columns=renames)
    for c in df.columns:
        if df[c].dtype == 'object':
            df[c] = df[c].astype('str')
    return df


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
               'sell_p', 'buy_p', 'sell_cost', 'buy_cost', 'sell_type', 'sell_dt', 'buy_dt']
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
        if l_buy['amount'] < sell['amount']:
            print(f"{symbol} Need to concat more than one buy into one: {l_buy['amount']}, {sell['amount']}")
            combined_buy = buy_df.groupby('symbol').agg(dict(dt='first', price='mean', cost='sum', amount='sum')).reset_index()
            assert len(combined_buy) == 1
            l_buy = combined_buy.iloc[0]
            # need to filter buy to start from lastest sell prior to symbol sell['ts'] to sell['ts']
            print(f"{symbol} Combined {len(buy_df)} buy into one total: {l_buy['amount']}, {sell['amount']}")
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
            [symbol, sell_buy_price, profit, sell_price, buy_price, sell_cost, buy_cost, sell_type, sell_dt, buy_dt])
        # res.append([symbol, profit, pct, sell_price, buy_price, sell_dt, buy_dt])
    df_trades = pd.DataFrame(res, columns=columns)
    # remove the timezone from dt by slicing
    df_trades['sell_dt'] = pd.to_datetime(df_trades['sell_dt'].str.slice(0, -5), utc=False)
    df_trades['buy_dt'] = pd.to_datetime(df_trades['buy_dt'].str.slice(0, -5), utc=False)
    t1 = time()
    print('TOTAL SELL/BUY %:', df_trades['sell_buy_price'].sum(), f'time= {t1-t0:0.2f}sec')
    return df_trades


if __name__ == '__main__':
    # things to do
    # 1. add option to check only on one coin
    # 2. Save trades from exchange into a db or csv (tricky because this is needed to do it every day.

    get_from_exchange('2022-05-25')
    # calc_trade_pct()
    # calc_trade_profit()

