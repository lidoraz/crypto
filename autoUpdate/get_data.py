import pandas as pd
from datetime import datetime
import os
import json

TIME_CONV = "%Y-%m-%dT%H:%M:%S"  # .strftime


def _save_ts(path):
    with open(path + '/last.json', 'w') as fp:
        json.dump({'last_updated': datetime.utcnow().strftime(TIME_CONV)}, fp)


def _get_last_filesystem_ts(path):
    try:
        with open(path + '/last.json', 'r') as fp:
            last_date_updated = json.load(fp)['last_updated']
            return last_date_updated
    except FileNotFoundError:
        return '2022-01-01T00:00:00'


def get_data_from_remote(start_date, end_date, dir_name, cwd, remote_address, private_key):
    pwd_dir_name = os.path.join(cwd, dir_name)
    os.makedirs(pwd_dir_name, exist_ok=True)
    date_range = [d.date() for d in sorted(pd.date_range(start_date, end_date, freq='d'))]
    last_updated_date = datetime.strptime(_get_last_filesystem_ts(pwd_dir_name), TIME_CONV).date()
    for date in date_range:
        if date >= last_updated_date:
            date = str(date)
            # os.system('ls')
            os.system(f"scp -q -i {private_key} {remote_address}:{dir_name}/{date}.csv '{pwd_dir_name}/{date}.csv'")
    _save_ts(pwd_dir_name)
