from Strategy.DataWrap import CryptoData
from Strategy.Strategies import BB
from Utils.utils import WaitToMinEveryHour
from datetime import datetime


def get_latest_buy_sell(data_wrapper, symbols, stratgy, tf='1H'):
    # on crypto it updated every 1 min so no problem
    # has saftey mechanism from datawrapper crypto live if db is not updated!
    # Implmenet with act buy, so it will be generalized and support stoplosses
    n_candle = -1  # last updated candle, -1 updates on hour basis, so on open hour it will not be correct
    buy_lst = []
    sell_lst = []
    for coin in symbols:
        # TODO: add to get_data option to filter out for most recent data, not only on init class.
        df = data_wrapper.get_data(coin, tf)
        # TODO rework this.
        import pandas as pd
        from dateutil import tz
        now_minus_tf = datetime.now(tz.gettz('Israel')) - pd.to_timedelta(tf)
        df = df[:now_minus_tf]
        # now_minus_tf_aligned = pd.to_datetime(now_minus_tf.replace(minute=0, second=0, microsecond=0))

        # TODO: get the data, and check its ts if it matches current machine ts to make sure we are sending correct ts.
        if df is None:
            print('Skipping:', coin, tf)
            continue
        df = stratgy.add_indicators(df)

        last_row = df.iloc[n_candle]
        ts = df.index[-1]
        print(ts, coin, tf)
        buy_vars = stratgy.act_buy(0, last_row)  # last row
        #            return {'buy_idx': buy_idx,
        #                     'buy_price': buy_price,
        #                     'sell_price_win_stop': sell_price_win_stop,
        #                     'sell_price_lose_stop': sell_price_lose_stop}
        if buy_vars:
            buy_vars['coin'] = coin
            buy_vars['ts'] = ts
            buy_lst.append(buy_vars)

        if last_row['SELL_ALGO']:
            sell_lst.append(dict(coin=coin, buy_price=last_row['close'], ts=ts))

    return buy_lst, sell_lst


def handle_buy_sell(strategy, buy_lst, sell_lst, tb_notify):
    TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime

    def extract_to_txt_sell(lst):
        return [f"{x['coin']}, {x['price']}, ({x['ts'].strftime('%H:%M')})" for x in lst]

    def extract_to_txt_buy(lst):
        return [f"{x['coin']}, P:{x['buy_price']} (T:{x['sell_price_win_stop']}, B:{x['sell_price_lose_stop']})" for x
                in lst]

    buy_txt = ''
    txt = ''
    if len(buy_lst):
        str_lst = extract_to_txt_buy(buy_lst)
        buy_txt = '\n'.join(str_lst)
        txt += f'<b>Buy:</b>\n{buy_txt}\n'
    if len(sell_lst):
        str_lst = extract_to_txt_sell(sell_lst)
        sell_txt = '\n'.join(str_lst)
        if len(buy_txt):
            txt += f'\n<b>Sell:</b>\n{sell_txt}'
        else:
            txt += f'<b>Sell:</b>\n{sell_txt}'
    if len(txt):
        # dt = datetime.now().strftime(TIME_CONV)
        txt = f'{strategy}:\n' + txt
        print(txt)
        tb_notify.send(txt)


if __name__ == '__main__':
    data_wrapper = CryptoData.get_wrapper(live=True, start_date='2022-05-01')
    symbols = data_wrapper.get_symbols()
    strategy = BB()
    timeframe = '1H'  # '15Min'  # '1H'
    from Utils.notify import TelegramBot

    tb_notify = TelegramBot()
    buy_change = set()
    sell_change = set()
    buy_notify = []
    sell_notify = []
    print(strategy)
    owned_coins = set()
    # trigger_minutes = [0, 15, 30, 45]
    trigger_minutes = [1]
    # trigger_minutes = range(60)
    sell_only_if_owned = True
    wait = WaitToMinEveryHour(trigger_minutes)
    print('Starting...')
    while True:
        wait.wait()
        # Test validty of this algorithm, and how to use it. looks on the brightside that the async code works well and did not crash during weekend.

        buy_details_lst, sell_details_lst = get_latest_buy_sell(data_wrapper, symbols, strategy, tf=timeframe)
        print(datetime.now())
        print('buy_lst', buy_details_lst)
        print('sell_lst', sell_details_lst)

        buy_curr = set([detail['coin'] for detail in buy_details_lst])
        notify_coins = buy_curr - buy_change
        buy_notify = [detail for detail in buy_details_lst if detail['coin'] in notify_coins]
        buy_change = buy_curr

        sell_curr = set([detail['coin'] for detail in sell_details_lst])
        notify_coins = sell_curr - sell_change
        sell_notify = [detail for detail in sell_details_lst if detail['coin'] in notify_coins]
        sell_change = sell_curr

        print('buy_change:', buy_change)
        print('sell_change:', sell_change)

        if sell_only_if_owned:
            sell_notify = [c for c in sell_notify if c['coin'] in owned_coins]
        print('buy_notify:', buy_notify)
        print('sell_notify:', sell_notify)

        handle_buy_sell(strategy, buy_notify, sell_notify, tb_notify)

        # TODO Better to do this async
