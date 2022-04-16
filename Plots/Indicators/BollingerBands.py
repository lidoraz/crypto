from plotly import graph_objects as go
import pandas as pd


class BollingerBands:
    def __init__(self, lookahead=25, std_m=2):
        self.lookahead = lookahead
        self.std_m = std_m
        self.bb = None
        self.cols = None

    def calc(self, prices) -> pd.DataFrame:
        rolling_func = prices.rolling(self.lookahead)
        sma = rolling_func.mean()
        top_BB = sma + rolling_func.std() * self.std_m
        bot_BB = sma - rolling_func.std() * self.std_m
        cols = ['SMA_{}', 'BBTOP_{}', 'BBBOT_{}']
        self.cols = [x.format(self.lookahead) for x in cols]
        self.bb = pd.DataFrame(dict(zip(self.cols, [top_BB, sma, bot_BB])))
        return self.bb

    def plot(self, fig):
        name = f'BB({self.lookahead})'
        top_trace = go.Scatter(x=self.bb[self.cols[0]].index, y=self.bb[self.cols[0]], name=name, line_color='purple',
                               line_width=1,
                               legendgroup=name, opacity=0.2, visible='legendonly')
        bot_trace = go.Scatter(x=self.bb[self.cols[2]].index, y=self.bb[self.cols[2]], fill='tonexty', name=name,
                               line_color='purple', line_width=1,
                               legendgroup=name, opacity=0.2, visible='legendonly')
        fig.add_trace(top_trace)
        fig.add_trace(bot_trace)
        return fig
