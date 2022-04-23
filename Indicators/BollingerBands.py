from plotly import graph_objects as go
from .Indicator import Indicator
import pandas as pd


class BollingerBands(Indicator):
    def __init__(self, lookahead=25, std_m=2, visible=True):
        self.lookahead = lookahead
        self.std_m = std_m
        self.bb = None
        self.cols = None
        self.visible = visible

    def calc(self, prices) -> pd.DataFrame:
        rolling_func = prices.rolling(self.lookahead)
        sma = rolling_func.mean()
        top_BB = sma + rolling_func.std() * self.std_m
        bot_BB = sma - rolling_func.std() * self.std_m
        self.cols = [f'BBTOP_{self.lookahead}', f'SMA_{self.lookahead}', f'BBBOT_{self.lookahead}']
        self.bb = pd.DataFrame(dict(zip(self.cols, [top_BB, sma, bot_BB])))
        return self.bb

    def plot(self, fig, loc=(1, 1)):
        name = f'BB({self.lookahead})'
        bb = self.bb
        cols = self.cols
        plot_kwargs = dict(name=name, line_color='DarkViolet', line_width=0.5, legendgroup=name)
        if not self.visible:
            plot_kwargs['visible'] = 'legendonly'
        trace_mid = go.Scatter(x=bb[f'SMA_{self.lookahead}'].index, y=bb[cols[1]],  # name=f'SMA({self.lookahead})'
                               **plot_kwargs)
        trace_top = go.Scatter(x=bb[f'BBTOP_{self.lookahead}'].index, y=bb[f'BBTOP_{self.lookahead}'], fill=None,
                               mode='lines',
                               **plot_kwargs)
        trace_bot = go.Scatter(x=bb[f'BBBOT_{self.lookahead}'].index, y=bb[f'BBBOT_{self.lookahead}'],
                               fill='tonexty',
                               mode='lines',
                               fillcolor="rgba(148, 0, 211, 0.15)",
                               **plot_kwargs)
        fig.add_trace(trace_mid, row=loc[0], col=loc[1])
        fig.add_trace(trace_top, row=loc[0], col=loc[1])
        fig.add_trace(trace_bot, row=loc[0], col=loc[1])
        return fig
