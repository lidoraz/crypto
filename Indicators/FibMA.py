from plotly import graph_objects as go
from .Indicator import Indicator


def _fib_seq(length):
    fib_i = 0
    next_fib_i = 1
    fib_seq = []
    while fib_i < length:
        fib_seq.append(fib_i)
        tmp = fib_i
        fib_i = fib_i + next_fib_i
        next_fib_i = tmp
    if len(fib_seq) > 1:
        fib_seq.remove(1)
    return fib_seq


def _fibma(data):
    fib_seq = _fib_seq(len(data))
    return data.iloc[fib_seq[::-1]].mean()


class FibMA(Indicator):
    def __init__(self, lookback, plot_loc=None, color='Pink'):
        super(FibMA, self).__init__(f"FibMA{lookback}", "MAIN_PLOT")
        self.lookahead = lookback
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def calc(self, ohlc, to_frame=False):
        prices = ohlc['close']
        ra = prices.rolling(self.lookahead).apply(_fibma)
        ra.name = self.name
        if to_frame:
            return ra.to_frame()
        else:
            return ra

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, df, fig):
        ra = df[self.name]
        trace = go.Scatter(x=ra.index, y=ra, name=self.name, line_color=self.color, line_width=1)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
