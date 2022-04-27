from Persistence import Persistence
import yfinance as yf
import pandas as pd


# db_path='small.db'
# db = Persistence(db_path)


def use_schdule():
    import schedule
    def thing_you_wanna_do():
        pass

    schedule.every().hour.do(thing_you_wanna_do)
    while True:
        schedule.run_pending()


# limitations:
# granularity -> last days
# 1m -> 7 days
# 5m -> 60 days
# 15m -> 60 days
# 1h -> 730 days
# 1D -> No limit

def multi_download(tickers):
    # If persistance not updated, get updated data from yahoo and put in db.
    # Easier solution - pull every data from

    # Best solution- at start:
    # on given interval get data from limit table above.
    # use DB until last avialbable record.
    # use yf.download to get from record to time now ranges.
    # on close push all new data to the sql.

    pass


symbol = 'AAPL'  # 'BTC-USD'
# tf = '15min'
tf = '1D'
db = Persistence()
df = db.get_df(symbol, tf)
if df is not None:
    print(len(df))


def convert_to_yf_interval(tf):
    digit = ''.join([i for i in tf if i.isdigit()])
    granularity = ''.join([i for i in tf if not i.isdigit()]).lower()
    granularity = 'mo' if granularity == 'm' else granularity  # month
    granularity = 'm' if granularity == 'min' else granularity  # min
    return digit + granularity.lower()


# TODO Last value is not full on granular.
def get_from_yfinance_multi(tickers, start, tf, tz='Israel'):
    # Usage ticker=('FB', 'AAPL'), start=pd.to_datetime('2022-04-20T12:00:00'), tf='15min', tz='Israel'
    yf_tf = convert_to_yf_interval(tf)
    data = yf.download(tickers=','.join(tickers), start=start, interval=yf_tf)
    if len(data) == 0:
        return None
    data.index = data.index.tz_convert(tz)
    dfs = []
    for ticker in tickers:
        df_sym = data.loc[:, (slice(None), ticker)]
        cols = [c[0] for c in df_sym.columns]
        df_sym.columns = cols
        dfs.append(df_sym)
    return dfs


def get_from_yfinance(ticker, start, tf, tz='Israel'):
    # usage: ticker='BTC-USD', start=pd.to_datetime('2022-04-20T12:00:00'), tf='15min'
    yf_tf = convert_to_yf_interval(tf)
    data = yf.download(tickers=ticker, start=start, interval=yf_tf)
    data.index = data.index.tz_convert(tz)
    return data


symbols = ['FB', 'AAPL']
tf = '15min'
start = pd.to_datetime('2022-04-20T12:00:00')

# dfs = get_from_yfinance_multi(symbols, start, tf)
df = get_from_yfinance(symbols[0], start, tf)

# print(dfs)
print(df)
