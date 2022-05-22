# SupportResistanceLines
from plotly import graph_objects as go
import pandas as pd
import numpy as np
from .Indicator import Indicator, human_format, human_format_time


# TODO ReworkNaming
class WinLossStoploss(Indicator):
    def __init__(self, win_pct: float, lose_pct: float, plot_loc=None):
        self.win_pct = win_pct
        self.lose_pct = lose_pct
        self.current_ts = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    # TODO: support resistance should be calculated in predfined intervals, OR by getting k maximums as resistances and supports.
    def calc(self, ohlc: pd.DataFrame):
        support = ohlc['low'] - ohlc['low'] * self.lose_pct
        resistance = ohlc['high'] + ohlc['high'] * self.win_pct
        res = pd.DataFrame({'resistance': resistance, 'support': support})
        return res

    def _plot(self, fig, ts, v, is_max):
        c = 'red' if is_max else 'green'
        # can use first ts if using lines in the middle.
        # time_delta_str = get_str_name(self.current_ts, ts, v, is_max=is_max)
        # t = go.Scatter(x=[ts, self.current_ts], y=[v, v], name=time_delta_str, mode='lines',
        #                hoverinfo='skip', legendgroup='support_resistance',
        #                line_dash="dot", line_color=c, line_width=1)
        fig.add_trace(t, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig

    def plot(self, fig):
        # for min_ts, min_v in self.v_lines_min.items():
        #     fig = self._plot(fig, min_ts, min_v, False)
        # for max_ts, max_v in self.v_lines_max.items():
        #     fig = self._plot(fig, max_ts, max_v, True)

        return fig
