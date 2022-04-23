from DataProcessing.data_utils import get_data_providers, adjust_plot_start_datetime, prepare_data
from DataProcessing.data_consts import COINS, START_DATA_DATE

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import plotly.graph_objects as go
from Indicators import CandleStick
import pandas as pd
import numpy as np


def generate_cupnhandle(cupnhandle_length=100, small_cup_ratio=0.25, small_cup_lowest=0.6):
    # generates a cup n handle pattern, ranges: [1,0]
    # 'small_cup_lowest' from big cup not linear,  increasing **2
    big_cup_length = int(cupnhandle_length * (1 - small_cup_ratio))
    small_cup_length = int(cupnhandle_length * small_cup_ratio)
    x1 = np.linspace(-1, 1, big_cup_length)
    big_cup = x1 ** 2
    x2_start = small_cup_lowest
    x2 = np.linspace(-x2_start, x2_start, small_cup_length)
    small_cup = x2 ** 2 + (1 - x2_start ** 2)  # 0.95
    cupnhandle = np.r_[big_cup, small_cup]
    if len(cupnhandle) < cupnhandle_length:  # fix if missing one
        cupnhandle = np.r_[cupnhandle, [cupnhandle[-1]]]
    return cupnhandle

# best used in daily nasdaq data
def detect_cupnhandle(coin, data: pd.Series, cupnhandle_treshold=0.05):
    # TODO: Add different cupnhandle tresholds to match coressponding window size.
    # TODO: w: 70, t: 0.017, w:150, t: 0.02, w:300, t:0.03 # maybe function like : 0.017 * ((150/70)/2)
    # https://school.stockcharts.com/doku.php?id=chart_analysis:chart_patterns:cup_with_handle_continuation
    # cup n handle usually works on month to a year.
    # worked well with window_size: 150, t=0.027, but cupnhandle is a longer term indicator
    # cupnhandle_treshold = 0.05  # 0.04  # 0.027 # 0.0175 for 50
    detected_parts = []
    # differnet types of handles
    cupnhandle_forms = [
        # dict(small_cup_ratio=0.2, small_cup_lowest=0.3), ## too narrow low
        # dict(small_cup_ratio=0.2, small_cup_lowest=0.2),
        dict(small_cup_ratio=0.25, small_cup_lowest=0.4),
        dict(small_cup_ratio=0.3, small_cup_lowest=0.5),
        dict(small_cup_ratio=0.4, small_cup_lowest=0.5),
        # dict(small_cup_ratio=0.3, small_cup_lowest=0.4), ## too narrow low
        dict(small_cup_ratio=0.25, small_cup_lowest=0.6)]

    ## daily data
    for windows_size in [70, 160, 300]:  # 7 weeks to a year   [150, 300]
        last_found = -1
        for rolling_window in data.rolling(windows_size):
            if len(rolling_window) < windows_size:  # ignore first rows that are not full sized
                continue
            # need to shift new window to other region so there wont be an overlap
            if 0 < last_found < windows_size:
                last_found += 1
                continue
            last_found = -1

            scaler = MinMaxScaler()
            rolling_window_s = scaler.fit_transform(rolling_window.values.reshape(-1, 1)).reshape(-1)
            for params in cupnhandle_forms:
                generic_cupnhandle = generate_cupnhandle(cupnhandle_length=windows_size, **params)
                error = mean_squared_error(generic_cupnhandle, rolling_window_s)
                if error < cupnhandle_treshold:
                    rescaled_cupnhandle = scaler.inverse_transform(generic_cupnhandle.reshape(-1, 1)).reshape(-1)
                    df_detect = pd.DataFrame({'signal': rolling_window, 'cupnhandle': rescaled_cupnhandle},
                                             index=rolling_window.index)
                    title = f'{coin}, starts: {rolling_window.index[0]}, ends:{rolling_window.index[-1]}' \
                            f'\n wlen:{windows_size}, {params}, e:{round(error, 4)}'
                    df_detect.attrs['title'] = title
                    detected_parts.append(df_detect)
                    print('found!', title)
                    last_found = 1
                    # plt.plot(rolling_window_s)
                    # plt.plot(generic_cupnhandle)
                    # plt.title(title)
                    # plt.show()
    return detected_parts


def plot_cupnhandle(df, part):
    from plotly.subplots import make_subplots
    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(go.Candlestick(x=df.index,
                                 open=df.open,
                                 high=df.high,
                                 low=df.low,
                                 close=df.close), row=1, col=1)
    # fig = go.Figure(data=[go.Candlestick(x=df.index,
    #                                      open=df.open,
    #                                      high=df.high,
    #                                      low=df.low,
    #                                      close=df.close)])
    # fig.add_trace(go.Scatter(x=df[col].index, y=df[col], name='org_close'))
    fig.add_trace(go.Scatter(x=part.index, y=part['cupnhandle'], name='cupnhandle', marker_color='Blue'), row=1, col=1)
    fig.add_trace(go.Scatter(x=part.index, y=part['signal'], name='related_signal', marker_color='Black'), row=1, col=1)

    fig.update_layout(title=part.attrs['title'], xaxis_rangeslider_visible=False)

    from Indicators import RSI
    rsi = RSI(14, plot_loc=2)
    rsi_v = rsi.calc(df)
    rsi.plot(fig, color='black')
    fig.show()
    # can plot volume as other form of verification of the pattern


def find_cupnhandle_and_show_on_data(coin, df, cupnhandle_treshold, col='close', show=True):
    detected_parts = detect_cupnhandle(coin, df[col], cupnhandle_treshold)
    if show and len(detected_parts) > 0:
        for part in detected_parts:
            plot_cupnhandle(df, part)
            # show them on graph
            # plt.plot(df[col], label='org')
            # plt.plot(part['cupnhandle'], label='cupnhandle')
            # plt.plot(part['signal'], label='related_signal')
            # plt.title(part.attrs['title'])
            # plt.legend()
            # plt.show()
    return detected_parts

if __name__ == '__main__':
    tf = '1H'
    print('Usually cupnhandle spans from 7 weeks to a year')
    print('tf =', tf)
    # filter_datetime = adjust_plot_start_datetime(tf)
    providers = get_data_providers()
    df_prices, df_agg = prepare_data(providers, START_DATA_DATE)

    # coin = 'ETH'
    col = 'close'
    print('finding cup n handles...')
    for coin in COINS:
        df = CandleStick(tf).calc(df_prices[coin])
        find_cupnhandle_and_show_on_data(coin, df, col='close', cupnhandle_treshold=0.03)
