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


def combine_value_ts_supports_by_index(ohlc_index, res, idx=None):
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


def fix_support_resistance_to_close_price(res, close, pct_win=1.15, pct_lose=.90):
    win_val = close * pct_win
    lose_val = close * pct_lose
    res['resistance'] = np.maximum(res['resistance'], win_val)
    res['support'] = np.minimum(res['support'], lose_val)
    return res


class SupportResistanceLines2(Indicator):
    """
    generate supports and resistance lines, used for stoploss and takeprofit
    lookahead_length
    """

    def __init__(self, lookback_length=None, fix_if_too_close=True, plot_index=-1, plot_loc=None):
        self.name = "SUPPORT_RESISTANCE"
        self.lookback_length = lookback_length
        self.plot_index = plot_index
        self.n_lookahead_points = 7
        self.plot_ts = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.ohlcv = None
        self.resistances_value = None
        self.supports_value = None
        self.lookaheads = None
        # TODO: add a print of that to the __repr__.
        self.fix_if_too_close = fix_if_too_close

    # TODO: support resistance should be calculated in predfined intervals, OR by getting k maximums as resistances and supports.
    # TODO: Improve perfromance for this algorithm, can add option if plot to calculate indexes
    def calc(self, ohlc: pd.DataFrame):
        idx = len(ohlc) + self.plot_index
        self.plot_ts = ohlc.index[idx]
        # start with multiple lookaheads, but combine them later.
        if self.lookback_length:
            lookaheads = [self.lookback_length]
        else:
            first_lookup = max(int(len(ohlc) * 0.05), 10)
            max_lookup = len(ohlc)
            lookaheads = np.linspace(first_lookup, max_lookup, self.n_lookahead_points).astype(int)
            self.lookback_length = lookaheads[0]  # just return something so dashboard wont fall

        # for each point in data, we will have n_lookaheads of support and resistance.
        self.ohlcv = ohlc
        self.resistances_value = [calc_roll(ohlc, lk, is_idx=False, is_max=True) for lk in lookaheads]
        self.supports_value = [calc_roll(ohlc, lk, is_idx=False, is_max=False) for lk in lookaheads]
        self.lookaheads = lookaheads
        res = pd.concat([self.resistances_value[0], self.supports_value[0]], axis=1)
        res = res.rename(
            columns={f'high_{self.lookback_length}': 'resistance',
                     f'low_{self.lookback_length}': 'support'})
        if self.fix_if_too_close:
            res = fix_support_resistance_to_close_price(res, ohlc.close)
        return res

    def _plot(self, fig, ts, v, is_max):
        c = 'red' if is_max else 'green'
        # can use first ts if using lines in the middle.
        time_delta_str = get_str_name(self.plot_ts, ts, v, is_max=is_max)
        t = go.Scatter(x=[ts, self.plot_ts], y=[v, v], name=time_delta_str, mode='lines',
                       hoverinfo='skip', legendgroup='support_resistance',
                       line_dash="dot", line_color=c, line_width=1)
        fig.add_trace(t, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig

    def plot(self, fig):
        ohlc = self.ohlcv
        lookaheads = self.lookaheads
        resistances_ts = [calc_roll(ohlc, lk, is_idx=True, is_max=True) for lk in lookaheads]
        supports_ts = [calc_roll(ohlc, lk, is_idx=True, is_max=False) for lk in lookaheads]
        # combine all into one dataframe, each support resistance will have #number of lookaheads
        all_combined = pd.concat(self.resistances_value + resistances_ts + self.supports_value + supports_ts, axis=1)
        # TODO: limit res to one major line.
        idx = len(ohlc) + self.plot_index
        # used for plot, combines ts and its support / resistance level into ts/value series
        supports, resistances = combine_value_ts_supports_by_index(ohlc.index, all_combined, idx=idx)
        for min_ts, min_v in supports.items():
            fig = self._plot(fig, min_ts, min_v, False)
        for max_ts, max_v in supports.items():
            fig = self._plot(fig, max_ts, max_v, True)

        return fig
