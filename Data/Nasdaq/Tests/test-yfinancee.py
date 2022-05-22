import pandas as pd
from datetime import datetime

# limitations:
# granularity -> last days
# 1m -> 7 days
# 5m -> 60 days
# 15m -> 60 days
# 1h -> 730 days
# 1D -> No limit


symbols = ['FB', 'AAPL']
tf = '15min'

# TODO: This works, add this to a yahoo class data provider.
limitation_days = {'1min': 7, '5min': 60, '15min': 60, '1h': 730}
limit = limitation_days.get(tf, '1D') - 1
start_date = datetime.utcnow() - pd.to_timedelta(limit, unit='D')

from Nasdaq.yahoo_finance import get_from_yfinance

df = get_from_yfinance('AAPL', start_date, tf=tf, tz='Israel')
# print(dfs)
print(df)
