# ONLINE DATA PROVIDER
import pandas as pd
from datetime import datetime

from yahoo_finance import get_from_yfinance

# Best solution- at start:
# on given interval get data from limit table above.
# use DB until last avialble record.
# use yf.download to get from record to time now ranges.
# on close push all new data to the sql.
# Also, There is an option to save daily data easily
symbols = ['FB', 'AAPL']
tf = '1min'
limitation_days = {'1min': 7, '5min': 60, '15min': 60, '1h': 730}
limit = limitation_days.get(tf.lower(), '1D') - 1
start_date = datetime.utcnow() - pd.to_timedelta(limit, unit='D')

df = get_from_yfinance('AAPL', start_date, tf=tf, tz='Israel')

print(len(df))

# SCHEDULE a call to API


# # TODO\;
# #   THINKABOUT HOW TO IMPLEMENT THIS, IF we work on differnet graunlarities, should we use only lowest and then upsample?
# #   There is a limit on how much we can pull from yfinanace and limit on computer resources.
#
#
#
# # TODO: WE can do an two level approach- for live view - use 1min data that will be stored regulary.
# # If persistance not updated, get updated data from yahoo and put in db.
# # Easier solution - pull every data from
#
# # Best solution- at start:
# # on given interval get data from limit table above.
# # use DB until last avialbable record.
# # use yf.download to get from record to time now ranges.
# # on close push all new data to the sql.
# # Also, There is an option to save daily data easily
