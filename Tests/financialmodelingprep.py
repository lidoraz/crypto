api_key = '2a7d32df72d5ab368b1a2a500e4b9033'

from datetime import datetime
import requests
import json
import pandas as pd
from Tests.symbols import nasdq_100
# TODO: Crap library

# DAILY OHLCV
def get_from_financialmodelingprep(symbol, from_date, to_date):
    path = f"https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}?from={from_date}&to={to_date}&apikey={api_key}"
    r = requests.get(path)
    if r.status_code != 200:
        print('Status code differs from 200')
    data = json.loads(r.content)
    df = None
    if len(data) != 0:
        df = pd.DataFrame(data['historical']).set_index('date').sort_index()
    return df


def save_financialmodelingprep_data():
    pre_path = "Tests/financialmodelingprep_data"
    from_date = '2021-01-01'
    to_date = str(datetime.now().date())
    for idx, symbol in enumerate(nasdq_100):
        df = get_from_financialmodelingprep(symbol, from_date, to_date)
        if df is not None:
            df.to_csv(f'{pre_path}/{symbol}_{from_date}_{to_date}.csv')
        if idx > 5:
            break


if __name__ == '__main__':
    save_financialmodelingprep_data()
