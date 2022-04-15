import numpy as np
from .candle_rankings import candle_rankings
import talib

# Best Performance candlestick pattern matched by www.thepatternsite.com
def recognize_candles(df):
    """
    Recognizes candlestick patterns and Returns a df with these columns:
    'best_pattern - best pattern found by strength based by www.thepatternsite.com'
    'best_trend - best strength pattern multiplied by bull / bear (1, -1)
    'n_patterns - number of matching patterns found'
    """
    df = df.copy()
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

    for pattern in patterns:
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
            return 'na', None, 0
        k, v = list(zip(*patterns.to_dict().items()))
        if len(patterns) == 1:  # not zero there is signal
            k_with_trend = convert_to_pattern_trend(k[0], v[0])
            return k_with_trend, candle_rankings[k_with_trend], 1
        else:  # larger than 1
            k_with_trend = [convert_to_pattern_trend(k, v) for k, v in zip(k, v)]
            ranking = [candle_rankings[k] for k in k_with_trend]
            return k_with_trend[np.argmin(ranking)], ranking[np.argmin(ranking)], len(patterns)

    res = df[patterns].apply(apply_on_patterns, axis=1, result_type='expand')
    res.columns = ['best_pattern', 'best_ranking', 'n_patterns']

    def define_trend(x):
        if x.endswith('_Bull'):
            return 1
        elif x.endswith('_Bear'):
            return -1
        else:
            return 0

    res['best_trend'] = res['best_pattern'].apply(define_trend)
    res['best_pattern'] = res['best_pattern'].apply(lambda x: x.split('_')[0][3:] if x is not None else x)

    return res
