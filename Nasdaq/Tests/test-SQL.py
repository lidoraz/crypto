import sqlite3
import pandas as pd
import os

# TODO Implement this into file.
from Nasdaq.Tests.Persistence import Persistence


def fill_db():
    import os
    from tqdm import tqdm
    persist = Persistence()

    pre = '../yahoo_data/'
    for f in tqdm(os.listdir(pre)):
        t = f.split('.')[0].split('_')
        symbol = t[0]
        tf = '1D'
        path = os.path.join(pre, f)
        persist.create(symbol, tf)
        df_to_add = pd.read_csv(path, index_col='Date')
        persist.add(df_to_add, symbol, tf)
    persist.close()


if __name__ == '__main__':
    # fill_db()
    persist = Persistence()

    symbol = 'AAPL'
    tf = '1D'

    df = persist.get_df(symbol, tf, start_ts='2022-01-01')
    print(len(df))

    ts = persist.get_latest_ts(symbol, tf)
    print(ts)
    persist.close()
