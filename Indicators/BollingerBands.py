from plotly import graph_objects as go
from .Indicator import Indicator
import pandas as pd


class BollingerBands(Indicator):
    def __init__(self, lookback=20, std_m=2, plot_loc=None, visible=True):
        super(BollingerBands, self).__init__(f"BB{lookback}", "MAIN_PLOT")
        self.lookback = lookback
        self.std_m = std_m
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.visible = visible
        self.bb = None
        self.cols = None

    def calc(self, ohlc) -> pd.DataFrame:
        prices = ohlc['close']
        rolling_func = prices.rolling(self.lookback)
        sma = rolling_func.mean()
        top_BB = sma + rolling_func.std() * self.std_m
        bot_BB = sma - rolling_func.std() * self.std_m
        self.cols = [f'BBTOP_{self.lookback}', f'SMA_{self.lookback}', f'BBBOT_{self.lookback}']
        bb = pd.DataFrame(dict(zip(self.cols, [top_BB, sma, bot_BB])))
        return bb

    def plot(self, df, fig):
        upper = self.cols[0]
        mid = self.cols[1]
        bottom = self.cols[2]
        plot_kwargs = dict(line_color='DarkViolet', line_width=0.5, legendgroup=self.name)
        if not self.visible:
            plot_kwargs['visible'] = 'legendonly'

        trace_mid = go.Scatter(x=df[mid].index, y=df[mid],
                               name=mid, **plot_kwargs)
        trace_top = go.Scatter(x=df[upper].index, y=df[upper],
                               name=upper, mode='lines', fill=None, **plot_kwargs)
        trace_bot = go.Scatter(x=df[bottom].index, y=df[bottom],
                               name=bottom, mode='lines', fill='tonexty', **plot_kwargs,
                               fillcolor="rgba(148, 0, 211, 0.15)")
        loc = dict(row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(trace_mid, **loc)
        fig.add_trace(trace_top, **loc)
        fig.add_trace(trace_bot, **loc)
        return fig
