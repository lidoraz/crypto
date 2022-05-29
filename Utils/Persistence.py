import pandas as pd
import sqlite3


# TODO MOVE THIS TO Crypto / Nasdaq Directory.

def cols_str(cols):
    return ', '.join([f'{p[0]} {p[1]}' for p in cols])


def row_values_to_str(row: pd.Series):
    return ', '.join([str(v) for v in row.values])


# cols = [('ts', 'text'),
#         ('open', 'real'),
#         ('high', 'real'),
#         ('low', 'real'),
#         ('close', 'real'),
#         ('volume', 'real'),
#         # ('dividends', 'real'),
#         # ('splits', 'real'),
#         ]
# TODO SQL LITE CONVERT
#   select datetime(ts, 'unixepoch', 'localtime') from BTC_USDT_1M where ts  > 1651352820;
#   select datetime(ts, 'unixepoch', 'localtime') as dt from BINANCE_APE_USDT_1M  order by dt desc limit 10
#   with ts_delta as(
#   select (ts- lag(ts) over (partition by null order by ts) ) as ts_diff  from KUCOIN_RMRK_USDT_1M)
#   select DISTINCT ts_diff from ts_delta where ts_diff is not null;

cols = [('ts', 'number'),
        ('open', 'real'),
        ('high', 'real'),
        ('low', 'real'),
        ('close', 'real'),
        ('volume', 'real'),
        # ('dividends', 'real'),
        # ('splits', 'real'),
        ]


def _treat_name(symbol, tf):
    # https://stackoverflow.com/questions/3411771/best-way-to-replace-multiple-characters-in-a-string
    symbol = symbol.replace('-', '_').replace('/', '_').replace('.', '_').strip().upper()
    tf = tf.strip().upper()
    return f'{symbol}_{tf}'


def split_db_name_to_table_tf(x):
    last_underscore_idx = len(x) - x[::-1].index('_') - 1
    table_name_only = x[:last_underscore_idx]
    tf = x[last_underscore_idx + 1:]
    return table_name_only, tf


# TODO add get tables for sanity check.

