# https://www.cryptocompare.com/coins/guides/how-to-use-our-api/
# limit of # calls per hour:
# https://min-api.cryptocompare.com/stats/rate/hour/limit
# url = f"https://min-api.cryptocompare.com/data/price?fsym={from_coin}&tsyms={to_coin}"
import time
import os
import requests
import json
from datetime import datetime, timedelta

# TODO: can use Scheduler, looks much more smooth.
api_key = '90d6d0bc6a720716f80e6bf38272c4fd39cc71b88b1b77fe8da86e5c0a210054'
path_data_dir = 'data'
coins = [
    'BTC',
    'ETH',
    'SOL',
    'ROSE',
    'RMRK',
    'MOVR',
    'DOT',
    'LUNA',
    'KDA',
    'KSM',
    'HTR',
    'VRA',
    'TEL',
    'QRDO',
    'FLUX',
    'RNDR',
    'MATIC',
    'GLMR',
    'EGLD',
    'LYXE',
    'SOUL',
    'ACA',
    'GCOIN',
    'CRV',
    'BNB',
    'ADA',
    'AXS',
    'XRP',
    'APE',
    'SHIB',
    'GALA',
    'SAND',
    'FTM',
    'MANA',
    'XLM',
    'RUNE',
    'OGN',
    'CAKE',
]

str_coins = ','.join(coins)


def get_coin_data(coins):
    str_coins = ','.join(coins)
    url = f"https://min-api.cryptocompare.com/data/pricemulti?fsyms={str_coins}&tsyms=USDT&api_key={api_key}"
    response = requests.get(url)
    if (response.status_code != 200):
        print(response.status_code, response.text)
        return None
    else:
        coin_data = json.loads(response.text)
        return coin_data


def parse_json(coin_data):
    keys = list(coin_data.keys())
    values = [list(x.values())[0] for x in coin_data.values()]
    return keys, values


def get_curr_coin_prices(coins):
    coin_data = get_coin_data(coins)
    if coin_data:
        coin_keys, coin_values = parse_json(coin_data)
        return coin_keys, coin_values
    else:
        return None


def array_to_str_comma(x):
    return ','.join([str(xx) for xx in x])


def is_5sec_to_half_min(time_now):
    second = time_now.second
    return second > 25 and second < 30 or second > 55 and second < 60


# append with 'a' instead of 'w'
print(f'Running forever...')

os.makedirs(path_data_dir, exist_ok=True)
is_could_save = False
has_output_cols = False
while True:
    is_day_finished = False
    curr_day = datetime.utcnow().date()
    with open(f'{path_data_dir}/{str(curr_day)}.csv', 'a') as f:
        while not is_day_finished:
            time_now = datetime.utcnow()
            if is_5sec_to_half_min(time_now):
                time_now_str = time_now.strftime("%Y-%m-%dT%H:%M:%S")
                coin_data = get_curr_coin_prices(coins)
                if coin_data:
                    coin_symbols, coin_values = coin_data
                    print(array_to_str_comma([time_now_str] + coin_values), file=f, flush=True)
                    time.sleep(10)  # sleep in order to pass predicate
                else:
                    print((time_now_str, 'something is wrong, null response'), flush=True)
            if time_now.date() > curr_day:
                is_day_finished = True
            time.sleep(1)

    if not has_output_cols:
        print((time_now_str, coin_symbols, coin_values), flush=True)
        is_output_cols = True
