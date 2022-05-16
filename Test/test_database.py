from Utils import Persistence
import pandas as pd
import numpy as np
import os
import time

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)


def test_db_latest_record(db, allowed_sec=300):
    tables = db.get_all_tables()
    sql = """
    SELECT ts from {table} order by ts desc limit 1
    """
    ts_machine = int(time.time())
    for t in tables:
        df = pd.read_sql_query(sql.format(table=t), db.con)
        if df is None or len(df) == 0:
            print('Table not exists or empty!')
        else:
            db_ts = df.iloc[0][0]
            db_dt = pd.to_datetime(db_ts, utc=True, unit='s').tz_convert('Israel')
            if ts_machine > allowed_sec + db_ts:
                hours = round((ts_machine - db_ts) / 3600, 2)
                print(f"{t}, {db_dt}, Over {allowed_sec} sec, {hours}H")


def test_db_ts_diff(db, start_date):
    tables = db.get_all_tables()
    sql = """
    with ts_delta as(
       select ts , (ts- lag(ts) over (partition by null order by ts) ) as ts_diff  from {table}
       where date(ts, 'unixepoch') >= date('{start_date}'))
       select datetime(ts, 'unixepoch', 'localtime'), ts, ts_diff from ts_delta where ts_diff is not null and ts_diff > 60;
    """
    percentiles = [50, 75, 90, 99]
    print(percentiles)
    print(start_date)
    for t in tables:
        run_sql = sql.format(table=t, start_date=start_date)
        df = pd.read_sql_query(run_sql, db.con)
        if len(df) > 1:
            print(t, len(df), df.ts_diff.mean(), np.percentile(df.ts_diff, percentiles).astype(int))


if __name__ == '__main__':
    db = Persistence('ccxt_1m.db')

    # KUCOIN_RMRK_USDT_1M
    start_date = '2022-05-01'
    # test_db_ts_diff(db, start_date)
    test_db_latest_record(db)
