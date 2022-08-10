from plotly import graph_objects as go
from .Indicator import Indicator
import pandas as pd


class SMA(Indicator):
    """
    Long SMA is used to detect long term trend (99)
    """

    def __init__(self, lookback, plot_loc=None, color='Orange'):
        super(SMA, self).__init__(f"SMA{lookback}", "MAIN_PLOT")
        self.lookback = lookback
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def calc(self, ohlc):
        if isinstance(ohlc, pd.DataFrame):
            prices = ohlc['close']
        else:
            prices = ohlc
        ra = prices.rolling(self.lookback).mean()
        ra.name = self.name
        return ra

    def plot(self, df, fig):
        ra = df[self.name]
        trace = go.Scatter(x=ra.index, y=ra, name=self.name, line_color=self.color, line_width=0.8)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
