from plotly import graph_objects as go
import pandas as pd
import numpy as np
from . import EMA

# https://cdn.website-editor.net/25dd89c80efb48d88c2c233155dfc479/files/uploaded/The-Complete-Guide-to-Trading.pdf
from .Indicator import Indicator


class MACD(Indicator):
    """
    Momentum indicator, used to detect momentum
    MACD measures the relationship between two EMAs
    MACD = EMA(CLOSE, 12)-EMA(CLOSE, 26)
    SIGNAL = SMA(MACD, 9)
    """

    def __init__(self, lookahead_short=12, lookahead_long=26, lookahead_signal=9, normalize=True, plot_loc=None):
        self.name = "MACD"
        self.lookahead_short = lookahead_short
        self.lookahead_long = lookahead_long
        self.lookahead_signal = lookahead_signal
        # TODO: can normalize but does not work that good.
        # self.normalize = normalize
        # self.normalize_lk = 100
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        #
        self._ind_fast = EMA(lookahead_short)  # fast
        self._ind_slow = EMA(lookahead_long)  # slow
        self._ind_signal = EMA(lookahead_signal)  # smooth
        self.plot_c = dict(macd="#2962FF",
                           signal='#FF6D00',
                           grow_above='#26A69A',
                           fall_above='#B2DFDB',
                           grow_below='#FFCDD2',
                           fall_below='#FF5252')
        self._marker_color = None

    def calc(self, ohlc) -> pd.DataFrame:
        macd = self._ind_fast.calc(ohlc) - self._ind_slow.calc(ohlc)
        signal = self._ind_signal.calc(macd)
        hist = macd - signal
        self.name = f"MACD({self.lookahead_short},{self.lookahead_long},{self.lookahead_signal})"
        cols = ['MACD', 'MACD_SIGNAL', 'MACD_HIST']
        self.macd = pd.DataFrame(dict(zip(cols, [macd, signal, hist])))

        def paint_hist(x):
            return np.where(x >= 0, np.where(x > x.shift(1), self.plot_c['grow_above'], self.plot_c['fall_above']),  # green, light-green
                            np.where(x > x.shift(1), self.plot_c['grow_below'], self.plot_c['fall_below']))  # light-red, red

        self._marker_color = paint_hist(self.macd['MACD_HIST'])
        return self.macd

    def plot(self, fig):
        t_mcad = go.Scatter(x=self.macd['MACD'].index, y=self.macd['MACD'],
                            line_color=self.plot_c['macd'],
                            line_width=1, legendgroup=self.name, name="MACD")
        trace_sma = go.Scatter(x=self.macd['MACD_SIGNAL'].index, y=self.macd['MACD_SIGNAL'],
                               line_color=self.plot_c['signal'],
                               line_width=1, legendgroup=self.name, name="Signal")
        t_hist = go.Bar(x=self.macd['MACD_HIST'].index, y=self.macd['MACD_HIST'],
                        marker_color=self._marker_color, legendgroup=self.name, name=self.name)
        fig.add_trace(t_hist, row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(t_mcad, row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace_sma, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
