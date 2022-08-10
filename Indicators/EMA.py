import pandas as pd
from plotly import graph_objects as go
from .Indicator import Indicator


class EMA(Indicator):
    def __init__(self, lookback, plot_loc=None, color='Brown'):
        super(EMA, self).__init__(f"EMA{lookback}", "MAIN_PLOT")
        self.lookahead = lookback
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def calc(self, ohlc, to_frame=False):
        if isinstance(ohlc, pd.DataFrame):
            prices = ohlc['close']
        else:
            prices = ohlc
        # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html
        ra = prices.ewm(span=self.lookahead, adjust=False, min_periods=self.lookahead).mean()  # closed to the right!!
        ra.name = self.name
        if to_frame:
            return ra.to_frame()
        else:
            return ra

    def plot(self, df, fig):
        ra = df[self.name]
        trace = go.Scatter(x=ra.index, y=ra, name=self.name, line_color=self.color, line_width=1)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
