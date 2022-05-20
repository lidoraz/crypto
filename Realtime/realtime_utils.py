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


def get_latest_buy_sell(data_wrapper, symbols, strategy, tf='1H', n_candles_to_get=150, use_closed=True):
    """ gets latest coins to buy or sell based on strategy.
        Provides support with use_closed to filter out most recent unclosed candle
        It is designed to be used when a timeframe has been closed, such as right after a new hour has started
        For experimental option, use_closed can be False
    """
    buy_lst = []
    sell_lst = []
    checked_coins = []
    dt_now = pd.to_datetime(datetime.utcnow(), utc=True).tz_convert('Israel')
    time_now_minus_tf = dt_now - pd.to_timedelta(tf)
    start_date = str(dt_now.date() - pd.to_timedelta(tf) * n_candles_to_get)
    for coin in symbols:
        df = data_wrapper.get_data(coin, tf, start_date)
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
                                sell_price_win_stop=buy_vars['sell_price_win_stop'],
                                sell_price_lose_stop=buy_vars['sell_price_lose_stop'],
                                ts=ts))
        if last_row['SELL_ALGO']:
            sell_lst.append(dict(coin=coin,
                                 sell_price=last_row['close'],
                                 ts=ts))
    print(f'At: {dt_now.strftime(TIME_CONV)} - Checked {len(checked_coins)} coins,'
          f' #Buy={len(buy_lst)} / #Sell={len(sell_lst)}, use_closed={use_closed}')
    return buy_lst, sell_lst


def handle_buy_sell(title_strategy, buy_lst, sell_lst, tb_notify, prod=False):

    def extract_to_txt_buy(lst):
        return [f"{x['coin']}: {x['buy_price']} ({x['sell_price_win_stop']:.2f}, {x['sell_price_lose_stop']:.2f})" for x
                in lst]

    def extract_to_txt_sell(lst):
        return [f"{x['coin']}: {x['sell_price']} ({x['ts'].strftime('%H:%M')})" for x in lst]

    buy_txt = ''
    txt = ''
    if len(buy_lst):
        str_lst = extract_to_txt_buy(buy_lst)
        buy_txt = '\n'.join(str_lst)
        txt += f'<b>Buy:</b> BuyPrice (StopProfit, stopLoss)\n{buy_txt}'
    if len(sell_lst):
        txt += '\n' if len(buy_txt) else ''  # add newline if has buy
        str_lst = extract_to_txt_sell(sell_lst)
        sell_txt = '\n'.join(str_lst)
        txt += f'<b>Sell:</b> SellPrice (ts)\n{sell_txt}'

    if len(txt):
        # dt = datetime.now().strftime(TIME_CONV)
        txt = f'{title_strategy}:\n' + txt
        print(txt)
        if prod:
            tb_notify.send(txt)
