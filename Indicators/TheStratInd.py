import pandas as pd
import numpy as np
from plotly import graph_objects as go

from Data.Crypto.ccxt_utils import _resample_from_ohlcv
from .Indicator import Indicator


def get_color(ohlc):
    def colorize(row):
        return 'R' if row['open'] >= row['close'] else 'G'

    return ohlc.apply(colorize, axis=1).rename('cnd_color')


def get_numbers(ohlc):
    low_prev = ohlc['low'].shift(1)
    high_prev = ohlc['high'].shift(1)
    is_one = (low_prev < ohlc['low']) & (high_prev > ohlc['high'])
    is_three = (low_prev > ohlc['low']) & (high_prev < ohlc['high'])
    # is_two = (~is_one) & (~is_three)
    is_two_up = (ohlc['low'] > low_prev) & (high_prev < ohlc['high'])
    is_two_down = (ohlc['low'] < low_prev) & (high_prev > ohlc['high'])
    # return pd.Series(is_one * 1 + is_two * 2 + is_three * 3).rename('thestrat_num')
    return pd.Series(is_one * 1 + is_two_up * 2.1 + is_two_down * 2.2 + is_three * 3).rename('thestrat_num')


def get_combos(ohlc):
    # 212 Bear R, 212 Bull R
    # 22 Bear R, 22 Bull R
    # 312 Bear R, # 312 Bull R
    # 1 Bear R, 1 Bull R
    # TODO: FIX 222CL, where it is actually 222CS, as there are gaps even though the candles are green, they are red by the strat
    #  Can be fixed by looking at the code of thestrat, also there is nice explain of 1, 2U, 2D, and 3 to ease.
    # each combo should indicate entry and target, stop loss can be set as swing
    num_b3 = ohlc['thestrat_num'].shift(3)
    col_b3 = ohlc['cnd_color'].shift(3)
    num_b2 = ohlc['thestrat_num'].shift(2)
    col_b2 = ohlc['cnd_color'].shift(2)
    num_b1 = ohlc['thestrat_num'].shift(1)
    col_b1 = ohlc['cnd_color'].shift(1)
    num_b0 = ohlc['thestrat_num']
    col_b0 = ohlc['cnd_color']
    entry = None
    target = None
    stop = None

    # Reversals works correctly as the strat indicator, taking account 2 candles as 2up and 2down
    combos = dict(
        # reversal
        is_212RS=(num_b2 == 2.2) & (num_b1 == 1) & (num_b0 == 2.2),
        is_212RL=(num_b2 == 2.1) & (num_b1 == 1) & (num_b0 == 2.1),
        # reversal22, b1 candle low must be above next candle if L
        is_22RS=(num_b1 == 2.1) & (num_b0 == 2.2),
        is_22RL=(num_b1 == 2.2) & (num_b0 == 2.1),
        # Continuations
        is_212CS=(num_b2 == 2.2) & (num_b1 == 1) & (num_b0 == 2.2),
        is_212CL=(num_b2 == 2.1) & (num_b1 == 1) & (num_b0 == 2.1),
        is_222CS=(num_b2 == 2.2) & (num_b1 == 2.2) & (num_b0 == 2.2),
        is_222CL=(num_b2 == 2.1) & (num_b1 == 2.1) & (num_b0 == 2.1),
        # 322
        is_322RS=(col_b2 == 'G') & (num_b2 == 3) & (num_b1 == 2.2) & (num_b0 == 2.2),
        is_322RL=(col_b2 == 'R') & (num_b2 == 3) & (num_b1 == 2.1) & (num_b0 == 2.1),
        # 312
        is_312RS=(col_b2 == 'G') & (num_b2 == 3) & (num_b1 == 1) & (num_b0 == 2.2),
        is_312RL=(col_b2 == 'R') & (num_b2 == 3) & (num_b1 == 1) & (num_b0 == 2.1),
        # 122
        is_122RS=(num_b2 == 1) & (num_b1 == 2.1) & (num_b0 == 2.2),
        is_122RL=(num_b2 == 1) & (num_b1 == 2.2) & (num_b0 == 2.1),
        # # Below needs more clarification
        # 3-2
        is_32RS=(col_b1 == 'G') & (num_b1 == 3) & (num_b0 == 2.2),
        is_32RL=(col_b1 == 'R') & (num_b1 == 3) & (num_b0 == 2.1),
        # 1 Bar
        is_1RS=(col_b0 == 'R') & (num_b0 == 3),
        is_1RL=(col_b0 == 'G') & (num_b0 == 3),
        # 2-2-2
        is_222RS=(num_b3 == 2.2) & (num_b2 == 2.2) &
                 (num_b1 == 2.1) & (num_b0 == 2.2),
        is_222RL=(num_b3 == 2.1) & (num_b2 == 2.1) &
                 (num_b1 == 2.2) & (num_b0 == 2.1)

    )
    # combos = dict(
    #     # reversal
    #     is_212RS=(col_b2 == 'G') & (num_b2 == 2) & (num_b1 == 1) & (num_b0 == 2) & (col_b0 == 'R'),
    #     is_212RL=(col_b2 == 'R') & (num_b2 == 2) & (num_b1 == 1) & (num_b0 == 2) & (col_b0 == 'G'),
    #     # reversal22, b1 candle low must be above next candle if L
    #     is_22RS=(col_b1 == 'G') & (num_b1 == 2) & (num_b0 == 2) & (col_b0 == 'R'),
    #     is_22RL=(col_b1 == 'B') & (num_b1 == 2) & (num_b0 == 2) & (col_b0 == 'B'),
    #     # Continuations
    #     is_212CS=(col_b2 == 'R') & (num_b2 == 2) & (num_b1 == 1) & (num_b0 == 2) & (col_b0 == 'R'),
    #     is_212CL=(col_b2 == 'G') & (num_b2 == 2) & (num_b1 == 1) & (num_b0 == 2) & (col_b0 == 'G'),
    #     is_222CS=(col_b2 == 'R') & (num_b2 == 2) & (col_b1 == 'R') & (num_b1 == 2) & (num_b0 == 2) & (col_b0 == 'R'),
    #     is_222CL=(col_b2 == 'G') & (num_b2 == 2) & (col_b1 == 'G') & (num_b1 == 2) & (num_b0 == 2) & (col_b0 == 'G'),
    #     # 322
    #     is_322RS=(col_b2 == 'G') & (num_b2 == 3) & (col_b1 == 'R') & (num_b1 == 2) & (num_b0 == 2) & (col_b0 == 'R'),
    #     is_322RL=(col_b2 == 'R') & (num_b2 == 3) & (col_b1 == 'G') & (num_b1 == 2) & (num_b0 == 2) & (col_b0 == 'G'),
    #     # 312
    #     is_312RS=(col_b2 == 'G') & (num_b2 == 3) & (num_b1 == 1) & (num_b0 == 2) & (col_b0 == 'R'),
    #     is_312RL=(col_b2 == 'R') & (num_b2 == 3) & (num_b1 == 1) & (num_b0 == 2) & (col_b0 == 'G'),
    #     # 122
    #     is_122RS=(num_b2 == 1) & (col_b1 == 'G') & (num_b1 == 2) & (col_b0 == 'R') & (num_b0 == 2),
    #     is_122RL=(num_b2 == 1) & (col_b1 == 'R') & (num_b1 == 2) & (col_b0 == 'G') & (num_b0 == 2),
    #     # # Below needs more clarification
    #     # 3-2
    #     is_32RS=(col_b1 == 'G') & (num_b1 == 3) & (col_b0 == 'R') & (num_b0 == 2),
    #     is_32RL=(col_b1 == 'R') & (num_b1 == 3) & (col_b0 == 'G') & (num_b0 == 2),
    #     # 1 Bar
    #     is_1RS=(col_b0 == 'R') & (num_b0 == 3),
    #     is_1RL=(col_b0 == 'G') & (num_b0 == 3),
    #     # 2-2-2
    #     is_222RS=(col_b3 == 'R') & (num_b3 == 2) & (col_b2 == 'R') & (num_b2 == 2) &
    #              (col_b1 == 'G') & (num_b1 == 2) & (col_b0 == 'R') & (num_b0 == 2),
    #     is_222RL=(col_b3 == 'G') & (num_b3 == 2) & (col_b2 == 'G') & (num_b2 == 2) &
    #              (col_b1 == 'R') & (num_b1 == 2) & (col_b0 == 'G') & (num_b0 == 2)
    #
    # )
    combos_lst = list(combos.values())
    combos_names = [k[3:] for k in combos.keys()]
    combos_names_idx = list(range(1, len(combos_lst) + 1))
    combos_names = [''] + combos_names
    # combos = pd.concat(combos_lst, axis=1)
    # combos.columns = combos_names
    comb = pd.concat(list(map(lambda x: x[0] * x[1], zip(combos_lst, combos_names_idx))), axis=1)
    _combos = comb.sum(axis=1)
    _combos = comb.apply(lambda xx: [x for x in xx if x != 0], axis=1)
    _combos = _combos.apply(lambda xx: [combos_names[x] for x in xx])
    _combos = _combos.apply(lambda lst: max(lst) if len(lst) > 0 else '')  # take only strongest combo by string length
    # ohlc['thestrat_combo'] = is_one * 1 + is_two * 2 + is_three * 3
    # ohlc = pd.concat([ohlc, combos], axis=1)
    return _combos.rename('thestrat_combo')


