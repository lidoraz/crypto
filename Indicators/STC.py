from plotly import graph_objects as go
import pandas as pd
import numpy as np

from .EMA import EMA
from .Indicator import Indicator


class STC(Indicator):
    """
    Schaff Trend Cycle (STC)
    Simple EMA as it seems
    """

    def __init__(self, lookahead, fast_len, slow_len, ratio=0.5, plot_loc=None, color='white'):
        self.name = "RSI"
        self.lookahead = lookahead
        self.fast_len = fast_len
        self.slow_len = slow_len
        self.ratio = ratio
        self.ra = None
        self.data = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color
        self._ind_fast = EMA(self.fast_len)
        self._ind_slow = EMA(self.slow_len)

    def calc(self, ohlc) -> pd.DataFrame:
        prices = ohlc['close']
        macd = self._ind_fast.calc(ohlc) - self._ind_slow.calc(ohlc)
        lo_macd = macd.rolling(self.lookahead).min()
        hi_macd = macd.rolling(self.lookahead).max() - lo_macd
        t_macd = np.where(lo_macd > 0, (macd - lo_macd) / hi_macd * 100, 0)
        ddd = np.where(t_macd != 0.0, 0, self.ratio * t_macd)
        lo_ddd = pd.Series(ddd).rolling(self.lookahead).min()
        hi_ddd = pd.Series(ddd).rolling(self.lookahead).max()
        dddddd = np.where(hi_ddd > 0, (ddd - lo_ddd) / hi_ddd * 100, 0)
        res = self.ratio * dddddd
        res = pd.Series(res, index=macd.index)
        # lo_macd.apply(lambda x: (macd - lo_macd) / hi_macd * 100 if x > 0 else 0)
        # ddd = t_macd if
        self.ra = res
        self.ra.name = f"STC_{self.lookahead}"
        # self.ra_sma = SMA(self.lookahead).calc(self.ra)
        self.data = pd.DataFrame({'value': res, 'signal_buy': res > res.shift(1)})
        return self.ra.to_frame()

    def plot(self, fig):
        ra = self.data['value']
        buy_signals = self.data[self.data['signal_buy']]['value']
        sell_signals = self.data[~self.data['signal_buy']]['value']
        trace_green = go.Scatter(x=buy_signals.index, y=buy_signals, name=f'STC({self.lookahead})', line_color='Green',
                                 line_width=1.2)
        trace_red = go.Scatter(x=sell_signals.index, y=sell_signals, name=f'STC({self.lookahead})', line_color='Red',
                               line_width=1.2)
        loc = dict(row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace_green, **loc)
        fig.add_trace(trace_red, **loc)
        return fig
