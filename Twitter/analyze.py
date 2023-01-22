from Twitter.connector import connect_ppg2
from Twitter.utils import print_from_db, get_latest_from_db, get_lastest_from_db_postgres
import pandas as pd

from Utils.utils import WaitToMinEveryHour


def analyize_query(min_back, free_text_filter=None):
    conn = connect_ppg2()
    df = get_lastest_from_db_postgres(conn, min_back, free_text_filter)
    # df = df.query(query)
    print_from_db(df)
    return df
    # # users = ['marketrebels', 'benzinga', 'epsguid']
    # users = ['unusual_whales']
    # df = df[df.name.isin(users)]
    # # tickers = ['NVDA', 'MSFT']
    # # tickers = ['Pelosi', 'pelosi']
    # tickers = ['COIN']
    # df = df[df.text.str.contains('|'.join(tickers))]


def analyize_postgres(users=None, min_back=240):
    with connect_ppg2() as conn:
        df = get_lastest_from_db_postgres(conn, min_back)
        if users:
            df = df[df.name.isin(users)]
        print_from_db(df)


# def search_in_text(find):
# df = df.sort_index(ascending=False)
# db = TweetDB()
# SELECT * FROM TWEETS
# df = pd.read_sql(f"Select *  from tweets where text LIKE '%{find}%' order by ts", db.con)
# print_from_db(df)


def get_by_symbol(symbol, days_back=3):
    min_back = 60 * 24 * days_back
    q = f"and text LIKE '%{symbol.upper()}%'"
    analyize_query(min_back, q)


def get_by_free_text(txt, days_back=3):
    min_back = 60 * 24 * days_back
    q = f"and text LIKE '%{txt}%'"
    analyize_query(min_back, q)


def get_all_last_12h():
    min_back = 60 * 12
    analyize_query(min_back)


if __name__ == '__main__':
    # search_in_text("COIN")
    users = ['unusual_whales', 'cnbc']
    # get_all_last_12h()
    print('-' * 60)
    symbol = 'GILD'
    symbol = 'AMD'
    # txt = 'Top Ticker flow'   # Get unusual_whales
    # txt =
    symbol = 'BTC'
    # symbol = '🚨'
    get_by_symbol(symbol, days_back=5)
    # get_by_free_text(txt, days_back=60)
