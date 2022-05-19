from Data import CryptoData
from Backtesting.Strategies import RSIBB
from Utils.utils import WaitToMinEveryHour
from datetime import datetime
from Utils.notify import TelegramBot
import pandas as pd
from dateutil import tz
from Realtime.realtime_utils import get_latest_buy_sell, handle_buy_sell


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
        print('******* Broadcast Params ********\n'
              f'Broadcasting every {timeframe}\n'
              f'At {trigger_minutes} min every hour\n'
              f'PROD={prod}\n'
              f'show_msg={show_start_msg}\n',
              '******* ******* ******* ********\n')
        return params
    raise ValueError(usage)


def run_broadcast():
    parsed_args = handle_args()
    timeframe = parsed_args['timeframe']
    trigger_minutes = parsed_args['trigger_minutes']
    prod = parsed_args['prod']
    show_start_msg = parsed_args['show_start_msg']
    data_wrapper = CryptoData.get_wrapper(live=True, start_date='2022-05-01')
    symbols = data_wrapper.get_symbols()
    # strategy = BB()
    strategy_params = dict(RSIBB_n_rsi_soon=7,
                           RSIBB_rsi_ahead=16,
                           RSIBB_bb_ahead=12,
                           RSIBB_rsi_low=30,
                           RSIBB_rsi_high=70,
                           RSIBB_bb_std=2.16)
    strategy = RSIBB(strategy_params)

    tb_notify = TelegramBot()
    buy_change = set()
    sell_change = set()
    owned_coins = set()
    wait = WaitToMinEveryHour(trigger_minutes)
    title_strategy = f'{strategy}({timeframe})'
    str_symbols = ", ".join(symbols)
    start_msg = f'{title_strategy}\nFollowing: {str_symbols}'
    if show_start_msg:
        print(start_msg)
        if prod:
            tb_notify.send(start_msg)

    while True:
        if prod:
            wait.wait()
        time_now_minus_tf = datetime.now(tz.gettz('Israel')) - pd.to_timedelta(timeframe)
        buy_details_lst, sell_details_lst = get_latest_buy_sell(data_wrapper, time_now_minus_tf, symbols, strategy,
                                                                tf=timeframe)

        buy_curr = set([detail['coin'] for detail in buy_details_lst])
        notify_coins = buy_curr - buy_change
        buy_change = buy_curr
        buy_notify = [detail for detail in buy_details_lst if detail['coin'] in notify_coins]

        sell_curr = set([detail['coin'] for detail in sell_details_lst])
        notify_coins = sell_curr - sell_change
        sell_change = sell_curr
        sell_notify = [detail for detail in sell_details_lst if detail['coin'] in notify_coins]

        print('-> Getting time_now_minus_tf =', time_now_minus_tf)
        print('buy_lst', buy_details_lst)
        # print('buy_change:', buy_change)
        print('buy_notify:', buy_notify)
        print('sell_lst', sell_details_lst)
        # print('sell_change:', sell_change)
        print('sell_notify:', sell_notify)
        handle_buy_sell(title_strategy, buy_notify, sell_notify, tb_notify, prod)


# Test validity of this algorithm, and how to use it.
# looks on the bright side that the async code works well and did not crash during weekend.
if __name__ == '__main__':
    run_broadcast()
