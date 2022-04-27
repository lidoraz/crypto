import pandas as pd
import sqlite3


def cols_str(cols):
    return ', '.join([f'{p[0]} {p[1]}' for p in cols])


def row_values_to_str(row: pd.Series):
    return ', '.join([str(v) for v in row.values])


cols = [('ts', 'text'),
        ('open', 'real'),
        ('high', 'real'),
        ('low', 'real'),
        ('close', 'real'),
        ('volume', 'real'),
        # ('dividends', 'real'),
        # ('splits', 'real'),
        ]


def _treat_name(symbol, tf):
    symbol = symbol.replace('-', '_').replace('.', '_').strip().upper()
    tf = tf.strip().upper()
    return f'{symbol}_{tf}'


class Persistence:

    def __init__(self, db_path='example.db'):
        self.db_path = db_path
        self.con = sqlite3.connect(db_path)
        self.INDEX = 'ts'

    def create(self, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        cur = self.con.cursor()
        # Create table
        cur.execute(f"CREATE TABLE if not exists {tbl_name} ({cols_str(cols)})")
        self.con.commit()

    def _add_verified(self, df, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        cur = self.con.cursor()
        for idx, row in df.iterrows():
            values_to_insert = f"'{idx}', {row_values_to_str(row)}"
            cur.execute(f"INSERT INTO {tbl_name} VALUES ({values_to_insert})")
        self.con.commit()

    def add(self, df, symbol, tf):
        df.index = pd.to_datetime(df.index)
        df = self._align_df(df, symbol, tf)
        self._add_verified(df, symbol, tf)

    def get_df(self, symbol, tf, start_ts=None):
        tbl_name = _treat_name(symbol, tf)
        if not self.is_exists(tbl_name):
            return None
        if start_ts:
            query = f"SELECT * from {tbl_name} WHERE ts >= '{start_ts}' order by ts"
        else:
            query = f"SELECT * from {tbl_name} order by ts"
        df = pd.read_sql_query(query, self.con)
        if len(df) == 0:
            return None
        return df

    def get_latest_ts(self, symbol, tf):
        tbl_name = _treat_name(symbol, tf)
        query = f"SELECT * from {tbl_name} order by ts desc limit 1"
        df = pd.read_sql_query(query, self.con, index_col=self.INDEX)
        df.index = pd.to_datetime(df.index)
        return df.index[0]

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
