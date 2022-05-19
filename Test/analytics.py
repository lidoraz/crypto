from Data import CryptoData
from datetime import datetime, timedelta
import pandas as pd
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)


# def get_most_changing_coins_in_tf():
#     tf = '2D'
#     provider = CryptoData.get_wrapper(live=False)
#     symbols = provider.get_symbols()
#
#     series = pd.Series(dtype=float)
#     for coin in symbols:
#         start_date = str((datetime.utcnow() - timedelta(days=30)).date())
#         df = provider.get_data(coin, tf, start_date=start_date)
#         last_change = df.close.pct_change().iloc[-1]
#         series = pd.concat([series, pd.Series([last_change], [coin])])
#
#     series = series.sort_values()
#     print('Most Gain:')
#     print(series.tail(5)[::-1])
#     print('Most Lose:')
#     print(series.head(5))


# def change_in_volume_every_day(provider, symbols):
#     tf = '24h'
#     series = pd.Series(dtype=float)
#     for coin in symbols:
#         df = provider.get_data(coin, tf)  # will not be closed to the right
#         df = df[:-1].copy()
#         vol = df['volume'].pct_change() - 1
#         last_change = df['rolling'].values[-1] / df['rolling'].values[-7] #df.volume.pct_change().iloc[-1]
#         series = pd.concat([series, pd.Series([last_change], [coin])])
#     series.name = 'chg_volume'
#     return series
# def compare_change_price_volume_24h(provider, symbols, compare_to_day):
#     compare_to_day = compare_to_day + 1
#     res = []
#     # df['rolling'] = vol.rolling(7).sum()
#     for coin in symbols:
#         df = provider.get_data(coin, '1min') # will not be closed to the right
#         last_price = df[:-1]
#         df_day_before = df[df.index < pd.to_datetime(datetime.utcnow(), utc=True).tz_convert('Israel') - pd.to_timedelta('1D')].iloc[-1]
#         df = df[:-1].copy()
#         res.append({
#             'coin': coin,
#             'chg_price': (df['close'][-1] / df['close'][-compare_to_day]) - 1,
#             'chg_volume': (df['volume'][-1] / df['volume'].values[-compare_to_day]) - 1})
#     return pd.DataFrame(res).set_index('coin')


def compare_change_price_volume(provider, symbols, compare_to_day):
    compare_to_day = compare_to_day + 1
    tf = '1D'
    res = []
    # df['rolling'] = vol.rolling(7).sum()
    for coin in symbols:
        df = provider.get_data(coin, tf)  # will not be closed to the right
        df = df[:-1].copy()
        res.append({
            'coin': coin,
            'chg_price': (df['close'][-1] / df['close'][-compare_to_day]) - 1,
            'chg_volume': (df['volume'][-1] / df['volume'].values[-compare_to_day]) - 1})
    return pd.DataFrame(res).set_index('coin')


def _get_provider(tf):
    start_date = str((datetime.utcnow() - timedelta(days=14)).date())
    print('starting from:', start_date)
    provider = CryptoData.get_wrapper(live=False, start_date=start_date)
    provider = provider.get_offline_wrapper([tf])
    symbols = provider.get_symbols()
    return provider, symbols


def generate_report():
    provider, symbols = _get_provider('1D')  # '1D'
    # change_in_volume_every_day(provider, symbols)
    dfs = []
    for compare_to_day in [1, 7]:
        # df = compare_change_price_volume_24h(provider, symbols, compare_to_day)
        df = compare_change_price_volume(provider, symbols, compare_to_day)
        df.columns = [f'{c}_{compare_to_day}' for c in df.columns]
        dfs.append(df)
    df = pd.concat(dfs, axis=1)
    df = df[sorted(df.columns)]

    sort_by = 'chg_volume_7'  # chg_price
    print('sorted by', sort_by)
    pd.options.display.float_format = '{:.2%}'.format
    df = df.sort_values(sort_by, ascending=False)
    print(df)

    def print_html_pct(df):
        df.style. \
            background_gradient(cmap='RdYlGn', vmin=-0.75, vmax=.75, axis=0). \
            format('{:.2%}'.format). \
            set_properties(**{'font-size': '10pt', 'font-family': 'ui-monospace'}) \
            .to_html('output.html')

    print_html_pct(df)


if __name__ == '__main__':
    generate_report()
    # get_most_changing_coins_in_tf()
