# SupportResistanceLines
from plotly import graph_objects as go
import pandas as pd
import numpy as np
from .Indicator import Indicator, human_format, human_format_time

# Support is the level at which demand is strong enough to stop the stock from falling any further.
def get_str_name(currents_ts, ts, v, is_max):
    time_delta = (currents_ts - ts).total_seconds()
    time_delta_str = human_format_time(time_delta)
    time_delta_str = f'{human_format(v)}({time_delta_str})'
    time_delta_str = f'R:{time_delta_str}' if is_max else f'S:{time_delta_str}'
    return time_delta_str


# Relevant only on recent stock value, so it will calc based on fixed intervals
# TODO: Can also add multiple support and resistance to the dataframe, so it will have 1st support/ 2nd support etc, instead of only latest
class SupportResistanceLines(Indicator):
    def __init__(self, from_lookahead=14, upto_lookahead=365, n_lookaheads=5, geometric_spacing=False, plot_loc=None):
        self.lookaheads_params = [from_lookahead, upto_lookahead, n_lookaheads]
        if geometric_spacing:
            self.lookaheads = np.geomspace(from_lookahead, upto_lookahead, n_lookaheads).astype(int)
        else:
            self.lookaheads = np.linspace(from_lookahead, upto_lookahead, n_lookaheads).astype(int)
        self.geometric_spacing = geometric_spacing
        self.currents_ts = None
        self.v_lines_max = None
        self.v_lines_min = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    def calc(self, ohlc: pd.DataFrame):
        v_lines_min = pd.Series(dtype=float)
        v_lines_max = pd.Series(dtype=float)
        self.currents_ts = ohlc.index[-1]
        for lookahead in self.lookaheads:
            if lookahead < len(ohlc):
                lk_interval = ohlc[-lookahead:]
                minimum = lk_interval['low'].sort_values()[:1]
                v_lines_min = pd.concat([v_lines_min, minimum])
                maximum = lk_interval['high'].sort_values(ascending=False)[:1]
                v_lines_max = pd.concat([v_lines_max, maximum])
                # print(lookahead, minimum, maximum)
        # filter if current is a support/resist, drop duplicates and rename for join
        self.v_lines_max = v_lines_max[v_lines_max.index < self.currents_ts].drop_duplicates().rename("resistance")
        self.v_lines_min = v_lines_min[v_lines_min.index < self.currents_ts].drop_duplicates().rename("support")
        # expand to dataframe and forward fill, can be bfill the missing (but does not really matter that far away)
        res = ohlc['low'].to_frame().join([self.v_lines_max, self.v_lines_min], how='outer').fillna(
            method='ffill')  # .fillna(method='bfill')
        return res[['resistance', 'support']]

    def _plot(self, fig, ts, v, is_max):
        c = 'red' if is_max else 'green'
        time_delta_str = get_str_name(self.currents_ts, ts, v, is_max=is_max)
        t = go.Scatter(x=[ts, self.currents_ts], y=[v, v], name=time_delta_str, mode='lines',
                       hoverinfo='skip', legendgroup='support_resistance',
                       line_dash="dot", line_color=c, line_width=1)
        fig.add_trace(t, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig

    def plot(self, fig):
        for min_ts, min_v in self.v_lines_min.items():
            fig = self._plot(fig, min_ts, min_v, False)
        for max_ts, max_v in self.v_lines_max.items():
            fig = self._plot(fig, max_ts, max_v, True)

        return fig

# https://plotly.com/python/shapes/
# fig.add_shape(dict(type="line", x0=min_v_ts, x1=self.currents_ts, y0=min_v_val, y1=min_v_val,
#                    name='ss', line_dash="dash", line_color="green"))
# fig.add_hline(y=min_v, row=loc[0], col=[1], line_width=1, line_color='green', line_dash="dash")
