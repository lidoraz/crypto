from abc import ABC, abstractmethod
import pandas as pd


class Indicator(ABC):

    @abstractmethod
    def calc(self, data: [pd.DataFrame, pd.Series]):
        pass

    @abstractmethod
    def plot(self, **kwargs):
        pass


def get_marker_color_candle(coin_ohlc):
    marker_color = ['Green' if x > 0 else 'Red' for x in coin_ohlc['close'] > coin_ohlc['open']]
    return marker_color
