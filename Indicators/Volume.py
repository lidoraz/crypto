from plotly import graph_objects as go
from .Indicator import Indicator, get_marker_color_candle


class Volume(Indicator):
    def __init__(self, plot_loc=None):
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.vol = None
        self.marker_color = None

    def calc(self, ohlcv):
        self.vol = ohlcv['volume']
        self.marker_color = get_marker_color_candle(ohlcv)
        return self.vol

    def plot(self, fig, color='Orange'):
        ra = self.vol
        trace = go.Bar(x=ra.index, y=ra, name='Volume', opacity=0.9,  # yaxis='y2',
                       marker_color=self.marker_color)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
