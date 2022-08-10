from plotly import graph_objects as go
import pandas as pd
import numpy as np

from .SMA import SMA
from .Indicator import Indicator


def calc_rsi(prices, n):
    if n >= len(prices):  # fail safe in case of an error
        n = len(prices) - 1

    # https://stackoverflow.com/questions/57006437/calculate-rsi-indicator-from-pandas-dataframe
    def rma(x, n, y0):
        a = (n - 1) / n
        ak = a ** np.arange(len(x) - 1, -1, -1)
        return np.r_[np.full(n, np.nan), y0, np.cumsum(ak * x) / ak / n + y0 * a ** np.arange(1, len(x) + 1)]

    df = prices.to_frame().copy()
    df['change'] = df[prices.name].diff()
    df['gain'] = df.change.mask(df.change < 0, 0.0)
    df['loss'] = -df.change.mask(df.change > 0, -0.0)
    df['avg_gain'] = rma(df.gain[n + 1:].to_numpy(), n, np.nansum(df.gain.to_numpy()[:n + 1]) / n)
    df['avg_loss'] = rma(df.loss[n + 1:].to_numpy(), n, np.nansum(df.loss.to_numpy()[:n + 1]) / n)
    df['rs'] = df.avg_gain / df.avg_loss
    df['rsi_n'] = 100 - (100 / (1 + df.rs))
    return df['rsi_n']


class RSI(Indicator):
    """
    RSI measures price change in relation to recent price highs and lows.
    RSI Gives More Reliable Trading Signals In Non-Trending Markets than MACD
    The 2014 study conducted by Business Perspective also suggests that the RSI Indicator
     is more reliable than the MACD Indicator, when used during the non-trending periods.

    """

    def __init__(self, lookback, plot_loc=None, color='white'):
        super(RSI, self).__init__(f"RSI{lookback}", "SUB_PLOT")
        self.lookback = lookback
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def calc(self, ohlc) -> pd.DataFrame:
        prices = ohlc['close']
        ra = calc_rsi(prices, self.lookback)
        ra.name = self.name
        return ra.to_frame()

    def plot(self, df, fig):
        ra = df[self.name]
        trace_rsi = go.Scatter(x=ra.index, y=ra, name=self.name, line_color=self.color, line_width=1.2)
        # trace_smi = go.Scatter(x=ra.index, y=self.ra_sma, name=f'RSI_SMA({self.lookahead})', line_color="yellow", line_width=0.8)
        loc = dict(row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace_rsi, **loc)
        # fig.add_trace(trace_smi, **loc)
        # fig.add_hline(y=80, **loc, line_width=0.8, opacity=0.0)
        # fig.add_hline(y=20, **loc, line_width=0.8, opacity=0.0)

        fig.add_hline(y=70, **loc, line_width=0.5, line_color='red')
        fig.add_hline(y=30, **loc, line_width=0.5, line_color='green')
        return fig
