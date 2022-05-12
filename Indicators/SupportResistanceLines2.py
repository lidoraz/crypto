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


class Sup_Res_Finder:
    def isSupport(self, df, i):
        support = df['low'][i] < df['low'][i - 1] and \
                  df['low'][i] < df['low'][i + 1] and \
                  df['low'][i + 1] < df['low'][i + 2] and \
                  df['low'][i - 1] < df['low'][i - 2]

        return support

    def isResistance(self, df, i):
        resistance = df['high'][i] > df['high'][i - 1] and \
                     df['high'][i] > df['high'][i + 1] > df['high'][i + 2] and \
                     df['high'][i - 1] > df['high'][i - 2]

        return resistance

    def find_levels(self, df):
        levels = []
        lows = []
        highs = []
        s = np.mean(df['high'] - df['low'])

        for i in range(2, df.shape[0] - 2):
            if self.isSupport(df, i):
                l = df['low'][i]

                if np.sum([abs(l - x) < s for x in levels]) == 0:
                    levels.append((i, l))
                    lows.append((df.index[i], l))
            elif self.isResistance(df, i):
                l = df['high'][i]

                if np.sum([abs(l - x) < s for x in levels]) == 0:
                    levels.append((i, l))
                    highs.append((df.index[i], l))

        idx, values = zip(*lows)
        lows = pd.Series(values, idx)
        idx, values = zip(*highs)
        highs = pd.Series(values, idx)
        return lows, highs


# Relevant only on recent stock value, so it will calc based on fixed intervals
class SupportResistanceLines2(Indicator):
    def __init__(self, plot_loc=None):
        pass
        # self.from_lookahead = from_lookahead
        # self.upto_lookahead = upto_lookahead
        # self.n_lookaheads = n_lookaheads
        # if geometric_spacing:
        #     self.lookaheads = np.geomspace(from_lookahead, upto_lookahead, n_lookaheads).astype(int)
        # else:
        #     self.lookaheads = np.linspace(from_lookahead, upto_lookahead, n_lookaheads).astype(int)
        # self.geometric_spacing = geometric_spacing
        self.currents_ts = None
        # self.v_lines_max = None
        # self.v_lines_min = None
        self.plot_loc = (plot_loc, 1 if plot_loc else None)

    # def _set_lookaheads(self, upto_lookahead):
    #     params = (self.from_lookahead, upto_lookahead, self.n_lookaheads)
    #     if self.geometric_spacing:
    #         self.lookaheads = np.geomspace(*params).astype(int)
    #     else:
    #         self.lookaheads = np.linspace(*params).astype(int)

    # TODO: support resistance should be calculated in predfined intervals, OR by getting k maximums as resistances and supports.
    def calc(self, ohlc: pd.DataFrame):
        self.current_ts = ohlc.index[-1]
        curr_max = -np.inf
        curr_min = np.inf
        # Swing
        # change_pct
        change_pct = 0.05
        lows = []
        highs = []

        n_points = 10
        lookaheads = np.geomspace(14, len(ohlc), n_points).astype(int)
        resistances = [ohlc['high'].rolling(lk, min_periods=1).max().rename(f'high_{lk}') for lk in lookaheads]
        supports = [ohlc['low'].rolling(lk, min_periods=1).min().rename(f'low_{lk}') for lk in lookaheads]
        # for each point, we will have n_points of support and resistance.
        iloc = 1000
        supports_last = [s.iloc[100:101] for s in supports]
        resistances_last = [s.iloc[100:101] for s in resistances]
        self.v_lines_min = pd.concat(supports_last).drop_duplicates()
        self.v_lines_max = pd.concat(resistances_last).drop_duplicates()
        res = pd.concat(resistances + supports, axis=1)
        # print(df.shape)
        # for idx, row in ohlc.iterrows():
        #     # min:
        #     if curr_min > (1+change_pct) * row['low']:
        #         curr_min = row['low']
        #     #max:
        #     if curr_max * (1+change_pct) < row['high']:
        #         curr_max = row['high']
        #
        #     # detect swing.
        #     lows.append(curr_min)
        #     highs.append(curr_max)

        # def filter_by_stats(s, mul=1):
        #     s = s[~s.duplicated()]
        #     diff_mean_std = abs(s.diff().mean()) + s.diff().std() * mul
        #     s = s[abs(s.diff()) > diff_mean_std]
        #     return s
        # highs = ohlc['high'].cummax()
        # lows = ohlc['low'].cummin()
        #
        # print(highs)
        # # res = pd.DataFrame({'resistance': highs, 'support': lows})
        # # lows
        # # finder = Sup_Res_Finder()
        # # lows, highs = finder.find_levels(ohlc)
        # res = pd.DataFrame({'support': lows, 'ldiff': lows.diff(), 'lshift': lows.shift(1), 'resistance': highs, 'hdiff': highs.diff(),'hshift': highs.shift(1) })
        # # res = pd.DataFrame({'resistance': highs, 'support': lows})
        # # for idx, row in res.iterrows():
        # #     if row['hdiff'] > 0: # uptrend
        # #         res.loc[idx, 'support'] = row['hshift']
        # #     if row['ldiff'] < 0: # downtrend
        # #         res.loc[idx, 'resistance'] = row['lshift']
        #
        # res = res[['support', 'resistance']]
        # self.v_lines_min = res['support'].drop_duplicates().sort_values(ascending=True)[:10]
        # self.v_lines_max = res['resistance'].drop_duplicates().sort_values(ascending=False)[:10]
        return res

        # print(lows, highs, levels)
        # print()
        # self._set_lookaheads(len(ohlc))
        # for lookahead in self.lookaheads:
        #     if lookahead < len(ohlc):
        #         lk_interval = ohlc[-lookahead:]
        #         minimum = lk_interval['low'].sort_values()[:1]
        #         v_lines_min = pd.concat([v_lines_min, minimum])
        #         maximum = lk_interval['high'].sort_values(ascending=False)[:1]
        #         v_lines_max = pd.concat([v_lines_max, maximum])
        #         # print(lookahead, minimum.to_dict(), maximum.to_dict())
        # # filter if current is a support/resist, drop duplicates and rename for join
        # self.v_lines_max = v_lines_max[v_lines_max.index < self.current_ts].drop_duplicates().rename("resistance")
        # self.v_lines_min = v_lines_min[v_lines_min.index < self.current_ts].drop_duplicates().rename("support")
        # # expand to dataframe and forward fill, can be bfill the missing (but does not really matter that far away)
        # res = ohlc['low'].to_frame().join([self.v_lines_max, self.v_lines_min], how='outer').fillna(
        #     method='ffill')  # .fillna(method='bfill')

    def _plot(self, fig, ts, v, is_max):
        c = 'red' if is_max else 'green'
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

# https://plotly.com/python/shapes/
# fig.add_shape(dict(type="line", x0=min_v_ts, x1=self.current_ts, y0=min_v_val, y1=min_v_val,
#                    name='ss', line_dash="dash", line_color="green"))
# fig.add_hline(y=min_v, row=loc[0], col=[1], line_width=1, line_color='green', line_dash="dash")
