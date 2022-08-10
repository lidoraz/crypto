from plotly import graph_objects as go
from .Indicator import Indicator


class CandleStick(Indicator):
    def __init__(self, interval, ohlc=None, plot_loc=None):
        super(CandleStick, self).__init__("CS", "MAIN_PLOT")
        self.interval = interval
        self.ohlc = ohlc
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    def calc(self, data):
        if not self.ohlc:
            ohlc = data.resample(self.interval, closed='right').ohlc()
            ohlc.attrs['interval'] = self.interval
        else:
            raise ValueError('CandleStick already initiated with data')
        return ohlc

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, df, fig):

        trace = go.Candlestick(x=df.index,
                               open=df.open,
                               high=df.high,
                               low=df.low,
                               close=df.close,
                               name='Candle')
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
