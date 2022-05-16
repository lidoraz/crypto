import pandas as pd
import sqlite3
import time

#  TODO: Add commission, sell trade id.
cols_history = [('trade_id', 'number'),
                ('buy_ts', 'number'),
                ('exchange', 'varchar'),
                ('symbol', 'varchar'),
                ('buy_price', 'real'),
                ('amount', 'real'),
                ('sell_ts', 'number'),
                ('sell_price', 'real'),
                ('profit', 'real'),
                ('profit_pct', 'real')]

cols_open_trades = [('trade_id', 'number'),
                    ('buy_ts', 'number'),
                    ('exchange', 'varchar'),
                    ('symbol', 'varchar'),
                    ('buy_price', 'real'),
                    ('amount', 'real')]


class PersistenceTrades:
    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path)
        self._create_table_history(cols_history)
        self._create_table_open_trades(cols_open_trades)

    def _create_table_history(self, cols):
        create_table_history = f"""
        CREATE TABLE IF NOT EXISTS trade_history ({cols_str(cols)}, PRIMARY KEY ({cols[0][0]}))
        """
        cur = self.con.cursor()
        cur.execute(create_table_history)
        self.con.commit()

    def _create_table_open_trades(self, cols):
        create_table_history = f"""
        CREATE TABLE IF NOT EXISTS open_trades ({cols_str(cols)}, PRIMARY KEY ({cols[0][0]}))
        """
        cur = self.con.cursor()
        cur.execute(create_table_history)
        self.con.commit()

    def get_open_trades(self):
        q = """
        SELECT * FROM open_trades order by buy_ts
        """
        df = pd.read_sql_query(q, self.con)
        return df

    def get_trade_history(self):
        q = """
                SELECT * FROM trade_history order by buy_ts
                """
        df = pd.read_sql_query(q, self.con)
        return df

    def get_open_trade_by_symbol(self, exchange, symbol):
        q = f"""SELECT * FROM open_trades WHERE exchange='{exchange}' and symbol='{symbol}'"""
        df = pd.read_sql_query(q, self.con)
        if len(df):
            if len(df) > 1:
                print(f'get_open_trade_by_symbol {exchange, symbol} has more than 1 records!')
            return df.iloc[0]
        return None

    def get_open_trade_by_trade_id(self, trade_id):
        q = f"""SELECT * FROM open_trades WHERE trade_id={trade_id}"""
        df = pd.read_sql_query(q, self.con)
        if len(df):
            if len(df) > 1:
                print(f'get_open_trade_by_symbol {trade_id}  has more than 1 records!')
            return df.iloc[0]
        return None

    def add_trade(self, trade_id, exchange, symbol, buy_price, amount):
        # symbol = symbol.replace('-', '_').replace('/', '_').replace('.', '_').strip().upper()
        buy_ts = int(time.time())
        q = f"""
        INSERT INTO open_trades VALUES ({trade_id}, {buy_ts}, '{exchange}', '{symbol}', {buy_price}, {amount})
        """
        con = self.con.cursor()
        con.execute(q)
        self.con.commit()

    def close_trade(self, trade_id, sell_price, amount_sold):
        record = self.get_open_trade_by_trade_id(trade_id)
        if record is None:
            raise ValueError('attempted to close a null record')
        record = record.to_dict()
        assert record['trade_id'] == trade_id
        if amount_sold != record['amount']:
            # TODO: Add basic replace for not allowed strings, like "'", "," and maybe more.
            # TODO: Really important bottom
            # TODO can alter trade amount so it will reduce the amount it sold
            # TODO: Next time it will buy the same amount but sell the whole amount.
            print(f'close_trade: Amount sold is not equal!!!!!!', trade_id)
            # Workaround for this is to record number sold, and sell whatever we own.
            # Another way is to use 3rd table that will be called assets, if we have asset, we can sell it.
        sell_ts = int(time.time())
        profit = (sell_price - record['buy_price']) * record['amount']
        profit_pct = (sell_price / record['buy_price']) - 1

        row_str = f"{record['trade_id']}, {record['buy_ts']}, '{record['exchange']}'," \
                  f"'{record['symbol']}', {record['buy_price']}, {record['amount']}," \
                  f"{sell_ts}, {sell_price}, {profit}, {profit_pct}"
        q_history = f"""INSERT INTO trade_history VALUES ({row_str})"""
        cur = self.con.cursor()
        cur.execute(q_history)
        # Delete open trade
        q_delete = f"""
        DELETE FROM open_trades WHERE trade_id = {trade_id}
        """
        cur.execute(q_delete)
        self.con.commit()

    def calc_profit(self):
        trades = self.get_trade_history()
        n_trades = len(trades)
        sum_profit = trades.profit.sum()
        print(f'calc_profit n_trades= {n_trades}, sum_profit= {sum_profit:.2f} USDT')
        return sum_profit

    def close(self):
        self.con.close()


def _treat_str(s):
    unallowed_chars = list("\"',")
    # s = s.replace('-', '_').replace('/', '_').replace('.', '_').strip().upper()
    for char in unallowed_chars:
        s = s.replace(char, '')
    return s


def cols_str(cols):
    return ', '.join([f'{p[0]} {p[1]}' for p in cols])


def row_values_to_str(row: pd.Series):
    return ', '.join([str(v) for v in row.values])


if __name__ == '__main__':
    # Unit test
    db_path = 'test_trades.db'
    db = PersistenceTrades(db_path)
    import numpy as np
    from Data.Crypto.symbols import exchance_symbol_pairs

    owned_pairs = set()
    print(db.get_open_trades())
    trade_usdt_value = 100
    for i in range(15):
        pair_idx = np.random.randint(0, len(exchance_symbol_pairs))
        if pair_idx in owned_pairs:
            print(pair_idx, 'owned')
            continue
        owned_pairs.add(pair_idx)
        trade_id = int(np.random.random() * 1e12)
        exchange, symbol = exchance_symbol_pairs[pair_idx]
        buy_price = np.random.random() * 1000

        amount = trade_usdt_value / buy_price
        db.add_trade(trade_id, exchange, symbol, buy_price, amount)

    df_open_trades = db.get_open_trades()
    print(df_open_trades)
    print(df_open_trades.sort_values('buy_ts').symbol)

    print('Selling...')
    for i in range(10):
        pair_idx = np.random.randint(0, len(exchance_symbol_pairs))
        exchange, symbol = exchance_symbol_pairs[pair_idx]
        record = db.get_open_trade_by_symbol(exchange, symbol)
        if pair_idx not in owned_pairs:
            if record is not None:
                raise ValueError('record exists will should not')
            print(pair_idx, 'not owned')
            continue
        if pair_idx in owned_pairs and record is None:
            raise ValueError('')
        owned_pairs.add(pair_idx)

        trade_id = record['trade_id']
        buy_price = record['buy_price']
        sell_price = np.random.random() * 1000
        amount = record['amount']
        db.close_trade(trade_id, sell_price, amount_sold=amount)
        owned_pairs.remove(pair_idx)
        print('sold asset:', symbol)
    print(db.get_open_trades())

    print('All History')
    db_trade_history = db.get_trade_history()
    print(db_trade_history)

    print('profit:', db_trade_history.profit.sum())
    print(db.calc_profit())

    db.close()
    import os

    print('deleted db')
    os.remove(db_path)
