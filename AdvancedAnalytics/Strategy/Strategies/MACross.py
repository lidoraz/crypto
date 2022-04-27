# TODO: For example, a simple trading strategy may be a moving average crossover whereby a short-term moving average
# crosses above or below a long-term moving average.
from AdvancedAnalytics.Strategy.DataWrap import NasdaqData
from Indicators import SMA


def add_indicators(df, short=25, long=100):
    # n_rsi_soon: when RSI has alert, how forward to notify that alert
    ind_short = SMA(short)
    ind_long = SMA(long)
    df = df.join(ind_short.calc(df))
    df = df.join(ind_long.calc(df))
    df = df.dropna()

    df['BUY_ALGO'] = df[f'SMA_{short}'] > df[f'SMA_{long}']  # buy
    df['SELL_ALGO'] = df[f'SMA_{short}'] < df[f'SMA_{long}']  # sell

    # # add stop-loss
    # # Handled during the DF iter rows
    # df['SELL_WIN_STOP'] = df[f'BBTOP_{ind_ahead}'] < df['close']
    # df['SELL_LOSE_STOP'] = df[f'BBBOT_{ind_ahead}'] > df['close']
    return df


if __name__ == '__main__':
    data_wrapper = NasdaqData.get_wrapper(start_date='2016-01-01')
    df = data_wrapper.get_data('AAPL', tf='1D')
    add_indicators(df)
