from plotly import graph_objects as go
import pandas as pd
from . import EMA
from . import SMA

from .Indicator import Indicator

import numpy as np


def wma(data, lk):
    weights = np.linspace(1, lk, lk)
    sum_weights = np.sum(weights)
    # res = (data.rolling(window=lk, center=True)
    #        .apply(lambda x: np.sum(weights * x) / sum_weights, raw=False))
    res = (data.rolling(window=lk)
           .apply(lambda x: np.sum(weights * x) / sum_weights))
    # i = 0
    # lk = 3
    # weights = np.linspace(1, lk, lk)
    # sum_weights = np.sum(weights)
    # print(weights)
    # data = pd.Series([1, 2, 3])
    # for w in data.rolling(3):
    #     print((6))
    #     x = pd.DataFrame({'r': w, 'v': w.apply(lambda x: np.sum(weights * x) / sum_weights), 'm': np.mean(w)})
    #     print(x)
    #     i += 1
    #     if i == 4:
    #         break
    return res


class TrendTrader(Indicator):
    """
    // This is plots the indicator developed by Andrew Abraham
    // in the Trading the Trend article of TASC September 1998
    // Trend Trader Strategy
    """

    def __init__(self, lookback=21, multiplier=3, plot_loc=None):
        super(TrendTrader, self).__init__(f"Trend({self.lookback},{self.multiplier})", "SUB_PLOT")
        self.lookback = lookback
        self.multiplier = multiplier
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self._marker_color = None
        self.ra = None

    def calc(self, ohlc) -> pd.DataFrame:
        # max(high-low, abs(high - close[1], abs(low -close[1]))
        atr_1 = np.maximum(ohlc.high - ohlc.low,
                           (ohlc.high - ohlc.close.shift(1)).abs(),
                           (ohlc.low - ohlc.close.shift(1)).abs())
        avg_tr = wma(atr_1, self.lookback)
        highest_c = ohlc['high'].rolling(self.lookback).max()
        lowest_c = ohlc['low'].rolling(self.lookback).min()
        hi_limit = highest_c.shift(1) - (avg_tr.shift(1) * self.multiplier)
        lo_limit = lowest_c.shift(1) + (avg_tr.shift(1) * self.multiplier)
        close = ohlc['close']
        ret = np.where((close > hi_limit) & (close > lo_limit), hi_limit,
                       np.where((close < lo_limit) & (close < hi_limit),
                                lo_limit, np.nan))
        # fills the nan values, with backward data, fills first value in series with close
        ret = pd.Series(ret, index=close.index).ffill().fillna(close)
        ret.name = 'TrendTrader'
        # All good, tested against TW.
        return ret

    def plot(self, df, fig):
        ra = go.Scatter(x=self.ra.index, y=self.ra,
                        line_color='#2196F3',
                        line_width=1, legendgroup=self.name, name=self.name)
        fig.add_trace(ra, row=self.plot_loc[0], col=self.plot_loc[1])
        # fig.add_hline(y=0, row=self.plot_loc[0], col=self.plot_loc[1], line_width=0.5, line_color='black')
        return fig
