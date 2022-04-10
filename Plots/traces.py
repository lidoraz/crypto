from plotly import graph_objects as go
from .plot_utils import calc_rsi


# TODO: probably a good way to do this is by creating a class of metrics, then, each child will have calc and plot.
#  plot will create a trace, while calc will enable to use the calculated data.

def get_pct_change(coin, df_hourly):
    pct_hourly = df_hourly[f'{coin}_CHANGEPCTHOUR']
    pct_color = pct_hourly.apply(lambda x: 'Green' if x > 0 else 'Red')
    trace = go.Bar(x=df_hourly.index, y=pct_hourly, marker_color=pct_color)
    return trace


def get_candle_stick(df_coin):
    trace = go.Candlestick(x=df_coin.index,
                           open=df_coin.open,
                           high=df_coin.high,
                           low=df_coin.low,
                           close=df_coin.close,
                           name='Candle')
    return trace


def get_pct_change_c(prices, resample=False):
    if resample:
        prices = prices.resample('1H').ffill()
        s = resample
    else:
        s = ""
    close_pct = prices.pct_change() * 100
    close_pct_color = close_pct.apply(lambda x: 'Green' if x > 0 else 'Red')
    return go.Bar(x=close_pct.index, y=close_pct, marker_color=close_pct_color, name=f'PCTChange({s})')


def get_volume(volume):
    # VOLUMEHOURTO
    # VOLUMEHOUR
    return go.Bar(x=volume.index, y=volume, name='Volume')


def get_MAD(coin_ohlc, pts, col='close', color='purple'):
    ra = coin_ohlc[col].rolling(pts).mean()
    # visible='legendonly' - appears but grayed out
    return go.Scatter(x=ra.index, y=ra, name=f'MA({pts})', line_color=color, line_width=1)


def get_EMA(coin_ohlc, pts, col='close', color='orange'):
    ema = coin_ohlc[col].ewm(span=pts).mean()  # closed to the right!!
    #     ra = coin_ohlc['close'].resample(f'{days}D').mean()
    return go.Scatter(x=ema.index, y=ema, name=f'EMA({pts})', line_color=color)


def _fib_seq(length):
    fib_i = 0
    next_fib_i = 1
    fib_seq = []
    while fib_i < length:
        fib_seq.append(fib_i)
        tmp = fib_i
        fib_i = fib_i + next_fib_i
        next_fib_i = tmp
    if len(fib_seq) > 1:
        fib_seq.remove(1)
    return fib_seq


def FMA(data):
    fib_seq = _fib_seq(len(data))
    return data[::-1].iloc[fib_seq][::-1].mean()


def get_FibMAD(coin_ohlc, pts, col='close', color='cyan'):
    fma = coin_ohlc[col].rolling(pts).apply(FMA)
    return go.Scatter(x=fma.index, y=fma, name=f'FibMA({pts})', line_color=color)


def get_RSI_from_calucated(ra, pts, color='white'):
    return go.Scatter(x=ra.index, y=ra, name=f'RSI({pts})', line_color=color, line_width=1)


def get_RSI(df_coin, pts, col='close', color='white'):
    ra = calc_rsi(df_coin, pts, col=col)
    return go.Scatter(x=ra.index, y=ra, name=f'RSI({pts})', line_color=color, line_width=1)
