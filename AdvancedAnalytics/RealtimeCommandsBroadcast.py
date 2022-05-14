from Strategy.DataWrap import CryptoData
from Strategy.Strategies import BB, RSIBB
from Utils.utils import WaitToMinEveryHour
from datetime import datetime
from Utils.notify import TelegramBot
import pandas as pd
from dateutil import tz
#
prod = False
if prod:
    print('@-------> prod True!!!!')


def get_latest_buy_sell(data_wrapper, time_now_minus_tf, symbols, stratgy, tf='1H'):
    # on crypto it updated every 1 min so no problem
    # has saftey mechanism from datawrapper crypto live if db is not updated!
    # Implmenet with act buy, so it will be generalized and support stoplosses
    n_candle = -1  # last updated candle, -1 updates on hour basis, so on open hour it will not be correct
    buy_lst = []
    sell_lst = []
    for coin in symbols:
        # TODO: add to get_data option to filter out for most recent data, not only on init class.
        df = data_wrapper.get_data(coin, tf)
        # TODO: get the data, and check its ts if it matches current machine ts to make sure we are sending correct ts.
        if df is None:
            print('Skipping:', coin, tf)
            continue
        df = stratgy.add_indicators(df)
        df = df[:time_now_minus_tf]  # filter out

        last_row = df.iloc[n_candle]
        ts = df.index[-1]
        buy_vars = stratgy.act_buy(0, last_row)
        # print(ts, coin, tf)
        #            return {'buy_idx': buy_idx,
        #                     'buy_price': buy_price,
        #                     'sell_price_win_stop': sell_price_win_stop,
        #                     'sell_price_lose_stop': sell_price_lose_stop}
        if buy_vars:
            buy_vars['coin'] = coin
            buy_vars['ts'] = ts
            buy_lst.append(buy_vars)

        if last_row['SELL_ALGO']:
            sell_lst.append(dict(coin=coin, sell_price=last_row['close'], ts=ts))

    return buy_lst, sell_lst


def handle_buy_sell(title_strategy, buy_lst, sell_lst, tb_notify):
    TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime

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
    timeframe, trigger_minutes = handle_args()
    print(f'Broadcasting every {timeframe}, at {trigger_minutes} min every hour')

    data_wrapper = CryptoData.get_wrapper(live=True, start_date='2022-05-01')
    symbols = data_wrapper.get_symbols()
    strategy = BB()
    # strategy = RSIBB(dict(RSIBB_n_rsi_soon=5, RSIBB_ind_ahead=14, RSIBB_BB_std=2.5))

    tb_notify = TelegramBot()
    buy_change = set()
    sell_change = set()
    owned_coins = set()
    wait = WaitToMinEveryHour(trigger_minutes)
    title_strategy = f'{strategy}({timeframe})'
    str_symbols = ", ".join(symbols)
    start_msg = f'{title_strategy}\nFollowing: {str_symbols}'
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
        handle_buy_sell(title_strategy, buy_notify, sell_notify, tb_notify)
