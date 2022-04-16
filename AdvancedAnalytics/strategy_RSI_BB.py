from DataProcessing.data_utils import get_data_providers, adjust_plot_start_datetime, prepare_data, get_coin_ohlc
from DataProcessing.data_consts import COINS
from Plots.traces import calc_pct_change
import pandas as pd
from DataProcessing.data_utils import extract_volume

from Plots.Indicators import RSI, BollingerBands, SMA


def mark_enter_exit_points(tf):
    filter_datetime = adjust_plot_start_datetime(tf)
    providers = get_data_providers()
    df_prices, df_hourly = prepare_data(providers, filter_datetime)

    pct_threshold = 0  # 15.0
    lookback = '1H'
    rsi_lookahead = 14
    # ,'1H'
    res = []

    ind_rsi = RSI(rsi_lookahead)
    ind_bb = BollingerBands(rsi_lookahead)
    ind_sma = SMA(100)
    # TODO: RSI divergence  or MaCD divergence
    sum_pct = 0
    for coin in COINS:
        # TODO: https://www.youtube.com/watch?v=yBjk9r9igcQ

        # TODO: add indicators for - oversold before -> RSI < 30 for 5 candles
        # BUY ENTRY: First candle that closes on the middle BB, soon after RSI was < 30
        # SELL ENTRY: First candle that close below the middle BB, soon after RSI was > 70
        # GOOD PORTION OF THE CANDLE HAS TO CLOSE ABOVE / BELOW the middle BB
        # STOP LOSS SETS ON THE LOWER BB
        # STOP LOSS SETS ON THE HIGHER BB on SELL
        # _, volume = extract_volume(df_agg=df_hourly, coin=coin, interval=tf)
        # df_coin = df_prices[coin]
        df = get_coin_ohlc(df_prices, coin, tf)
        # prices = coin_ohlc['close']
        df = df.join(ind_rsi.calc(df['close']))
        df = df.join(ind_bb.calc(df['close']))
        df = df.join(ind_sma.calc(df['close']))

        df = df.dropna()

        rsi_col = f"RSI_{rsi_lookahead}"

        df['rsi_70'] = df[rsi_col] > 70
        df['rsi_30'] = df[rsi_col] < 30
        df['OVER_BB'] = df[f'BBTOP_{rsi_lookahead}'] < df['close']
        df['BELOW_BB'] = df[f'BBBOT_{rsi_lookahead}'] > df['close']

        # buy condition
        n_rsi_soon = 10
        df[f'b_30_n_{n_rsi_soon}'] = df['rsi_30'].rolling(n_rsi_soon).sum() > 0
        df['passed_mid_bb'] = df['close'] >= df[f'SMA_{rsi_lookahead}']

        # sell condition
        df[f'u_70_n_{n_rsi_soon}'] = df['rsi_70'].rolling(n_rsi_soon).sum() > 0
        df[f'below_mid_bb'] = df['close'] < df[f'SMA_{rsi_lookahead}']

        df['buy'] = df[f'b_30_n_{n_rsi_soon}'] & df['passed_mid_bb']
        df['sell'] = df[f'u_70_n_{n_rsi_soon}'] & df['below_mid_bb']

        # print(df.columns)
        # has passed RSI 70

        # has passed RSI 30
        # print(df.tail())

        # print(coin, df['rsi_70'].sum(), df['rsi_30'].sum())

        buy_idxes = list(df[df['buy']].index)
        sell_idxes = list(df[df['sell']].index)

        # last_sell = df.index[0]
        # last_buy = df.index[0]
        found = False

        for sell_idx in sell_idxes:
            if found:
                break
            for buy_idx in buy_idxes:
                if found:
                    break
                if sell_idx > buy_idx:
                    # if last_buy == buy_idx or last_sell == sell_idx:
                    #     continue
                    buy_price = df['close'].loc[buy_idx]
                    sell_price = df['close'].loc[sell_idx]
                    profit_pct = (sell_price / buy_price) - 1
                    # There's ▲: \u25B2 and ▼: \u25BC
                    if profit_pct > 0:
                        print('Trade:', coin, buy_idx, sell_idx, f'{profit_pct:.2%} $ \u25B2')
                    else:
                        print('Trade:', coin, buy_idx, sell_idx, f'{profit_pct:.2%} . \u25BC')
                    # print(buy_price, sell_price)
                    sum_pct += profit_pct
                    found = True

        # if len(buy_idx) > 0:
        #     print(coin)
        #     print('buy_idx', buy_idx)
        #     print('sell_idx', sell_idx)
        # pct = calc_pct_change(df_coin, lookback)
        # current_granular_change = pct.tail(1)
        # dt = current_granular_change.index[0]
        # val = round(current_granular_change[0], 3)
        # if abs(val) > pct_threshold:
        #     res.append({'dt': dt, 'coin': coin, f'pct_{lookback}': val})

    # res = pd.DataFrame(res).set_index('dt')
    # res = res.sort_values(by=f'pct_{lookback}')
    # res = res[:5]
    # print(res)
    print('sum_pct', sum_pct)
    return None


if __name__ == '__main__':
    df = mark_enter_exit_points('1H')
    # df.tail()
