import os
import pandas as pd
import ccxt
from Data.Crypto.symbols import exchange_symbol_pairs
from tqdm import tqdm
from time import time
import sqlite3


def get_from_exchange(start_ts, symbol=None):
    exchange = ccxt.binance({
        'apiKey': os.environ.get('BINANCE_API'),
        'secret': os.environ.get('BINANCE_SECRET'),
        'enableRateLimit': True,
        # 'options': {
        #     'defaultType': 'spot', // spot, future, margin
        # },
    })
    symbols = sorted([c[1] for c in exchange_symbol_pairs])
    if symbol:
        symbols = [symbol]
    exchange.load_markets()

    all_trades = []
    for symbol in tqdm(symbols):
        trades = exchange.fetch_my_trades(symbol, start_ts, None)
        if not len(trades):
            continue
        for i, trade in enumerate(trades):
            # get order type (market/stop_loss)
            trade_info = exchange.fetch_order(trade['order'], symbol)
            if len(trade_info):
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
    # print(df)
    return df



# timestamp,datetime,symbol,id,order,type,side,takerOrMaker,price,amount,cost,fee,fees
# 1653498027455,2022-05-25T17:00:27.455Z,ACA/USDT,3962185,29994329,market,buy,taker,0.386,31.16,12.02776,"{'cost': 0.03116, 'currency': 'ACA'}","[{'currency': 'ACA', 'cost': 0.03116}]"
from Realtime.Trade.utils.persistence_trades_simple import cols_str

columns = [('ts', 'number'),
           ('dt', 'varchar'),
           ('symbol', 'varchar'),
           ('id', 'number'),
           ('order_id', 'number'),
           ('type', 'varchar'),
           ('side', 'varchar'),
           ('takerOrMaker', 'varchar'),
           ('price', 'number'),
           ('amount', 'number'),
           ('cost', 'number'),
           ('fee', 'varchar'),
           ('fees', 'varchar'), ]
db_path = 'all_orders.db'
tbl_name = 'executed_orders'


def create_table_ignore_exists(con):
    create_table_history = f"""
            CREATE TABLE IF NOT EXISTS {tbl_name} ({cols_str(columns)})
            """
    cur = con.cursor()
    cur.execute(create_table_history)
    con.commit()
    # primary key: # cannot alter sqllite table after it has been created.
    # con.execute(f'ALTER TABLE {tbl_name} ADD PRIMARY KEY (symbol, id);')


def get_latest_record(con):
    res = pd.read_sql_query(f'select ts from {tbl_name} order by ts desc limit 1', con)
    if len(res):
        return res['ts'][0]
    return 1653480000000  # 2022-05-25T12:00:00


def get_table():
    with sqlite3.connect(db_path) as con:
        sql = f"select * from {tbl_name} order by ts desc"
        raw_trades = pd.read_sql_query(sql, con)
        return raw_trades


def update_orders_table():
    cols_str(columns)
    n_added = 0
    with sqlite3.connect(db_path) as con:
        create_table_ignore_exists(con)
        latest_ts = get_latest_record(con) + 1
        df = get_from_exchange(latest_ts)
        if df is not None:
            n_added = len(df)
            print('n_new_records', len(df))
            df.to_sql(tbl_name, con, if_exists='append', index=False)
        else:
            print('no new records found')
    return n_added


if __name__ == '__main__':
    # start_dt = str(pd.to_datetime(1654023631370, unit='ms', utc=False))
    # start_dt = '2022-05-31T00:00:00'
    ts = 1654023631370
    get_from_exchange(ts, symbol='APE/USDT')
    # update_orders_table()

