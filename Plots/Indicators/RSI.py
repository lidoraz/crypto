from plotly import graph_objects as go
import pandas as pd
import numpy as np


class RSI:
    def __init__(self, lookahead):
        self.lookahead = lookahead
        self.ra = None

    @staticmethod
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

    def calc(self, prices) -> pd.DataFrame:
        self.ra = self._calc_rsi(prices, self.lookahead)
        self.ra.name = f"RSI_{self.lookahead}"
        return self.ra.to_frame()

    def plot(self, fig, loc=(0, 0), color='white'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'RSI({self.lookahead})', line_color=color, line_width=1)
        fig.add_trace(trace, row=loc[0], col=[1])
        fig.add_hline(y=70, row=loc[0], col=[1], line_width=1, line_color='green', line_dash="dash")
        fig.add_hline(y=30, row=loc[0], col=[1], line_width=1, line_color='red', line_dash="dash")
        return fig
