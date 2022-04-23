from plotly import graph_objects as go
from .Indicator import Indicator
import pandas as pd


class BollingerBands(Indicator):
    def __init__(self, lookahead=25, std_m=2, plot_loc=None, visible=True):
        self.lookahead = lookahead
        self.std_m = std_m
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.visible = visible
        self.bb = None
        self.cols = None

    def calc(self, olhc) -> pd.DataFrame:
        prices = olhc['close']
        rolling_func = prices.rolling(self.lookahead)
        sma = rolling_func.mean()
        top_BB = sma + rolling_func.std() * self.std_m
        bot_BB = sma - rolling_func.std() * self.std_m
        self.cols = [f'BBTOP_{self.lookahead}', f'SMA_{self.lookahead}', f'BBBOT_{self.lookahead}']
        self.bb = pd.DataFrame(dict(zip(self.cols, [top_BB, sma, bot_BB])))
        return self.bb

    def plot(self, fig):
        name = f'BB({self.lookahead})'
        bb = self.bb
        cols = self.cols
        plot_kwargs = dict(line_color='DarkViolet', line_width=0.5, legendgroup=name)
        if not self.visible:
            plot_kwargs['visible'] = 'legendonly'

        trace_mid = go.Scatter(x=bb[f'SMA_{self.lookahead}'].index, y=bb[cols[1]],
                               name=f'BB-MID({self.lookahead})', **plot_kwargs)
        trace_top = go.Scatter(x=bb[f'BBTOP_{self.lookahead}'].index, y=bb[f'BBTOP_{self.lookahead}'],
                               name=f'BB-HIGH({self.lookahead})', mode='lines', fill=None, **plot_kwargs)
        trace_bot = go.Scatter(x=bb[f'BBBOT_{self.lookahead}'].index, y=bb[f'BBBOT_{self.lookahead}'],
                               name=f'BB-LOW({self.lookahead})', mode='lines', fill='tonexty', **plot_kwargs,
                               fillcolor="rgba(148, 0, 211, 0.15)")
        loc = dict(row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace_mid, **loc)
        fig.add_trace(trace_top, **loc)
        fig.add_trace(trace_bot, **loc)
        return fig
