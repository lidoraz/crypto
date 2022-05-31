import pandas as pd
import sqlite3
import os

from Analytics.binance_fetch_all_my_trades import get_from_exchange

# timestamp,datetime,symbol,id,order,type,side,takerOrMaker,price,amount,cost,fee,fees
# 1653498027455,2022-05-25T17:00:27.455Z,ACA/USDT,3962185,29994329,market,buy,taker,0.386,31.16,12.02776,"{'cost': 0.03116, 'currency': 'ACA'}","[{'currency': 'ACA', 'cost': 0.03116}]"
from Realtime.Trade.utils.persistence_trades_simple import PersistenceOrders, cols_str

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
    return None


def get_table():
    with sqlite3.connect(db_path) as con:
        sql = f"select * from {tbl_name} order by ts desc"
        raw_trades = pd.read_sql_query(sql, con)
        return raw_trades


def update_orders_table():
    start_dt = '2022-05-25T00:00:00'
    cols_str(columns)
    # db = PersistenceOrders(db_path, 'executed_orders')
    n_added = 0
    with sqlite3.connect(db_path) as con:
        create_table_ignore_exists(con)
        latest_ts = get_latest_record(con) + 1
        print('latest_ts: ', latest_ts)
        if latest_ts:
            start_dt = str(pd.to_datetime(latest_ts, unit='ms'))
        df = get_from_exchange(start_dt)
        if df is not None:
            n_added = len(df)
            print('n_new_records', len(df))
            df.to_sql(tbl_name, con, if_exists='append', index=False)
        else:
            print('no new records found')
    return n_added


if __name__ == '__main__':
    update_orders_table()