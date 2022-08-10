from plotly import graph_objects as go

from . import EMA
from .Indicator import Indicator, get_marker_color_candle


# TODO: Add some kind of SMA indicator for volume, to detect changes in volume, could trigger or used in an algorithm.

class Volume(Indicator):
    """
    calc returns "VolEMA7" -- smoothed version of volume
    """
    def __init__(self, vol_ema=7, plot_loc=None):
        super(Volume, self).__init__(f'VolEMA{vol_ema}', "SUB_PLOT")
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self._smoothed_name = None
        self.vol_ema = vol_ema
        self._smooth = EMA(self.vol_ema)

    def calc(self, ohlcv):
        smooth = self._smooth.calc(ohlcv['volume'])
        smooth.name = self.name
        self._smoothed_name = smooth.name
        return smooth

    def plot(self, df, fig, color='Orange'):
        ra = df['volume']
        vol_smooth = df[self.name]
        marker_color = get_marker_color_candle(df)
        trace = go.Bar(x=ra.index, y=ra, name='Volume', opacity=0.9,  # yaxis='y2',
                       marker_color=marker_color)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])

        trace = go.Scatter(x=vol_smooth.index, y=vol_smooth, name=self.name,
                           line_color='white', opacity=0.4)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
