from plotly import graph_objects as go

from . import EMA
from .Indicator import Indicator, get_marker_color_candle


# TODO: Add some kind of SMA indicator for volume, to detect changes in volume, could trigger or used in an algorithm.

class Volume(Indicator):
    """
    calc returns "volume_EMA7" -- smoothed version of volume
    """

    def __init__(self, plot_loc=None):
        self.name = "VOLUME"
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.vol = None
        self.marker_color = None
        self.smooth_factor = 7
        self._smooth = EMA(self.smooth_factor)

    def calc(self, ohlcv):
        self.vol = ohlcv['volume']
        self._smooth_calc = self._smooth.calc(self.vol)
        self._smooth_calc.name = f'volume_EMA{self.smooth_factor}'
        self.marker_color = get_marker_color_candle(ohlcv)
        return self._smooth_calc

    def plot(self, fig, color='Orange'):
        ra = self.vol
        trace = go.Bar(x=ra.index, y=ra, name='Volume', opacity=0.9,  # yaxis='y2',
                       marker_color=self.marker_color)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])

        trace = go.Scatter(x=self._smooth_calc.index, y=self._smooth_calc, name=f"VolEMA{self.smooth_factor}",
                           line_color='white', opacity=0.4)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
