# https://www.cryptocompare.com/coins/guides/how-to-use-our-api/
# limit of # calls per hour:
# https://min-api.cryptocompare.com/stats/rate/hour/limit
# url = f"https://min-api.cryptocompare.com/data/price?fsym={from_coin}&tsyms={to_coin}"
import time
import os
import requests
import json
from datetime import datetime, timedelta

import os

api_key = os.environ.get('CRYPTOCOMPARE_APYKEY')
if not api_key:
    raise ValueError('must have CRYPTOCOMPARE_APYKEY set')

path_data_dir = 'data_hourly'
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

selected_signals = [
    'PRICE',
    'LASTUPDATE',

    'OPENHOUR',
    'HIGHHOUR',
    'LOWHOUR',
    'VOLUMEHOUR',
    'VOLUMEHOURTO',
    'CHANGEHOUR',
    'CHANGEPCTHOUR',

    'OPEN24HOUR',
    'HIGH24HOUR',
    'LOW24HOUR',
    'VOLUME24HOUR',
    'VOLUME24HOURTO',
    'CHANGE24HOUR',
    'CHANGEPCT24HOUR',

    'OPENDAY',
    'HIGHDAY',
    'LOWDAY',
    'VOLUMEDAY',
    'VOLUMEDAYTO',
    'CHANGEDAY',
    'CHANGEPCTDAY',

]

str_coins = ','.join(coins)


def get_coin_data_multifull(coins):
    str_coins = ','.join(coins)
    url = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={str_coins}&tsyms=USDT&api_key={api_key}"
    try:
        response = requests.get(url)
        if (response.status_code == 200):
            coin_data = json.loads(response.text)
            coin_data = coin_data['RAW']
            if list(coin_data.keys()) == coins:
                return coin_data
            else:
                print('received coin keys do not match defined ordered list')
                return None
        else:
            print(response.status_code, response.text)
            return None
    except:
        print('got exception..')
        return None


def parse_multifull_msg(coins, signals, coin_data):
    raw_arr_keys = []
    raw_arr_values = []
    for c in coins:
        coin_struct_remote = coin_data[c]['USDT']
        # round columns TODO: maybe
        # round_cols = VOLUME, CHANGE, PCT, (so far none)
        pct_keys = [k for k in coin_struct_remote if 'PCT' in k]
        for pct_k in pct_keys:
            coin_struct_remote[pct_k] = round(coin_struct_remote[pct_k], 2)
        coin_struct = {k: '' for k in signals}
        intersect_keys = set(coin_struct.keys()).intersection(coin_struct_remote.keys())
        coin_struct.update((k, coin_struct_remote[k]) for k in intersect_keys)

        curr_coin_keys = [f'{c}_{k}' for k in coin_struct.keys()]
        curr_coin_values = list(coin_struct.values())
        raw_arr_keys += curr_coin_keys
        raw_arr_values += curr_coin_values
    return raw_arr_keys, raw_arr_values


def get_coin_signals_hourly(coins, signals):
    coin_data = get_coin_data_multifull(coins)
    if coin_data:
        coin_parsed_data = parse_multifull_msg(coins, signals, coin_data)
        if coin_parsed_data:
            coin_keys, coin_values = coin_parsed_data
            return coin_keys, coin_values
        else:
            return None
    else:
        return None


def array_to_str_comma(x):
    return ','.join([str(xx) for xx in x])


# def is_30sec_to_hour(time_now):
#     return time_now.minute == 59 and 30 < time_now.second < 50

def is_10sec_to_quarter_hour(time_now):
    if time_now.second < 51:
        return False
    elif time_now.minute in [14, 29, 44, 59]:
        return True
    else:
        return False


# VOLUME_HOUR is a counter that resets every 1 hour!!!!
# # append with 'a' instead of 'w'
print(f'Running forever...')

os.makedirs(path_data_dir, exist_ok=True)
has_output_cols = False
while True:
    is_day_finished = False
    curr_day = datetime.utcnow().date()
    # TODO: Bug when file is open for the first of the day but no data has been written yet
    with open(f'{path_data_dir}/{str(curr_day)}.csv', 'a') as f:
        while not is_day_finished:
            time_now = datetime.utcnow()
            if is_10sec_to_quarter_hour(time_now):
                time_now_str = time_now.strftime("%Y-%m-%dT%H:%M:%S")
                coin_data = get_coin_signals_hourly(coins, selected_signals)
                if coin_data:
                    coin_keys, coin_values = coin_data
                    print(array_to_str_comma([time_now_str] + coin_values), file=f, flush=True)
                    time.sleep(10)  # sleep in order to pass predicate
                else:
                    print((time_now_str, 'something is wrong, null response'), flush=True)
            if time_now.date() > curr_day:
                is_day_finished = True
            time.sleep(1)

    if not has_output_cols:
        print((time_now_str, coin_keys, coin_values), flush=True)
        is_output_cols = True
