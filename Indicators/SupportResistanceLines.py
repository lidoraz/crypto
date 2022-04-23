# SupportResistanceLines
from plotly import graph_objects as go
import pandas as pd
import numpy as np
from .Indicator import Indicator


# Support is the level at which demand is strong enough to stop the stock from falling any further.
def get_str_name(currents_ts, ts, v, is_max):
    time_delta = (currents_ts - ts).days
    time_delta_str = f'{int(np.floor(time_delta / 30))}M' if time_delta > 30 else f'{int(time_delta)}D'
    time_delta_str = f'R:{time_delta_str}_{round(v)}' if is_max else f'S:{time_delta_str}_{round(v)}'
    return time_delta_str


# Relevant only on recent stock value, so it will calc based on fixed intervals
# TODO: Can also add multiple support and resistance to the dataframe, so it will have 1st support/ 2nd support etc, instead of only latest
class SupportResistanceLines(Indicator):
    def __init__(self, from_lookahead=14, upto_lookahead=720, n_lookaheads=7):
        self.lookaheads_params = [from_lookahead, upto_lookahead, n_lookaheads]
        self.lookaheads = np.geomspace(from_lookahead, upto_lookahead, n_lookaheads).astype(int)
        self.currents_ts = None
        self.v_lines_max = None
        self.v_lines_min = None

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
                print(lookahead, minimum, maximum)

        self.v_lines_max = v_lines_max.drop_duplicates().rename("resistance")
        self.v_lines_min = v_lines_min.drop_duplicates().rename("support")
        # expand to dataframe and forward fill, can be bfill the missing (but does not really matter that far away)
        res = ohlc['low'].to_frame().join([self.v_lines_max, self.v_lines_min], how='outer').fillna(
            method='ffill')  # .fillna(method='bfill')
        return res[['resistance', 'support']]

    def plot(self, fig, loc=(None, None), color='Orange'):
        for min_ts, min_v in self.v_lines_min.items():
            time_delta_str = get_str_name(self.currents_ts, min_ts, min_v, is_max=False)
            t = go.Scatter(x=[min_ts, self.currents_ts], y=[min_v, min_v], name=time_delta_str,
                           line_dash="dash", line_color="green")
            fig.add_trace(t, row=loc[0], col=loc[1])
        for max_ts, max_v in self.v_lines_max.items():
            time_delta_str = get_str_name(self.currents_ts, max_ts, max_v, is_max=True)
            t = go.Scatter(x=[max_ts, self.currents_ts], y=[max_v, max_v], name=time_delta_str,
                           line_dash="dash", line_color="red")
            fig.add_trace(t, row=loc[0], col=loc[1])

        fig.update_layout(showlegend=True)
        return fig

# https://plotly.com/python/shapes/
# fig.add_shape(dict(type="line", x0=min_v_ts, x1=self.currents_ts, y0=min_v_val, y1=min_v_val,
#                    name='ss', line_dash="dash", line_color="green"))
# fig.add_hline(y=min_v, row=loc[0], col=[1], line_width=1, line_color='green', line_dash="dash")
