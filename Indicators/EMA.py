import pandas as pd
from plotly import graph_objects as go
from .Indicator import Indicator


class EMA(Indicator):
    def __init__(self, lookahead, plot_loc=None, color='Brown'):
        self.name = "EMA"
        self.lookahead = lookahead
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.ra = None
        self.color = color

    def calc(self, ohlc, to_frame=False):
        if isinstance(ohlc, pd.DataFrame):
            prices = ohlc['close']
        else:
            prices = ohlc
        # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html
        self.ra = prices.ewm(span=self.lookahead).mean()  # closed to the right!!
        self.ra.name = f'EWM_{self.lookahead}'

        if to_frame:
            return self.ra.to_frame()
        else:
            return self.ra

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, fig):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'EMA({self.lookahead})', line_color=self.color, line_width=1)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
