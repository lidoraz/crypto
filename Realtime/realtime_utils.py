import pandas as pd
from datetime import datetime

TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime


def handle_args():
    import sys
    args = sys.argv[1:]
    usage = 'usage: {15min, 1h} (prod) (start_msg)'
    print(usage)
    if len(args) >= 1:
        prod = False
        show_start_msg = False
        if args[0].lower() == '15min':
            timeframe = '15min'
            trigger_minutes = [0, 15, 30, 45]
        elif args[0].lower() == '1h':
            timeframe = '1h'
            trigger_minutes = [0]
        else:
            raise ValueError(usage)
        args = args[1:]
        if 'prod' in args:
            prod = True
        if 'start_msg' in args:
            show_start_msg = True
        params = dict(timeframe=timeframe, trigger_minutes=trigger_minutes, prod=prod, show_start_msg=show_start_msg)
        print('******* Realtime Params ********\n'
              f'Fetch every {timeframe}\n'
              f'At {trigger_minutes} min every hour\n'
              f'PROD={prod}\n'
              f'show_msg={show_start_msg}\n',
              '******* ******* ******* ********\n')
        return params
    raise ValueError(usage)


def _upsample_from_1m_curr_dt(df, tf, dt_now):
    df = pd.concat([
        df['open'].resample(tf, origin=dt_now).first(),
        df['close'].resample(tf, origin=dt_now).last(),
        df['low'].resample(tf, origin=dt_now).min(),
        df['high'].resample(tf, origin=dt_now).max(),
        df['volume'].resample(tf, origin=dt_now).sum()], axis=1)
    return df


def get_latest_buy_sell(data_wrapper, symbols, strategy, tf='1H', n_candles_to_get=150, use_closed=True):
    """ gets latest coins to buy or sell based on strategy.
        Provides support with use_closed to filter out most recent unclosed candle
        It is designed to be used when a timeframe has been closed, such as right after a new hour has started
        For experimental option, use_closed can be False, and then the data will be resampled to past selected TF.
    """
    buy_lst = []
    sell_lst = []
    checked_coins = []
    dt_now = pd.to_datetime(datetime.utcnow(), utc=True).tz_convert('Israel')
    time_now_minus_tf = dt_now - pd.to_timedelta(tf)
    start_date = str(dt_now.date() - pd.to_timedelta(tf) * n_candles_to_get)
    for coin in symbols:
        if use_closed:
            df = data_wrapper.get_data(coin, tf, start_date)
        else:
            df = data_wrapper.get_data(coin, '1T', start_date)
            df = _upsample_from_1m_curr_dt(df, tf, dt_now)
        if df is None:
            print('Skipping:', coin, tf)
            continue

        df = strategy.add_indicators(df)
        if use_closed:  # filter out to last closed candle
            df = df[:time_now_minus_tf]

        last_row = df.iloc[-1]
        ts = df.index[-1]
        checked_coins.append(coin)

        buy_vars = strategy.act_buy(0, last_row)
        if buy_vars:
            buy_lst.append(dict(coin=coin,
                                buy_price=last_row['close'],
                                buy_pct_change=last_row['pct_close'],
                                sell_price_win_stop=buy_vars['sell_price_win_stop'],
                                sell_price_lose_stop=buy_vars['sell_price_lose_stop'],
                                ts=ts))
        if last_row['SELL_ALGO']:
            sell_lst.append(dict(coin=coin,
                                 sell_price=last_row['close'],
                                 sell_pct_change=last_row['pct_close'],
                                 ts=ts))
    print(f'At: {dt_now.strftime(TIME_CONV)} - Checked {len(checked_coins)} coins,'
          f' #Buy={len(buy_lst)} / #Sell={len(sell_lst)}, use_closed={use_closed}')
    return buy_lst, sell_lst

