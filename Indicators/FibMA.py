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
    def __init__(self, lookahead):
        self.lookahead = lookahead
        self.ra = None

    def calc(self, prices, to_frame=False):
        self.ra = prices.rolling(self.lookahead).apply(_fibma)
        self.ra.name = f'FibMA_{self.lookahead}'
        if to_frame:
            return self.ra.to_frame()
        else:
            return self.ra

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, fig, loc=(0, 0), color='Orange'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'FibMA({self.lookahead})', line_color=color, line_width=1)
        fig.add_trace(trace, row=loc[0], col=loc[1])
        return fig
