from Data import CryptoData
from datetime import datetime, timedelta
import pandas as pd
import os

from Data.Crypto.ccxt_utils import get_exchange_symbol_by_coin
from Data.Crypto.symbols import DB_PATH
from Utils import Persistence

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
def output_timeseries():
    tf = '5T'
    coin = 'BTC'
    provider, symbols = _get_provider(tf, days_before=300)
    ohlcv = provider.get_data(coin, tf)
    ohlcv.index = ohlcv.index.tz_localize(None)
    # ohlcv['volume_scaled'] = ohlcv.close * ohlcv.volume
    # ohlcv[['volume', 'volume_scaled']].to_csv('btc_vol.csv')
    ohlcv.to_csv(f'ohlcv_{coin}_{tf}.csv')


def correlation():
    import pandas as pd
    pd.set_option('display.max_rows', 500)
    pd.set_option('display.max_columns', 500)
    tf = '1H'
    data = {}
    selected = ['BTC', 'ETH', 'APE', 'MKR', 'LTC', 'CAKE', 'ACA']
    for tf in ['15T']:  # '5T', '15T', '1H', '4H', '1D'
        print(tf)
        provider, symbols = _get_provider(tf, days_before=300)
        for symbol in selected:
            close = provider.get_data(symbol, tf)['close']
            # if symbol == 'BTC':
            #     close = close.shift(5)
            data[symbol] = close
        df = pd.DataFrame(data)
        corr_mat = df.corr('spearman')
        print(corr_mat)
        # break
    print()



def compare_volume_monthly():
    # TODO: good graph
    # db_path = DB_PATH
    # db = Persistence(db_path)
    # import plotly.express as px
    import plotly.graph_objects as go
    from sklearn.preprocessing import MinMaxScaler

    fig = go.Figure()
    days_before = 90
    scaled = False
    in_usdt = True
    tf = '1W'
    title_text = f'Daily Crypto volume {days_before}d, to last midnight utm,' \
                 f' scaled?={scaled},' \
                 f' in_usdt?={in_usdt}'
    provider, symbols = _get_provider(tf, days_before=days_before)
    # shib volume is insane, but that is because its supply is huge. scaler is must.
    for coin in sorted(symbols)[:30]:
        if not scaled and coin == 'SHIB':
            continue
        # exchange_name, symbol = get_exchange_symbol_by_coin(coin)
        # df_1m = db.get_df(f'{exchange_name}_{coin}_USDT', tf='1m', start_date='2022-05-01')
        # volume_1d = df_1m.tz_convert(None).volume.resample('1D').sum()[:-1]
        df = provider.get_data(coin, tf)[:-1]  # [:-1] will not be closed to the right
        volume = df.volume
        if in_usdt:
            volume = volume * df.close
        vol_idx = volume.index
        vol = volume.values
        if scaled:
            vol = MinMaxScaler().fit_transform(vol.reshape(-1, 1)).reshape(-1)
        fig.add_trace(go.Scatter(name=coin, x=vol_idx, y=vol, mode='lines+markers'))
        # fig = px.scatter(df, x=df.index, y='volume', name=coin, # color=coin
        #                  )
    fig.update_layout(title_text=title_text)
    fig.show()
    # print(df.head())
    # res.append({
    #     'coin': coin,
    #     'chg_price': (df['close'][-1] / df['close'][-compare_to_day]) - 1,
    #     'chg_volume': (df['volume'][-1] / df['volume'].values[-compare_to_day]) - 1})


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


def _get_provider(tf, days_before=14):
    start_date = str((datetime.utcnow() - timedelta(days=days_before)).date())
    print('starting from:', start_date)
    provider = CryptoData.get_wrapper(live=False, start_date=start_date)
    # provider = provider.get_offline_wrapper([tf])
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
            .to_html('Analytics/output.html')

    df.to_csv('report.csv')
    print_html_pct(df)


if __name__ == '__main__':
    # compare_volume_monthly()
    # correlation()
    output_timeseries()
    # generate_report()
    # get_most_changing_coins_in_tf()
