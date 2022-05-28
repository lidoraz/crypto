from plotly import graph_objects as go

from . import EMA
from .Indicator import Indicator, get_marker_color_candle


# TODO: Add some kind of SMA indicator for volume, to detect changes in volume, could trigger or used in an algorithm.

class Volume(Indicator):
    def __init__(self, plot_loc=None):
        self.name = "VOLUME"
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.vol = None
        self.marker_color = None

        self.smooth = EMA(7)

    def calc(self, ohlcv):
        self.vol = ohlcv['volume']
        self.smooth_calc = self.smooth.calc(self.vol)
        self.marker_color = get_marker_color_candle(ohlcv)
        return self.vol

    def plot(self, fig, color='Orange'):
        ra = self.vol
        trace = go.Bar(x=ra.index, y=ra, name='Volume', opacity=0.9,  # yaxis='y2',
                       marker_color=self.marker_color)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])

        trace = go.Scatter(x=self.smooth_calc.index, y=self.smooth_calc, name="VolEMA", line_color='white', opacity=0.4)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
