from AdvancedAnalytics.Strategy.DataWrap import CryptoData
from AdvancedAnalytics.Strategy.Strategies import BB, RSIBB
from AdvancedAnalytics.RealtimeCommandsBroadcast import get_latest_buy_sell
from Utils.utils import WaitToMinEveryHour
from datetime import datetime
from Utils.notify import TelegramBot
import pandas as pd
from dateutil import tz
import ccxt
import os

prod = False


def handle_buy_sell(buy_lst, sell_lst, exchange):
    TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime

    if len(buy_lst):
        print(buy_lst)
    if len(sell_lst):
        print(sell_lst)


def handle_args():
    import sys
    args = sys.argv[1:]
    usage = 'usage: 15min or 1h'
    if len(args) == 1:
        if args[0].lower() == '15min':
            trigger_minutes = [0, 15, 30, 45]
            return '15min', trigger_minutes
        if args[0].lower() == '1h':
            trigger_minutes = [0]
            return '1h', trigger_minutes
    print(usage)
    exit(-1)


# Test validity of this algorithm, and how to use it.
# looks on the bright side that the async code works well and did not crash during weekend.
if __name__ == '__main__':

    exchange = ccxt.binance({
        # 'apiKey': os.environ.get('BINANCE_API'),
        # 'secret': os.environ.get('BINANCE_SECRET'),
        'enableRateLimit': True,
    })

    timeframe, trigger_minutes = handle_args()
    print(f'Broadcasting every {timeframe}, at {trigger_minutes} min every hour')

    data_wrapper = CryptoData.get_wrapper(live=True, start_date='2022-05-01')
    # TODO: NEED TO FILTER OUT SYMBOLS, first run on very minimal set -> 5 coins at most from binance.
    symbols = data_wrapper.get_symbols()
    # generated 340% profit after 1.5 month.
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
    print(start_msg)
    # if prod:
    #     tb_notify.send(start_msg)

    while True:
        if prod:
            wait.wait()
        time_now_minus_tf = datetime.now(tz.gettz('Israel')) - pd.to_timedelta(timeframe)
        buy_details_lst, sell_details_lst = get_latest_buy_sell(data_wrapper, time_now_minus_tf, symbols, strategy,
                                                                tf=timeframe)

        buy_curr = set([detail['coin'] for detail in buy_details_lst])
        owned_coins.add(buy_curr)
        # notify_coins = buy_curr - buy_change
        # buy_change = buy_curr
        # buy_notify = [detail for detail in buy_details_lst if detail['coin'] in notify_coins]
        #
        # sell_curr = set([detail['coin'] for detail in sell_details_lst])
        # notify_coins = sell_curr - sell_change
        # sell_change = sell_curr
        # sell_notify = [detail for detail in sell_details_lst if detail['coin'] in notify_coins]
        #
        # owned_coins.add(buy_notify)
        # sell_notify = [c for c in sell_notify if c in owned_coins]
        # print('-> Getting time_now_minus_tf =', time_now_minus_tf)
        # print('buy_lst', buy_details_lst)
        # # print('buy_change:', buy_change)
        # print('buy_notify:', buy_notify)
        # print('sell_lst', sell_details_lst)
        # # print('sell_change:', sell_change)
        # print('sell_notify:', sell_notify)
        handle_buy_sell(title_strategy, buy_notify, sell_notify, tb_notify)
