from plotly import graph_objects as go
import pandas as pd
import numpy as np

from .SMA import SMA
from .Indicator import Indicator


class MFI(Indicator):
    """
    Money Flow Index measures price change in relation to recent price highs and lows.
    # TODO: Not working at the moment, it uses same forumla as rsi, but does not get to low values....
    """

    def __init__(self, lookback=14, plot_loc=None, color='white'):
        super(MFI, self).__init__(f"MFI{lookback}", "SUB_PLOT")
        self.lookback = lookback
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def calc(self, ohlc) -> pd.DataFrame:
        hlc3 = (ohlc['high'] + ohlc['low'] + ohlc['close']) / 3
        money_flow = hlc3 * ohlc['volume']
        # money_flow = ohlc['close'] * ohlc['volume']
        money_flow.name = 'money_flow'
        from Indicators.RSI import calc_rsi

        ra = calc_rsi(money_flow, self.lookback)
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
