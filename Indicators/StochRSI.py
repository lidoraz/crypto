from plotly import graph_objects as go
import pandas as pd
import numpy as np
from .RSI import calc_rsi
from .Indicator import Indicator
from . import SMA


class StochRSI(Indicator):
    def __init__(self, lookback, smooth=5, plot_loc=None, color='white'):
        super(StochRSI, self).__init__(f"StochRSI({lookback})", "SUB_PLOT")
        self.lookback = lookback
        self.stoch_rsi = None
        self.smooth_stock_rsi = None
        self.sma_smooth = smooth
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def calc(self, ohlc) -> pd.DataFrame:
        prices = ohlc['close']
        rsi = calc_rsi(prices, self.lookback)

        self.stoch_rsi = (rsi - rsi.min()) / (rsi.max() - rsi.min())
        ra = SMA(lookback=self.sma_smooth).calc(self.stoch_rsi) * 100
        ra.name = self.name
        return ra.to_frame()

    def plot(self, df, fig):
        ra = df[self.name]
        trace = go.Scatter(x=ra.index, y=ra, name=f'{self.name},{self.sma_smooth})',
                           line_color=self.color, line_width=1.2)
        loc = dict(row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace, **loc)
        # fig.add_hline(y=80, **loc, line_width=0.8, opacity=0.0)
        # fig.add_hline(y=20, **loc, line_width=0.8, opacity=0.0)

        fig.add_hline(y=80, **loc, line_width=0.8, line_color='red')
        fig.add_hline(y=20, **loc, line_width=0.8, line_color='green')
        return fig
