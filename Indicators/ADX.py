from plotly import graph_objects as go
import pandas as pd
import numpy as np
from . import EMA

from .Indicator import Indicator


# https://medium.com/codex/does-combining-adx-and-rsi-create-a-better-profitable-trading-strategy-125a90c36ac
def get_adx(high, low, close, lookback):
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr1 = pd.DataFrame(high - low)
    tr2 = pd.DataFrame((high - close.shift(1)).abs())
    tr3 = pd.DataFrame((low - close.shift(1)).abs())
    frames = [tr1, tr2, tr3]
    tr = pd.concat(frames, axis=1, join='inner').max(axis=1)
    atr = tr.rolling(lookback).mean()

    plus_di = 100 * (plus_dm.ewm(alpha=1 / lookback).mean() / atr)
    minus_di = (100 * (minus_dm.ewm(alpha=1 / lookback).mean() / atr)).abs()
    dx = ((plus_di - minus_di).abs() / (plus_di + minus_di).abs()) * 100
    adx = ((dx.shift(1) * (lookback - 1)) + dx) / lookback
    adx_smooth = adx.ewm(alpha=1 / (lookback // 2)).mean()
    return plus_di, minus_di, adx, adx_smooth


class ADX(Indicator):
    """
    Momentum indicator, used to detect momentum
    MACD measures the relationship between two EMAs
    MACD = EMA(CLOSE, 12)-EMA(CLOSE, 26)
    SIGNAL = SMA(MACD, 9)
    """

    def __init__(self, lookback=14, plot_loc=None):
        super(ADX, self).__init__(f"ADX({lookback}", "SUB_PLOT")
        self.lookback = lookback
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    def calc(self, ohlc) -> pd.DataFrame:
        plus_di, minus_di, adx, adx_smooth = get_adx(ohlc['high'], ohlc['low'], ohlc['close'], self.lookback)
        df_adx = pd.DataFrame(dict(plus_di=plus_di, minus_di=minus_di, adx=adx, adx_smooth=adx_smooth))
        return df_adx

    def plot(self, df, fig):
        plus_di = df['plus_di']
        minus_di = df['minus_di']
        adx = df['adx_smooth']  # adx_smooth # smooth is lagging, but more precise
        t_di_plus = go.Scatter(x=plus_di.index, y=plus_di,
                               line_color="#4CAF50",
                               line_width=1, legendgroup=self.name, name="DI+")
        t_di_minus = go.Scatter(x=minus_di.index, y=minus_di,
                                line_color="#FF5252",
                                line_width=1, legendgroup=self.name, name="DI-")
        t_adx = go.Scatter(x=adx.index, y=adx, line_width=1.5,
                           line_color="white", legendgroup=self.name, name=self.name)
        fig.add_trace(t_di_plus, row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(t_di_minus, row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_trace(t_adx, row=self.plot_loc[0], col=self.plot_loc[1])
        fig.add_hline(y=20, row=self.plot_loc[0], col=self.plot_loc[1], line_width=1, line_dash="dash",
                      line_color='#ffa726')
        return fig
