from plotly import graph_objects as go
import pandas as pd
from . import EMA
from . import SMA


# MACD = EMA(CLOSE, 12)-EMA(CLOSE, 26)
#
# SIGNAL = SMA(MACD, 9)
#
# Where:
# EMA – the Exponential Moving Average;
# SMA – the Simple Moving Average;
# SIGNAL – the signal line of the indicator.
# https://cdn.website-editor.net/25dd89c80efb48d88c2c233155dfc479/files/uploaded/The-Complete-Guide-to-Trading.pdf
class MACD:
    def __init__(self, lookahead_short=12, lookahead_long=26, lookahead_sma=9):
        self.lookahead_short = lookahead_short
        self.lookahead_long = lookahead_long
        self.lookahead_sma = lookahead_sma
        #
        self.ema_short = EMA(lookahead_short)
        self.ema_long = EMA(lookahead_long)
        self.sma = SMA(lookahead_sma)

    def calc(self, prices) -> pd.DataFrame:
        macd = self.ema_short.calc(prices) - self.ema_long.calc(prices)
        sma = self.sma.calc(macd)
        hist = macd - sma
        self.name = f"MACD({self.lookahead_short},{self.lookahead_long},{self.lookahead_sma})"
        cols = ['MCADEMA', 'MCADSMA', 'MCADHIST']
        self.macd = pd.DataFrame(dict(zip(cols, [macd, sma, hist])))
        return self.macd

    def plot(self, fig, loc: tuple):
        kwrags = dict(legendgroup=self.name, line_width=1, name=self.name)
        t_mcad = go.Scatter(x=self.macd['MCADEMA'].index, y=self.macd['MCADEMA'], line_color='blue',
                            **kwrags)
        trace_sma = go.Scatter(x=self.macd['MCADSMA'].index, y=self.macd['MCADSMA'], line_color='red',
                               **kwrags)
        t_hist = go.Scatter(x=self.macd['MCADHIST'].index, y=self.macd['MCADHIST'], line_color='white',
                            fill='tozeroy',
                            **kwrags)
        # fig.add_trace(t_mcad, row=loc[0], col=loc[1])
        # fig.add_trace(trace_sma, row=loc[0], col=loc[1])
        fig.add_trace(t_hist, row=loc[0], col=loc[1])
        fig.add_hline(y=0, row=loc[0], col=[1], line_width=0.5, line_color='Red')
        return fig
