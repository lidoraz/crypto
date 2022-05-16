from Data import CryptoData
from datetime import datetime, timedelta
import pandas as pd
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(root)


def get_most_changing_coins_in_tf():
    tf = '2D'
    provider = CryptoData.get_wrapper(live=False)
    symbols = provider.get_symbols()

    series = pd.Series(dtype=float)
    for coin in symbols:
        start_date = str((datetime.utcnow() - timedelta(days=30)).date())
        df = provider.get_data(coin, tf, start_date=start_date)
        last_change = df.close.pct_change().iloc[-1]
        series = pd.concat([series, pd.Series([last_change], [coin])])

    series = series.sort_values()
    print('Most Gain:')
    print(series.tail(5)[::-1])
    print('Most Lose:')
    print(series.head(5))


if __name__ == '__main__':
    get_most_changing_coins_in_tf()
