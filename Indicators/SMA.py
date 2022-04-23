from plotly import graph_objects as go
from .Indicator import Indicator


class SMA(Indicator):
    def __init__(self, lookahead, plot_loc=None):
        self.lookahead = lookahead
        self.ra = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    def calc(self, ohlc):
        prices = ohlc['close']
        self.ra = prices.rolling(self.lookahead).mean()
        self.ra.name = f'SMA_{self.lookahead}'
        return self.ra

    def plot(self, fig, color='Orange'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'SMA({self.lookahead})', line_color=color, line_width=0.8)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
