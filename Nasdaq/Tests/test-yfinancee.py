import yfinance as yf

symbol = 'TWTR'
# yf.Ticker
# tickers = yf.Tickers(symbol)
# ticker = tickers.tickers[ticker_str]
ticker = yf.Ticker(symbol)
# tickers = yf.Tickers('AAPL,MSFT,AMD,VIX')
period = "10y"
# tested :53 min after trade starts: there is ohlcv
# ticker.history('1D')
# df_h = ticker.history(period=period)
# df_h.to_csv(NASDAQ_PREPATH + f'{ticker_str}_{period}.csv')
df = ticker.history('1D')

# https://algotrading101.com/learn/yfinance-guide/
# API CALL TO:
# 'https://query2.finance.yahoo.com/v8/finance/chart/TWTR'
import time

print(df.columns)
from datetime import datetime

while True:
    # TODO: implemenrt a class for yahoo data - batch download and recent download for all ticker!
    # Interval required 5 minutes
    # can download historical data at once, then download just recent every X time and combine.
    # data = yf.download(tickers='UBER,AaPL', period='5d', interval='1m')
    # Can use yfinance for data also for crypto coins. 5min agg are ok.
    data = yf.download(tickers='BTC-USDT', period='5d', interval='1m')
    # BTC-USDT
    df = ticker.history('1D')
    # vals = df.values[0].tolist()
    # print(datetime.now(), vals)
    time.sleep(60)
