from plotly import graph_objects as go

from AdvancedAnalytics.PatternDetection.identify_candlestick import recognize_candles

# TODO: probably a good way to do this is by creating a class of metrics, then, each child will have calc and plot.
#  plot will create a trace, while calc will enable to use the calculated data.

# def get_pct_change(coin, df_hourly):
#     pct_hourly = df_hourly[f'{coin}_CHANGEPCTHOUR']
#     pct_color = pct_hourly.apply(lambda x: 'Green' if x > 0 else 'Red')
#     trace = go.Bar(x=df_hourly.index, y=pct_hourly, marker_color=pct_color)
#     return trace


def get_candle_stick(df_coin):
    trace = go.Candlestick(x=df_coin.index,
                           open=df_coin.open,
                           high=df_coin.high,
                           low=df_coin.low,
                           close=df_coin.close,
                           name='Candle')
    return trace


def calc_pct_change(prices, resample, closed='right'):
    prices = prices.resample(resample, closed=closed).last()
    print('calc_pct_change', resample)
    close_pct = prices.pct_change() * 100
    return close_pct


def get_pct_change_color(close_pct):
    close_pct_color = close_pct.apply(lambda x: 'Green' if x > 0 else 'Red')
    return close_pct_color


def get_fig_pct_change_c(prices, resample):
    close_pct = calc_pct_change(prices, resample)
    close_pct_color = get_pct_change_color(close_pct)
    return go.Bar(x=close_pct.index, y=close_pct, marker_color=close_pct_color, name=f'PCTChange({resample})')


def get_volume(volume, coin_ohlc):
    # drop na will fix spaces when granularity is lower than 15min
    coin_ohlc = coin_ohlc.join(volume).dropna()
    marker_color = get_marker_color_candle(coin_ohlc)
    return go.Bar(x=coin_ohlc.index, y=coin_ohlc[volume.name], name='Volume', opacity=0.9,
                  # yaxis='y2',
                  marker_color=marker_color)


def get_EMA(coin_ohlc, pts, col='close', color='orange'):
    ema = coin_ohlc[col].ewm(span=pts).mean()  # closed to the right!!
    #     ra = coin_ohlc['close'].resample(f'{days}D').mean()
    return go.Scatter(x=ema.index, y=ema, name=f'EMA({pts})', line_color=color)


def get_marker_color_candle(coin_ohlc):
    marker_color = ['Green' if x > 0 else 'Red' for x in coin_ohlc['close'] > coin_ohlc['open']]
    return marker_color


def get_pattern_fig(coin_ohlc, normalize_detected_patterns=True):
    print('get_pattern_fig:: normalize_detected_patterns:', normalize_detected_patterns)
    df_patterns = recognize_candles(coin_ohlc)
    df_patterns['plot_value'] = (104 - df_patterns['best_ranking']) * df_patterns['best_trend']
    if normalize_detected_patterns:
        df_patterns['plot_value_norm'] = df_patterns['plot_value'] * (1 / df_patterns['n_patterns'])

    #  match candle color to pattern color
    marker_color = get_marker_color_candle(coin_ohlc)
    # marker_color = ['Green' if x > 0 else 'Red' for x in df_patterns['plot_value']]
    text = df_patterns['best_pattern'] + '(' + df_patterns['n_patterns'].astype(str) + ')'
    trace = go.Bar(y=df_patterns['plot_value_norm'], x=df_patterns.index, text=text,
                   # f'PatternCertainty'
                   name=f'PTRN(STR)',  # textposition="outside",
                   marker_color=marker_color)
    return trace

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
    return data.iloc[fib_seq[::-1]].mean()


def get_FibMAD(coin_ohlc, pts, col='close', color='cyan'):
    fma = coin_ohlc[col].rolling(pts).apply(FMA)
    return go.Scatter(x=fma.index, y=fma, name=f'FibMA({pts})', line_color=color)
