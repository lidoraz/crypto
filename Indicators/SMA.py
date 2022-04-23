from plotly import graph_objects as go
from .Indicator import Indicator


class SMA(Indicator):
    def __init__(self, lookahead):
        self.lookahead = lookahead
        self.ra = None

    def calc(self, prices):
        self.ra = prices.rolling(self.lookahead).mean()
        self.ra.name = f'SMA_{self.lookahead}'
        return self.ra

    def plot(self, fig, loc=(0, 0), color='Orange'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'SMA({self.lookahead})', line_color=color, line_width=1)
        fig.add_trace(trace, row=loc[0], col=loc[1])
        return fig
