# from Persistence import Persistence
import yfinance as yf
import pandas as pd
from datetime import datetime


# db_path='small.db'
# db = Persistence(db_path)


def use_schdule():
    import schedule
    def thing_you_wanna_do():
        pass

    schedule.every().hour.do(thing_you_wanna_do)
    while True:
        schedule.run_pending()


def convert_to_yf_interval(tf):
    digit = ''.join([i for i in tf if i.isdigit()])
    granularity = ''.join([i for i in tf if not i.isdigit()]).lower()
    granularity = 'mo' if granularity == 'm' else granularity  # month
    granularity = 'm' if granularity == 'min' else granularity  # min
    return digit + granularity


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
        cols = [c[0].lower() for c in df_sym.columns]
        df_sym.columns = cols
        dfs.append(df_sym)
    return dfs


#     limitation_days = {'1min': 7, '5min': 60, '15min': 60, '1h': 730}
def get_from_yfinance_now(symbol, tf: str, tz='Israel'):
    tf = tf.lower()
    limitation_days = {'1min': 1, '5min': 2, '15min': 10, '1h': 30}
    limitation_days_daily = {'1d': 300, '7d': 1500, '30d': 3000, '365d': 10000}
    if tf in limitation_days:
        limit = limitation_days.get(tf) - 1
        limit = limit // 3  # too much prior data
    elif tf in limitation_days_daily:
        limit = limitation_days_daily.get(tf)
        tf = '1d'
    else:
        raise ValueError('tf not supported')
    start_date = (datetime.utcnow() - pd.to_timedelta(limit, unit='D')).date()
    import time
    t0 = time.time()
    print('fetching from yfinance')
    df = get_from_yfinance(symbol, start_date, tf, tz)
    t1 = time.time()
    print('Done in: ', int(t1 - t0), 'sec')

    return df


def get_from_yfinance(symbol, start, tf, tz='Israel'):
    # usage: ticker='BTC-USD', start=pd.to_datetime('2022-04-20T12:00:00'), tf='15min'
    yf_tf = convert_to_yf_interval(tf)
    print(f'getting from yfinance: {symbol, start, tf}')
    # data = yf.download(tickers=symbol, start=start, interval=yf_tf, progress=False,
    #                    prepost=True)
    ticker = yf.Ticker(symbol)
    company_name = ticker.info['longName']  # really slow as it fetches from # https://finance.yahoo.com/quote/{symbol}
    df = ticker.history(interval=yf_tf, start=start, end=None)
    df.columns = [c.lower() for c in df.columns]
    df.index = pd.to_datetime(df.index, utc=True).tz_convert(tz)

    df.attrs['interval'] = tf
    df.attrs['symbol'] = symbol
    df.attrs['company_name'] = company_name
    return df


# # Saved to CSV
# def get_y_finance_data():
#     from Nasdaq.symbols import nasdq_100
#     from Nasdaq.symbols import ta_125
#
#     ticker_lst = ta_125[:10]
#
#     tickers = yf.Tickers(','.join(ticker_lst))
#     # tickers = yf.Tickers('AAPL,MSFT,AMD,VIX')
#     for ticker_str in tqdm(tickers.symbols):
#         period = "10y"
#         ticker = tickers.tickers[ticker_str]
#         df_h = ticker.history(period=period)
#         df_h.to_csv(NASDAQ_PREPATH + f'{ticker_str}_{period}.csv')


if __name__ == '__main__':
    all_limitation_days = {'1min': 7, '5min': 60, '15min': 60, '1h': 730,
                           '1D': 90, '7D': 60, '30D': 1000, '365D': 3000}
    for tf in all_limitation_days.keys():
        df = get_from_yfinance_now('AAPL', tf=tf)
        print(tf, len(df))

    # get_y_finance_data()
