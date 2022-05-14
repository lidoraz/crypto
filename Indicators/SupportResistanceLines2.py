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


# using non null function to ignore them
def calc_roll(ohlc, lk, is_idx, is_max):
    col = 'high' if is_max else 'low'
    if is_idx:
        func = np.nanargmax if is_max else np.nanargmin
        indxes = ohlc[col].rolling(lk, min_periods=1).apply(func).rename(
            f'{col}_idx_{lk}') - lk + 1 + np.arange(len(ohlc.index))
        return indxes
    else:
        func = np.nanmax if is_max else np.nanmin
        return ohlc[col].rolling(lk, min_periods=1).apply(func).rename(
            f'{col}_{lk}')
    # if is_idx:
    #     func = np.nanargmax if is_max else np.nanargmin
    #     # TODO: try to use like shift, need for each lookahead take lookback such that lookahead is:   end<-----start<---now
    #     indxes = ohlc[col].shift(lk_half).rolling(lk_half, min_periods=1).apply(func).rename(
    #         f'{col}_idx_{lk}') - lk + 1 + np.arange(len(ohlc.index))
    #     return indxes - lk_half
    # else:
    #     func = np.nanmax if is_max else np.nanmin
    #     return ohlc[col].shift(lk).rolling(lk, min_periods=1).apply(func).rename(
    #         f'{col}_{lk}')


def lines_by_index(ohlc_index, res, idx=None):
    val_cols = [c for c in res.columns if 'idx' not in c]
    idx_cols = [c for c in res.columns if 'idx' in c]
    # ts_at_idx = res.index[idx]  # res.index[idx] + pd.Timedelta()
    idx_dict = res[idx:idx + 1][idx_cols].apply(lambda x: ohlc_index[int(np.maximum(0, np.nan_to_num(x)))]).to_dict()
    val_dict = res[idx:idx + 1][val_cols].iloc[0].to_dict()
    idx_high = [idx_dict[k] for k in idx_dict if 'high' in k]
    val_high = [val_dict[k] for k in val_dict if 'high' in k]
    idx_low = [idx_dict[k] for k in idx_dict if 'low' in k]
    val_low = [val_dict[k] for k in val_dict if 'low' in k]
    supports = pd.Series(val_low, index=idx_low).sort_index(ascending=False)
    resistances = pd.Series(val_high, index=idx_high).sort_index(ascending=False)
    # print('idx', idx, 'ts', ts_at_idx)
    # print('supports')
    # print(supports)
    # print('resistances')
    # print(resistances)
    return supports, resistances


class SupportResistanceLines2(Indicator):
    def __init__(self, lookahead=None, plot_index=-1, plot_loc=None):
        self.lookahead = lookahead
        self.plot_index = plot_index
        self.n_lookahead_points = 7
        self.current_ts = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    # TODO: support resistance should be calculated in predfined intervals, OR by getting k maximums as resistances and supports.
    def calc(self, ohlc: pd.DataFrame):
        import time
        calc_ts = time.time()
        print('calc called', calc_ts)
        first_lookup = 30
        max_lookup = len(ohlc)  # // 2
        lookaheads = np.linspace(first_lookup, max_lookup, self.n_lookahead_points).astype(int)
        # TODO: take only middle
        lk = self.lookahead
        if self.lookahead:
            lookaheads = [self.lookahead]

        # for each point, we will have n_points of support and resistance.
        resistances = [calc_roll(ohlc, lk, is_idx=False, is_max=True) for lk in lookaheads]
        supports = [calc_roll(ohlc, lk, is_idx=False, is_max=False) for lk in lookaheads]
        resistances_idx = [calc_roll(ohlc, lk, is_idx=True, is_max=True) for lk in lookaheads]
        supports_idx = [calc_roll(ohlc, lk, is_idx=True, is_max=False) for lk in lookaheads]
        res = pd.concat(resistances + resistances_idx + supports + supports_idx, axis=1)
        idx = len(ohlc) + self.plot_index
        # idx = np.random.randint(0, len(ohlc))
        supports, resistances = lines_by_index(ohlc.index, res, idx=idx)
        # TODO: Can combine multiple supports if they are realtive close to each other, by 5% ...
        self.current_ts = ohlc.index[idx]
        self.v_lines_min = supports
        self.v_lines_max = resistances
        # print('calc_time', time.time() - calc_ts)
        lk = str(lk)
        res_selected = res[[c for c in res.columns if lk in c and 'idx' not in c]]
        res_selected = res_selected.rename(columns={f'high_{lk}': 'resistance', f'low_{lk}': 'support'})
        return res_selected

    def _plot(self, fig, ts, v, is_max):
        c = 'red' if is_max else 'green'
        # can use first ts if using lines in the middle.
        time_delta_str = get_str_name(self.current_ts, ts, v, is_max=is_max)
        t = go.Scatter(x=[ts, self.current_ts], y=[v, v], name=time_delta_str, mode='lines',
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
