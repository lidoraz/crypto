from abc import ABC, abstractmethod
import pandas as pd


class Indicator(ABC):
    def __init__(self, name, location):
        assert location in ('SUB_PLOT', 'MAIN_PLOT')
        self.name = name
        self.location = location

    @abstractmethod
    def calc(self, data: [pd.DataFrame, pd.Series]):
        pass

    @abstractmethod
    def plot(self, df, fig):
        pass

    def __repr__(self):
        return self.name


def get_marker_color_candle(coin_ohlc):
    marker_color = ['Green' if x > 0 else 'Red' for x in coin_ohlc['close'] > coin_ohlc['open']]
    return marker_color


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'B', 'T', 'P'][magnitude])  # does not work for low values ('μ', 'm',)


def human_format_time(time_sec):
    month = 60 * 60 * 24 * 30
    day = 60 * 60 * 24
    hour = 60 * 60
    minute = 60
    time_sec = round(time_sec)
    if time_sec > month:
        return '{}M'.format(time_sec // month)
    elif time_sec > day:
        return '{}D'.format(time_sec // day)
    elif time_sec > hour:
        return '{}H'.format(time_sec // hour)
    else:
        return '{}T'.format(time_sec // minute)