class Persistence:

    def __init__(self, db_path, check_same_thread=True):
        self.db_path = db_path
        self.con = sqlite3.connect(db_path, check_same_thread=check_same_thread)
        self.INDEX = 'ts'
        self.tables_current_idx = {}
        self._preload_current_ts()

    def _preload_current_ts(self):
        tables = self.get_all_tables()
        for x in tables:
            table_name_only, tf = split_db_name_to_table_tf(x)
            latest_ts = self.get_latest_ts(table_name_only, tf)
            self.tables_current_idx[x] = latest_ts

    def create(self, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        cur = self.con.cursor()
        # Create table
        print('Creating table if not exists:', tbl_name)
        cur.execute(f"CREATE TABLE if not exists {tbl_name} ({cols_str(cols)},PRIMARY KEY ({cols[0][0]}))")
        self.con.commit()
        self.tables_current_idx[tbl_name] = 0

    def create_multiple_tables(self, exchanges_symbols, tf):
        n_tables_before = self.get_all_tables()
        # save_symbol = f'{exchange_name}_{symbol}'
        [self.create(f'{exchance}_{symbol}', tf) for exchance, symbol in exchanges_symbols]
        n_tables_after = self.get_all_tables()
        added = [x for x in n_tables_after if x not in n_tables_before]
        if len(added):
            print(f'Created {len(added)} tables:')
            [print(x) for x in added]

    def get_all_tables(self):
        q = 'SELECT name from sqlite_master where type= "table"'
        tables = pd.read_sql_query(q, con=self.con)['name'].tolist()
        return tables

    def _add_verified(self, df, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        cur = self.con.cursor()

        # df.to_sql(str, con=self.con, index=False, if_exists='replace')
        for idx, row in df.iterrows():
            values_to_insert = f"{idx}, {row_values_to_str(row)}"
            cur.execute(f"INSERT OR IGNORE INTO {tbl_name} VALUES ({values_to_insert})")
        self.con.commit()
        self.tables_current_idx[tbl_name] = df.index[-1]
        return len(df)

    def add(self, df, symbol, tf):
        if df.index.name != 'ts':
            raise ValueError("index name must be set to 'tf'")
        # df = self._align_df(df, symbol, tf)
        return self._add_verified(df, symbol, tf)

    def add_single_no_verify(self, line, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        cur = self.con.cursor()
        idx = line[0]
        row = line[1:]
        row = ', '.join([str(v) for v in row])
        values_to_insert = f"'{idx}', {row}"
        cur.execute(f"INSERT INTO {tbl_name} VALUES ({values_to_insert})")
        self.con.commit()

    # select datetime(ts, 'unixepoch', 'localtime') from BINANCE_APE_USDT_1M where ts  > 1651352820 order by ts  desc
    def get_df(self, symbol, tf, start_ts=None, start_date=None, to_datetime=True):
        tbl_name = _treat_name(symbol, tf)
        if not self.is_exists(tbl_name):
            raise ValueError(f'Table {tbl_name} not exists')
        if start_ts and start_date:
            raise ValueError('Only one start can be set')
        if start_ts:
            query = f"SELECT * from {tbl_name} WHERE ts >= '{start_ts}' order by ts"
        elif start_date:
            query = f"select * from {tbl_name} WHERE date(ts, 'unixepoch') >= date('{start_date}') order by ts"
        else:
            query = f"SELECT * from {tbl_name} order by ts"
        df = pd.read_sql_query(query, self.con, index_col='ts')
        if len(df) == 0:
            return None
        df.attrs['curr_ts_db'] = df.index[-1]
        if to_datetime:
            df.index = pd.to_datetime(df.index, unit='s', utc=True)
        return df

    def get_latest_ts(self, symbol=None, tf=None):
        tbl_name = _treat_name(symbol, tf)
        if tbl_name not in self.tables_current_idx:
            return -1
        query = f"SELECT * from {tbl_name} order by ts desc limit 1"
        df = pd.read_sql_query(query, self.con, index_col=self.INDEX)
        if len(df):
            return df.index[0]
        return 0

    @staticmethod
    def get_utcnow_ts():
        from datetime import datetime, timezone
        ts = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
        return ts

    def _align_df(self, df, symbol, tf):
        if self.is_empty(symbol, tf):
            return df
        latest_ts = self.get_latest_ts(symbol, tf)
        first_df_ts = df.sort_index().index[0]
        is_ok = latest_ts < first_df_ts
        if not is_ok:
            new_df = df[df.index > latest_ts]
            dropped_rows = len(df) - len(new_df)
            # print(f'DF is not aligned: first_df_ts={first_df_ts}, latest_ts={latest_ts}, Dropped {dropped_rows} rows')
            return new_df
        else:
            return df

    def is_empty(self, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        df = pd.read_sql_query(f"SELECT * FROM {tbl_name}", self.con)
        return len(df) == 0

    def is_exists(self, tbl_name):
        q = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl_name}'"
        df = pd.read_sql_query(q, self.con)
        return len(df) != 0

    def close(self):
        self.con.close()

# class Persistence:
#
#     def __init__(self, db_path='example.db'):
#         self.db_path = db_path
#         self.con = sqlite3.connect(db_path)
#         self.INDEX = 'ts'
#
#     def create(self, symbol, tf):
#         tbl_name = _treat_name(symbol, tf)
#         cur = self.con.cursor()
#         # Create table
#         print(tbl_name)
#         cur.execute(f"CREATE TABLE if not exists {tbl_name} ({cols_str(cols)},PRIMARY KEY ({cols[0][0]}))")
#         self.con.commit()
#
#     def _add_verified(self, df, symbol, tf):
#         tbl_name = _treat_name(symbol, tf)
#         cur = self.con.cursor()
#         for idx, row in df.iterrows():
#             values_to_insert = f"'{idx}', {row_values_to_str(row)}"
#             cur.execute(f"INSERT INTO {tbl_name} VALUES ({values_to_insert})")
#         self.con.commit()
#
#     def add(self, df, symbol, tf):
#         df.index = pd.to_datetime(df.index)
#         df = self._align_df(df, symbol, tf)
#         self._add_verified(df, symbol, tf)
#
#     def add_single_no_verify(self, line, symbol, tf):
#         tbl_name = _treat_name(symbol, tf)
#         cur = self.con.cursor()
#         idx = line[0]
#         row = line[1:]
#         row = ', '.join([str(v) for v in row])
#         values_to_insert = f"'{idx}', {row}"
#         cur.execute(f"INSERT INTO {tbl_name} VALUES ({values_to_insert})")
#         self.con.commit()
#
#     def get_df(self, symbol, tf, start_ts=None):
#         tbl_name = _treat_name(symbol, tf)
#         if not self.is_exists(tbl_name):
#             return None
#         if start_ts:
#             query = f"SELECT * from {tbl_name} WHERE ts >= '{start_ts}' order by ts"
#         else:
#             query = f"SELECT * from {tbl_name} order by ts"
#         df = pd.read_sql_query(query, self.con)
#         if len(df) == 0:
#             return None
#         return df
#
#     def get_latest_ts(self, symbol, tf):
#         tbl_name = _treat_name(symbol, tf)
#         query = f"SELECT * from {tbl_name} order by ts desc limit 1"
#         df = pd.read_sql_query(query, self.con, index_col=self.INDEX)
#         df.index = pd.to_datetime(df.index)
#         return df.index[0]
#
#     def _align_df(self, df, symbol, tf):
#         if self.is_empty(symbol, tf):
#             return df
#         latest_ts = self.get_latest_ts(symbol, tf)
#         first_df_ts = df.sort_index().index[0]
#         is_ok = latest_ts < first_df_ts
#         if not is_ok:
#             new_df = df[df.index > latest_ts]
#             dropped_rows = len(df) - len(new_df)
#             # print(f'DF is not aligned: first_df_ts={first_df_ts}, latest_ts={latest_ts}, Dropped {dropped_rows} rows')
#             return new_df
#         else:
#             return df
#
#     def is_empty(self, symbol, tf):
#         tbl_name = _treat_name(symbol, tf)
#         df = pd.read_sql_query(f"SELECT * FROM {tbl_name}", self.con)
#         return len(df) == 0
#
#     def is_exists(self, tbl_name):
#         q = f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tbl_name}'"
#         df = pd.read_sql_query(q, self.con)
#         return len(df) != 0
#
#     def close(self):
#         self.con.close()
