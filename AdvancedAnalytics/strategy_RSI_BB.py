from DataProcessing.data_utils import get_data_providers, adjust_plot_start_datetime, prepare_data, get_coin_ohlc
from DataProcessing.data_consts import COINS
from Plots.traces import calc_pct_change
import pandas as pd
from DataProcessing.data_utils import extract_volume

from Plots.Indicators import RSI, BollingerBands, SMA


def mark_enter_exit_points(tf, indicators_lookahead=14):
    rsi_lookahead = indicators_lookahead

    filter_datetime = adjust_plot_start_datetime(tf)
    providers = get_data_providers()
    df_prices, df_hourly = prepare_data(providers, filter_datetime)

    ind_rsi = RSI(rsi_lookahead)
    ind_bb = BollingerBands(rsi_lookahead)
    ind_sma = SMA(100)
    # TODO: RSI divergence  or MaCD divergence
    sum_pct = 0
    trades = []
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

        df['rsi_70'] = df[rsi_col] > 70  # has passed RSI 70
        df['rsi_30'] = df[rsi_col] < 30  # has passed RSI 30
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
        # buy_idxes = list(df[df['buy']].index)
        # sell_idxes = list(df[df['sell']].index)
        buy_idx = None
        for idx, row in df.iterrows():
            if row['buy']:
                buy_idx = idx
                continue
            if row['sell'] and buy_idx:
                sell_idx = idx
                buy_price = df['close'].loc[buy_idx]
                sell_price = df['close'].loc[sell_idx]
                profit_pct = (sell_price / buy_price) - 1
                if profit_pct > 0:
                    profit_pct_str = f'{profit_pct:.2%} $ \u25B2'  # ▲
                else:
                    profit_pct_str = f'{profit_pct:.2%} $ \u25BC'  # ▼
                transaction = f'Trade: {coin}, {buy_idx}, {sell_idx}, {profit_pct_str} '
                trades.append(transaction)

                sum_pct += profit_pct
                buy_idx = None

        #     print(idx, row)
        # for sell_idx in sell_idxes:
        #     if found:
        #         break
        #     for buy_idx in buy_idxes:
        #         if found:
        #             break
        #         if sell_idx > buy_idx:
        #             buy_price = df['close'].loc[buy_idx]
        #             sell_price = df['close'].loc[sell_idx]
        #             profit_pct = (sell_price / buy_price) - 1
        #             if profit_pct > 0:
        #                 profit_pct_str = f'{profit_pct:.2%} $ \u25B2'  # ▲
        #             else:
        #                 profit_pct_str = f'{profit_pct:.2%} $ \u25BC'  # ▼
        #             print('Trade:', coin, buy_idx, sell_idx, profit_pct_str)
        #             sum_pct += profit_pct
        #             found = True

    print('sum_pct', sum_pct)
    return sum_pct, trades


if __name__ == '__main__':
    res = []
    l_trades = []
    for tf in ['1H']:  # ['5Min', '15Min', '1H', '4H']
        for lookahead in range(7, 15, 2):  # range(7, 30, 4):
            sum_pct, trades = mark_enter_exit_points(tf, lookahead)
            res.append([tf, lookahead, sum_pct])
            l_trades.append(trades)
    df = pd.DataFrame(res, columns=['tf', 'lookahead', 'sum_profit_pct']).sort_values('sum_profit_pct',
                                                                                      ascending=False).reset_index()
    print(df)
    win_idx = df['index'][0]
    sum_profit_pct = df['sum_profit_pct'][0]
    print('Index:', win_idx, f'Pct profit: {sum_profit_pct:.2%}')
    print("\n".join(l_trades[win_idx]))
    # df.tail()
