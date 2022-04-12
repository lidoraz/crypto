from DataProcessing.data_utils import get_data_providers, adjust_plot_start_datetime, prepare_data
from DataProcessing.data_consts import COINS
from Plots.traces import calc_pct_change
import pandas as pd


def get_most_changing_coins_in_tf(tf):
    filter_datetime = adjust_plot_start_datetime(tf)
    providers = get_data_providers()
    df_prices, df_hourly = prepare_data(providers, filter_datetime)

    pct_threshold = 0  # 15.0
    lookback = '1D'  # ,'1H'
    res = []
    for coin in COINS:
        df_coin = df_prices[coin]
        pct = calc_pct_change(df_coin, lookback)
        current_granular_change = pct.tail(1)
        dt = current_granular_change.index[0]
        val = round(current_granular_change[0], 3)
        if abs(val) > pct_threshold:
            res.append({'dt': dt, 'coin': coin, f'pct_{lookback}': val})

    res = pd.DataFrame(res).set_index('dt')
    res = res.sort_values(by=f'pct_{lookback}')
    res = res[:5]
    print(res)


if __name__ == '__main__':
    get_most_changing_coins_in_tf('1H')
