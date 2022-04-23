from plotly import graph_objects as go
import pandas as pd
import numpy as np

from .Indicator import Indicator


def _calc_rsi(prices, n):
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
    def __init__(self, lookahead, plot_loc=None):
        self.lookahead = lookahead
        self.ra = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    def calc(self, olhc) -> pd.DataFrame:
        prices = olhc['close']
        self.ra = _calc_rsi(prices, self.lookahead)
        self.ra.name = f"RSI_{self.lookahead}"
        return self.ra.to_frame()

    def plot(self, fig, color='white'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'RSI({self.lookahead})', line_color=color, line_width=1.2)
        loc = dict(row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace, **loc)
        fig.add_hline(y=70, **loc, line_width=0.8, line_color='red')
        fig.add_hline(y=30, **loc, line_width=0.8, line_color='green')
        return fig
