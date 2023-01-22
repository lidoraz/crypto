import yfinance as yf
import time
from datetime import datetime, timedelta


def get_daily_data(symbols, days_before, group_by='column', progress=False):
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
                       interval='1d', threads=True, progress=progress)
    print(f"start={start}, data: {str(data.index[-1])} took: {time.time() - t0:0.2f}")
    return data


def plot_ohlc_daily(ohlc):
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(3, 1))
    ohlc.index = range(len(ohlc.index))
    up = ohlc[ohlc.close >= ohlc.open]
    down = ohlc[ohlc.close < ohlc.open]
    col1 = 'green'
    col2 = 'red'

    # Setting width of candlestick elements
    width = .3
    width2 = .03
    # width = .8
    # width2 = .08
    up_index = up.index
    # Plotting up prices of the stock
    plt.bar(up_index, up.close - up.open, width, bottom=up.open, color=col1, align='center')
    plt.bar(up_index, up.high - up.close, width2, bottom=up.close, color=col1, align='center')
    plt.bar(up_index, up.low - up.open, width2, bottom=up.open, color=col1, align='center')
    down_index = down.index
    # Plotting down prices of the stock
    plt.bar(down_index, down.close - down.open, width, bottom=down.open, color=col2, align='center')
    plt.bar(down_index, down.high - down.open, width2, bottom=down.open, color=col2, align='center')
    plt.bar(down_index, down.low - down.close, width2, bottom=down.close, color=col2, align='center')

    # rotating the x-axis tick labels at 30degree
    # towards right
    plt.xticks(rotation=30, ha='right')
    return fig