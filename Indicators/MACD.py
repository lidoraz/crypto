from plotly import graph_objects as go
import pandas as pd
import numpy as np
from . import EMA

# https://cdn.website-editor.net/25dd89c80efb48d88c2c233155dfc479/files/uploaded/The-Complete-Guide-to-Trading.pdf
from .Indicator import Indicator


def paint_hist(x, colors):
    return np.where(x >= 0, np.where(x > x.shift(1), colors['grow_above'], colors['fall_above']),
                    # green, light-green
                    np.where(x > x.shift(1), colors['grow_below'],
                             colors['fall_below']))  # light-red, red


class MACD(Indicator):
    """
    Momentum indicator, used to detect momentum
    MACD measures the relationship between two EMAs
    MACD = EMA(CLOSE, 12)-EMA(CLOSE, 26)
    SIGNAL = SMA(MACD, 9)
    """

    def __init__(self, lookback_short=12, lookback_long=26, lookback_signal=9, display_signal=True, plot_loc=None):
        super(MACD, self).__init__(f"MACD({lookback_short},{lookback_long},{lookback_signal})", "SUB_PLOT")
        self.lookback_short = lookback_short
        self.lookback_long = lookback_long
        self.lookback_signal = lookback_signal
        self.display_signal = display_signal
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self._ind_fast = EMA(lookback_short)  # fast
        self._ind_slow = EMA(lookback_long)  # slow
        self._ind_signal = EMA(lookback_signal)  # smooth
        self.plot_c = dict(macd="#2962FF",
                           signal='#FF6D00',
                           grow_above='#26A69A',
                           fall_above='#B2DFDB',
                           grow_below='#FFCDD2',
                           fall_below='#FF5252')

    def calc(self, ohlc) -> pd.DataFrame:
        macd = self._ind_fast.calc(ohlc) - self._ind_slow.calc(ohlc)
        signal = self._ind_signal.calc(macd)
        hist = macd - signal
        cols = ['MACD', 'MACD_SIGNAL', 'MACD_HIST']
        macd = pd.DataFrame(dict(zip(cols, [macd, signal, hist])))

        return macd

    def plot(self, df, fig):
        macd_hist = df['MACD_HIST']
        marker_color = paint_hist(macd_hist, self.plot_c)
        t_hist = go.Bar(x=macd_hist.index, y=macd_hist,
                        marker_color=marker_color, legendgroup=self.name, name=self.name)
        fig.add_trace(t_hist, row=self.plot_loc[0], col=self.plot_loc[1])
        if self.display_signal:
            macd = df['MACD']
            signal = df['MACD_SIGNAL']
            t_mcad = go.Scatter(x=macd.index, y=macd,
                                line_color=self.plot_c['macd'],
                                line_width=1, legendgroup=self.name, name="MACD")
            trace_sig = go.Scatter(x=signal.index, y=signal,
                                   line_color=self.plot_c['signal'],
                                   line_width=1, legendgroup=self.name, name="Signal")
            fig.add_trace(t_mcad, row=self.plot_loc[0], col=self.plot_loc[1])
            fig.add_trace(trace_sig, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
