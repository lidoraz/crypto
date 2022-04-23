from plotly import graph_objects as go
from .Indicator import Indicator


class CandleStick(Indicator):
    def __init__(self, interval, ohlc=None, plot_loc=None):
        self.interval = interval
        self.ra = None
        self.ohlc = ohlc
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    def calc(self, data):
        if not self.ohlc:
            self.ohlc = data.resample(self.interval, closed='right').ohlc()
        else:
            raise ValueError('CandleStick already initiated with data')
        return self.ohlc

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, fig):
        trace = go.Candlestick(x=self.ohlc.index,
                               open=self.ohlc.open,
                               high=self.ohlc.high,
                               low=self.ohlc.low,
                               close=self.ohlc.close,
                               name='Candle')
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
