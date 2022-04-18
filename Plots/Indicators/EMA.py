from plotly import graph_objects as go


class EMA:
    def __init__(self, lookahead):
        self.lookahead = lookahead
        self.ra = None

    def calc(self, prices, to_frame=False):
        # https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html
        self.ra = prices.ewm(span=self.lookahead).mean()  # closed to the right!!
        self.ra.name = f'EWM_{self.lookahead}'
        if to_frame:
            return self.ra.to_frame()
        else:
            return self.ra

    # TODO: change to 1: get_plot, and 2: add_to_fig
    def plot(self, fig, loc=(0, 0), color='Orange'):
        ra = self.ra
        trace = go.Scatter(x=ra.index, y=ra, name=f'EMA({self.lookahead})', line_color=color, line_width=1)
        fig.add_trace(trace, row=loc[0], col=[1])
        return fig
