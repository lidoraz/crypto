from AdvancedAnalytics.Strategy.DataWrap import CryptoData
from AdvancedAnalytics.Strategy.DataWrap.CryptoData import CryptoDataLive
from AdvancedAnalytics.Strategy.Strategies import BB
from datetime import datetime
import pytz


def get_latest_buy_sell(tf='1H', lookahead=14):
    print('tf =', tf, 'lookahead =', lookahead)
    data_wrapper = CryptoDataLive.get_wrapper(start_date='2022-04-25')
    symbols = data_wrapper.get_symbols()

    latest_data_ts = data_wrapper.get_latest_ts()  # .astimezone(None)

    latest_ts = datetime.now(tz=pytz.timezone('Israel'))  # utcnow()
    diff_min = (latest_ts - latest_data_ts).seconds / 60
    tolerance_minute = 3
    if diff_min > tolerance_minute:
        print('latest_data_ts', latest_data_ts)
        print('latest_ts', latest_ts)
        print('Warning!! Data is not update to date!')

    n_candle = -1  # last updated candle, -1 updates on hour basis, so on open hour it will not be correct
    if n_candle == -1:
        print("Looking on Latest candle - may not be updates as it builds")
    print('n_candle', n_candle)
    cnt_total_cmds = 0
    # print('Infering data ts:', df_prices.index[n_candle])
    buy_lst = []
    sell_lst = []
    bb_stratgy = BB()
    for coin in symbols:
        df = data_wrapper.get_data(coin, tf)
        df = bb_stratgy.add_indicators(df)
        # last_idx = df.iloc[-1].index
        last_row = df.iloc[n_candle]
        buy_vars = bb_stratgy.act_buy(0, last_row)
        # if buy_vars:
        #     {'buy_idx': buy_idx,
        #      'sell_price_win_stop': sell_price_win_stop,
        #      'sell_price_lose_stop': sell_price_lose_stop}
        ts = df.index[n_candle]

        if df.iloc[n_candle]['BUY_ALGO']:
            # print(ts, 'BUY_ALGO_BBRSI', coin)
            cnt_total_cmds += 1
            buy_lst.append((coin, last_row['close']))
        # sell
        if df.iloc[n_candle]['SELL_ALGO']:
            print(ts, 'SELL_ALGO_BBRSI', coin)
            sell_lst.append((coin, last_row['close']))
            # stoplosses
        # TODO: Should support also stop losses.
        # if df.iloc[n_candle]['SELL_WIN_STOP']:
        #     print(ts, 'SELL_WIN_STOP', coin)
        #     sell_lst.append(coin)
        # if df.iloc[n_candle]['SELL_LOSE_STOP']:
        #     print(ts, 'SELL_LOSE_STOP', coin)
        #     sell_lst.append(coin)
    # print(updated_data_time)
    # print(buy_lst)
    # print(sell_lst)

    # txt = f"Total commands n_Buy: {len(buy_lst)}"
    txt_buy_lst = ','.join([f'{x[0]},{x[1]}' for x in buy_lst])
    txt_sell_lst = ','.join([f'{x[0]},{x[1]}' for x in sell_lst])
    txt = f"Buy: {txt_buy_lst}" if len(txt_buy_lst) > 0 else ""
    txt += f"Sell: {txt_sell_lst}" if len(txt_sell_lst) > 0 else ""
    print(txt)
    from Utils.notify import SMSNotify

    # sms = SMSNotify()
    # sms.send_sms(txt)


if __name__ == '__main__':
    get_latest_buy_sell(tf='1H', lookahead=14)
    # df.tail()