_other_tf_ratio_str = 'thestratTF_{}'
_other_tf_number_str = 'thestratNUMBER_{}'
_other_tf_color_str = 'thestratCOLOR_{}'
_other_tf_combo_str = 'thestratCOMBO_{}'


class TheStratInd(Indicator):
    def __init__(self, calc_other_tf, db=None, plot_loc=None, color='Brown'):
        super(TheStratInd, self).__init__(f"TheStratInd", "MAIN_PLOT")
        if calc_other_tf:
            assert db is not None, 'when calculcating other tf, startdate and db must be present'
        self._db = db
        self._calc_other_tf = calc_other_tf

        self.plot_loc = (plot_loc, 1 if plot_loc else None)
        self.color = color

    def get_other_timeframes(self, ohlc):
        from Data.Crypto.ccxt_utils import get_candles_from_db
        from tqdm import tqdm
        attrs = ohlc.attrs
        tf = attrs['interval']
        symbol = attrs['symbol'].split('/')[0]
        tfs_default = ['1T', '3T', '5T', '15T', '30H', '1H', '2H', '4H', '12H', '1D', '1W', '4W', '12W']
        tfs_to_check = tfs_default[1 + tfs_default.index(tf):]
        self._tfs_to_check = []
        data_1m = get_candles_from_db(self._db, symbol, '1T', start_date=str(ohlc.index[0].date()), localize=ohlc.index.tz)
        # Calculate using fixed TF windows
        # for tf_check in tqdm(tfs_to_check):
        #     tf_check_str = _tf_check_str.format(tf_check)
        #     data_another_tf = _resample_from_ohlcv(data_1m, self._symbol, tf_check)
        #     ohlc[tf_check_str] = data_another_tf['open'].resample(self._tf).first().ffill()
        #     ohlc[tf_check_str] = ohlc[tf_check_str].ffill()
        #     ohlc[tf_check_str] = ohlc.apply(lambda row: (row['close'] / row[tf_check_str]) - 1, axis=1)
        #     assert len(data_another_tf)
        #     self.tfs_to_check.append(tf_check_str)
        print('tfs_to_check', tfs_to_check)
        # Calculate using moving window TF
        for tf_check in tqdm(tfs_to_check):
            # Get ratio
            tf_check_str = _other_tf_ratio_str.format(tf_check)
            index_minus_tf = ohlc.index - pd.to_timedelta(tf_check)
            index_minus_tf = np.where(index_minus_tf >= data_1m.index.min(), index_minus_tf, data_1m.index.min())
            open_tf_values = data_1m.loc[index_minus_tf]['open'].values
            ohlc[tf_check_str] = ohlc['close'] / open_tf_values - 1  # new / old , calculate change in various TFs
            self._tfs_to_check.append(tf_check_str)
            # Get Number # ohlc.merge(ohlc_t['cnd_color'])
            # ohlc.join(ohlc_t['cnd_color'].rename(_other_tf_color_str.format(tf_check)))
            # _other_tf_number_str
            # NOT GOOD CALCULATION WAY
            # should be done calculating each day start, to every timestamp in the dataset, ending every 24H
            # TODO: Add here implmenet other tf combos, add them to the main data
            # ohlc_t = _resample_from_ohlcv(data_1m, symbol, '1D')
            # ohlc_t = ohlc_t.join(get_numbers(ohlc_t))
            # ohlc_t = ohlc_t.join(get_color(ohlc_t))
            # ohlc_t = ohlc_t.join(get_combos(ohlc_t))
            print()
            #
        return ohlc

    def calc(self, ohlc):
        # TODO: TF CONTINUITY - CHECK ON HIGHER LEVELS - IF BEAR / BULL by simply checking on candle color
        s_numbers = get_numbers(ohlc)
        s_color = get_color(ohlc)
        res = pd.concat([s_numbers, s_color], axis=1)
        s_combos = get_combos(res)
        res = pd.concat([res, s_combos], axis=1)
        # ohlc = get_combos(ohlc)
        if self._calc_other_tf:
            # TODO: FIX HERE, also in the function itself
            ohlc = self.get_other_timeframes(ohlc)
        # GET MORE TIME FRAMES from upper TFS,
        # Configure entry, stoploss, targets.

        # not needed, API demands to return something to the indicators
        # ra = ohlc['close'].ewm(span=1, adjust=False,
        #                        min_periods=1).mean()  # closed to the right!!
        # ra.name = self.name
        return res

    def plot(self, df, fig):
        # Add Strat numbers to candlestick (currently in display on hover)
        import random
        time_conts = []
        print(df[self._tfs_to_check].tail(1).to_dict())
        for idx, row in df[-50:].iterrows():
            if not len(row['thestrat_combo']):
                time_conts.append('')
                continue
            # combo = max(row['thestrat_combo'])
            combo = row['thestrat_combo']
            # tfs_cont = row[self._tfs_to_check]
            # tfs_cont_str = ','.join(tfs_cont.apply(lambda x: '▲' if x > 0 else '▼'))
            # time_conts.append(tfs_cont_str)
            if 'RL' in combo:
                color = 'Green'
                # continue
            elif 'CL' in combo:
                color = '#094201'
            elif 'RS' in combo:
                color = 'Red'
                # continue
            elif 'CS' in combo:
                color = '#420101'
            else:
                continue
                color = 'gray'
            # tfs_cont = f'pos:{sum(tfs_cont > 0)}/{len(tfs_cont)}'
            # tfs_cont = ''

            fig.add_annotation(x=idx, y=row['high'],
                               text=combo,
                               bgcolor=color,
                               # arrowcolor="#FFFFFF",
                               # showarrow=True,
                               arrowhead=1
                               )
        assert fig.data[0].name == 'Candle'
        if self._calc_other_tf:
            converted_df = df[self._tfs_to_check].applymap(lambda x: '▲' if x > 0 else '▼')
            for col in self._tfs_to_check:
                _tf = col.split('_')[-1]
                converted_df[col] = converted_df[col].apply(lambda x: f'{_tf}:{x}')
            tfs_cont_str = converted_df.apply(lambda x: ','.join(x), axis=1).tolist()
            # tfs_cont_str = df[self._tfs_to_check].applymap(lambda x: '▲' if x > 0 else '▼').apply(lambda x: ','.join(x),
            #                                                                                       axis=1).tolist()
            fig.data[0].text = [f'Strat: {num} | {combo if len(combo) else "-"} | {time_cont}' for num, combo, time_cont in
                                zip(df['thestrat_num'].values.tolist(),
                                    df['thestrat_combo'].values.tolist(),
                                    tfs_cont_str)]
        else:
            fig.data[0].text = [f'Strat: {num}, {combo}' for num, combo, time_cont in
                                zip(df['thestrat_num'].values.tolist(),
                                    df['thestrat_combo'].values.tolist())
                                # df['thestrat_combo'].values.tolist())
                                ]

        # trace = go.Scatter(x=ra.index, y=ra, name=self.name, line_color=self.color, line_width=1)
        # fig.add_trace(trace, row=self.plot_loc[0], col=self.plot_loc[1])
        return fig
