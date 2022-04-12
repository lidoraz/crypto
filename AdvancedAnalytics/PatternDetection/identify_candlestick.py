import numpy as np
from .candle_rankings import candle_rankings
import talib
import numpy as np
from itertools import compress


def recognize_candles(df):
    """
    Recognizes candlestick patterns and appends 2 additional columns to df;
    1st - Best Performance candlestick pattern matched by www.thepatternsite.com
    2nd - # of matched patterns
    """

    op = df['open'].astype(float)
    hi = df['high'].astype(float)
    lo = df['low'].astype(float)
    cl = df['close'].astype(float)

    patterns = talib.get_function_groups()['Pattern Recognition']

    # patterns not found in the patternsite.com
    exclude_items = ('CDLCOUNTERATTACK',
                     'CDLLONGLINE',
                     'CDLSHORTLINE',
                     'CDLSTALLEDPATTERN',
                     'CDLKICKINGBYLENGTH')

    patterns = [pattern for pattern in patterns if pattern not in exclude_items]

    # create columns for each candle
    for pattern in patterns:
        # below is same as;
        # df["CDL3LINESTRIKE"] = talib.CDL3LINESTRIKE(op, hi, lo, cl)
        df[pattern] = getattr(talib, pattern)(op, hi, lo, cl)

    def apply_on_patterns(row):
        def convert_to_pattern_trend(k, v):
            if v > 0:
                return k + '_Bull'
            elif v < 0:
                return k + '_Bear'

        patterns = row[row != 0]
        if len(patterns) == 0:
            return None, None
        k, v = list(zip(*patterns.to_dict().items()))
        if len(patterns) == 1:  # not zero there is signal
            k_with_trend = convert_to_pattern_trend(k[0], v[0])
            return k_with_trend, candle_rankings[k_with_trend]
        else:  # larger than 1
            k_with_trend = [convert_to_pattern_trend(k, v) for k, v in zip(k, v)]
            ranking = [candle_rankings[k] for k in k_with_trend]
            return k_with_trend[np.argmin(ranking)], ranking[np.argmin(ranking)]

    res = df[patterns].apply(apply_on_patterns, axis=1, result_type='expand')
    res.columns = ['pattern', 'ranking']

    def define_trend(x):
        if x is None:
            return 0
        if x.endswith('_Bull'):
            return 1
        else:
            return -1

    res['trend'] = res['pattern'].apply(define_trend)
    res['pattern'] = res['pattern'].apply(lambda x: x.split('_')[0][3:] if x is not None else x)

    return res
    #
    # df['pattern'] = np.nan
    # df['match_count'] = np.nan
    # for index, row in df.iterrows():
    #
    #     # no pattern found
    #     if len(row[candle_names]) - sum(row[candle_names] == 0) == 0:
    #         df.loc[index,'pattern'] = "NO_PATTERN"
    #         df.loc[index, 'match_count'] = 0
    #     # single pattern found
    #     elif len(row[candle_names]) - sum(row[candle_names] == 0) == 1:
    #         # bull pattern 100 or 200
    #         if any(row[candle_names].values > 0):
    #             pattern = list(compress(row[candle_names].keys(), row[candle_names].values != 0))[0] + '_Bull'
    #             df.loc[index, 'pattern'] = pattern
    #             df.loc[index, 'match_count'] = 1
    #         # bear pattern -100 or -200
    #         else:
    #             pattern = list(compress(row[candle_names].keys(), row[candle_names].values != 0))[0] + '_Bear'
    #             df.loc[index, 'pattern'] = pattern
    #             df.loc[index, 'match_count'] = 1
    #     # multiple patterns matched -- select best performance
    #     else:
    #         # filter out pattern names from bool list of values
    #         patterns = list(compress(row[candle_names].keys(), row[candle_names].values != 0))
    #         container = []
    #         for pattern in patterns:
    #             if row[pattern] > 0:
    #                 container.append(pattern + '_Bull')
    #             else:
    #                 container.append(pattern + '_Bear')
    #         rank_list = [candle_rankings[p] for p in container]
    #         if len(rank_list) == len(container):
    #             rank_index_best = rank_list.index(min(rank_list))
    #             df.loc[index, 'pattern'] = container[rank_index_best]
    #             df.loc[index, 'match_count'] = len(container) # how many patterns were matched.
    # # clean up candle columns
    # df['pattern_strength'] = df['pattern'].apply(lambda x: 100 - candle_rankings[x] if x!= 'NO_PATTERN' else None)
    # cols_to_drop = patterns  #+ list(exclude_items)
    # #
    # df.drop(cols_to_drop, axis=1, inplace=True)
    # df
    # return df
