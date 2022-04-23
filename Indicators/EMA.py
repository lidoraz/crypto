from plotly import graph_objects as go
from .Indicator import Indicator


class EMA(Indicator):
    def __init__(self, lookahead, plot_loc=None):
        self.lookahead = lookahead
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.ra = None

    def calc(self, olhc, to_frame=False):
        prices = olhc['close']
        # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html
        self.ra = prices.ewm(span=self.lookahead).mean()  # closed to the right!!
        self.ra.name = f'EWM_{self.lookahead}'
        if to_frame:
            return self.ra.to_frame()
        else:
            return self.ra

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, fig, color='Orange'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'EMA({self.lookahead})', line_color=color, line_width=1)
        fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
