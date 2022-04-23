from plotly import graph_objects as go


def get_candlestick(df_coin):
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


def get_marker_color_candle(coin_ohlc):
    marker_color = ['Green' if x > 0 else 'Red' for x in coin_ohlc['close'] > coin_ohlc['open']]
    return marker_color

