from DataProcessing.data_utils import get_data_providers, adjust_plot_start_datetime, prepare_data, get_coin_ohlc
from DataProcessing.data_consts import COINS
from datetime import datetime
from AdvancedAnalytics.strategy_RSI_BB import add_indicators
import pytz


def get_latest_buy_sell(tf='1H', lookahead=14):
    print('tf =', tf, 'lookahead =', lookahead)
    filter_datetime = adjust_plot_start_datetime(tf)
    providers = get_data_providers()
    df_prices, df_agg = prepare_data(providers, filter_datetime)
    updated_data_time = df_prices.index[-1]  # .astimezone(None)

    updated_now_time = datetime.now(tz=pytz.timezone('Israel'))  # utcnow()
    diff_min = (updated_now_time - updated_data_time).seconds / 60
    tolerance_minute = 3
    if diff_min > tolerance_minute:
        print('updated_data_time', updated_data_time)
        print('updated_now_time', updated_now_time)
        print('Warning!! Data is not update to date!')

    n_candle = -1  # last updated candle, -1 updates on hour basis, so on open hour it will not be correct
    if n_candle == -1:
        print("Looking on Latest candle - may not be updates as it builds")
    print('n_candle', n_candle)
    cnt_total_cmds = 0
    # print('Infering data ts:', df_prices.index[n_candle])
    buy_lst = []
    sell_lst = []
    for coin in COINS:
        df = get_coin_ohlc(df_prices, coin, tf)
        df = add_indicators(df, lookahead)
        # 'BUY_ALGO_BBRSI', 'SELL_ALGO_BBRSI', 'SELL_WIN_STOP', 'SELL_LOSE_STOP'

        ts = df.index[n_candle]
        if df.iloc[n_candle]['BUY_ALGO_BBRSI']:
            # print(ts, 'BUY_ALGO_BBRSI', coin)
            cnt_total_cmds += 1
            buy_lst.append(coin)
        # sell
        if df.iloc[n_candle]['SELL_ALGO_BBRSI']:
            # print(ts, 'SELL_ALGO_BBRSI', coin)

            sell_lst.append(coin)
        # stoplosses
        if df.iloc[n_candle]['SELL_WIN_STOP']:
            # print(ts, 'SELL_WIN_STOP', coin)

            sell_lst.append(coin)
        if df.iloc[n_candle]['SELL_LOSE_STOP']:
            # print(ts, 'SELL_LOSE_STOP', coin)

            sell_lst.append(coin)
    print(updated_data_time)
    print(buy_lst)
    print(sell_lst)

    # txt = f"Total commands n_Buy: {len(buy_lst)}"
    txt_buy_lst = ','.join(buy_lst)
    txt_sell_lst = ','.join(sell_lst)
    txt = f"Buy: {txt_buy_lst}" if len(txt_buy_lst) > 0 else ""
    txt += f"Sell: {txt_sell_lst}" if len(txt_sell_lst) > 0 else ""
    print(txt)
    from Utils.notify import SMSNotify

    # sms = SMSNotify()
    # sms.send_sms(txt)


if __name__ == '__main__':
    get_latest_buy_sell(tf='1H', lookahead=14)
    # df.tail()
