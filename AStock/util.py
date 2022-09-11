import yfinance as yf
import time
from datetime import datetime, timedelta


def get_daily_data(symbols, days_before, group_by='column'):
    t0 = time.time()
    # start = int(t0) - 60 * 60 * 24 * days_before  # 1 day before
    # start = str(pd.to_datetime(start, unit='s', utc=True).date())
    curr_date = datetime.now().date()
    start = str(curr_date - timedelta(days_before))
    # print('Starting From:', start)
    data = yf.download(' '.join(symbols), start=start, end=None,
                       rounding=True,
                       group_by=group_by,  # default is on columns. ticker is easier to iterate
                       auto_adjust=False,  # false on default, what does it do?
                       show_errors=True,
                       interval='1d', threads=True, progress=False)
    print(f"start={start}, data: {str(data.index[-1])} took: {time.time() - t0:0.2f}")
    return data
