import pandas as pd
import sqlite3
import time

#  TODO: Add commission, sell trade id.

# {'ts': 1653058677, 'symbol': 'CRV/USDT', 'type': 'market', 'side': 'sell', 'price': 1.122, 'amount_req': 10.7,
#  'amount_filled': 10.7, 'valuation': 12.0911208, 'stopPrice': None, 'id': '807565252', 'status': 'closed',
#  'order_dt': '2022-05-20T14:57:57.914Z', 'exchange': 'BINANCE'}

# {'ts': 1653060133, 'symbol': 'CRV/USDT', 'type': 'market', 'side': 'sell', 'price': 1.099, 'amount_req': 10.9,
#  'amount_filled': 10.9, 'valuation': 11.99055, 'stopPrice': None, 'id': '807602592', 'status': 'closed',
#  'order_dt': '2022-05-20T15:22:13.408Z', 'exchange': 'BINANCE'}

test_order = {'ts': 1653061189, 'id': 28994335, 'symbol': 'CRV/USDT', 'type': 'LIMIT_MAKER', 'side': 'SELL',
              'price': 0.45, 'amount_req': 30.8, 'amount_filled': 0, 'valuation': 0, 'stopPrice': 0.0, 'status': 'NEW',
              'order_dt': None, 'exchange': 'BINANCE'}

cols_orders = [('ts', 'number'),
               ('id', 'number'),
               ('symbol', 'varchar'),
               ('type', 'varchar'),
               ('side', 'varchar'),
               ('price', 'number'),
               ('amount_req', 'number'),
               ('amount_filled', 'number'),
               ('valuation_req', 'number'),
               ('stopPrice', 'number'),
               ('status', 'varchar'),
               ('order_dt', 'varchar'),
               ('exchange', 'varchar')]


def treat_val_insert(val):
    if isinstance(val, str):
        return f"'{val}'"
    elif isinstance(val, (float, int)):
        return f"{val}"
    elif val is None:
        return f"Null"
    else:
        print('unssported', val)


# TODO: Rework this class, it needs to be aligned with the write to db function in RealtimeTrade
class PersistenceOrders:
    def __init__(self, db_path):
        self.con = sqlite3.connect(db_path)
        self._create_orders(cols_orders)

    def _create_orders(self, cols):
        create_table_history = f"""
        CREATE TABLE IF NOT EXISTS orders ({cols_str(cols)})
        """
        cur = self.con.cursor()
        cur.execute(create_table_history)
        self.con.commit()

    def add_order(self, res):
        res_vals = list(res.values())
        res_vals = [treat_val_insert(v) for v in res_vals]
        res_vals = ', '.join(res_vals)
        q_add = f"""
        INSERT INTO orders VALUES ({res_vals})
        """
        cur = self.con.cursor()
        cur.execute(q_add)
        self.con.commit()

    def fetch_all(self):
        df = pd.read_sql_query("SELECT * FROM orders order by ts desc", self.con)
        return df

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
    db = PersistenceOrders(db_path)
    db.add_order(test_order)

    print(db.fetch_all())
    db.close()
    import os

    # print('deleted db')
    # os.remove(db_path)
