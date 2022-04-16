import time
import os
from datetime import datetime
from get_data import get_data_from_remote

# /Users/lidorazulay/Library/Mobile Documents/com~apple~CloudDocs/DS/Crypto/autoUpdate/auto_update.py
# '/Users/lidorazulay/Library/Mobile Documents/com~apple~CloudDocs/DS/Crypto'
# python autoUpdate/auto_update.py
pwd = os.getcwd()
pwd = os.path.join(pwd, 'resources.nosync')
print('saving to:', pwd)
remote_address = "ec2-user@ec2-18-134-142-217.eu-west-2.compute.amazonaws.com"
private_key = "shushu_entrance.pem"

print('Running forever keeping data files updated...')

start_date = '2022-03-26'

# sync with remote:
while True:
    time_now = datetime.utcnow()
    if 3 < time_now.second < 6:
        break
    time.sleep(1)
print('synced with remote time..')
# get for the first time hourly data
get_data_from_remote(start_date, str(datetime.utcnow().date()), 'data_hourly', pwd, remote_address, private_key)

# TODO: can use Scheduler, looks much more smooth.
while True:
    time_now = datetime.utcnow()
    date_now_s = str(time_now.date())
    get_data_from_remote(start_date, date_now_s, 'data', pwd, remote_address, private_key)

    if time_now.minute in [1, 16, 31, 46]:  # better minute is it runs on real time
        # print('getting file:', f'{pwd_dir_name}/{date}.csv')
        print(time_now, 'getting hourly agg file')
        get_data_from_remote(start_date, date_now_s, 'data_hourly', pwd, remote_address, private_key)
    time.sleep(30)
