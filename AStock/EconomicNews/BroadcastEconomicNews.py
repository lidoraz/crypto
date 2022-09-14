# TELEGRAM_GROUP_NEWS
import schedule
import pandas as pd
from AStock.EconomicNews.util import scrape_data
from datetime import datetime
import requests
import os
import time


# df = df['dt'].dt.date


def get_todays(tz=None):
    try:
        df = scrape_data()
        print(f"Got table with {len(df)} rows, from {df['dt'].min()} -> {df['dt'].max()} (UTC)")
        # df['dt'] = df['dt'].dt.tz_localize('UTC').dt.tz_convert(tz)
        curr_date = datetime.now().date()
        df = df[df['dt'].dt.date == curr_date]
        print(f'Today\'s: {curr_date} total {len(df)}')
        # print(df.to_string())
        return df
    except Exception as e:
        print('Something went wrong..', e)
        return None


def publish(msg, prod):
    if prod:
        url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={group_id}&text={msg}&parse_mode=HTML"
        token = os.environ.get('TELEGRAM_TOKEN')
        group_id = os.environ.get('TELEGRAM_GROUP_NEWS')
        print('token:', token)
        print('group_id', group_id)
        print(url.format(token=token, group_id=group_id, msg=msg))
        res = requests.get(url.format(token=token, group_id=group_id, msg=msg))
        print(res.status_code)
        print(res.content)
    else:
        print(msg)


def build_str(df, convert_tz=None):
    df['dt'] = df['dt'].dt.tz_localize('UTC').dt.tz_convert(convert_tz)
    today = str(df['dt'].dt.date[0])
    str_build = f'<u><b>Todays ({today})</b></u>\n'
    if len(df) == 0:
        str_build += 'Nothing..'
        return str_build
    for _, row in df.iterrows():
        importance = row['importance']
        hour = row['dt'].hour
        minute = row['dt'].minute
        title = row['title']
        consensus = row['consensus']
        actual = row['actual']
        importance_icon = {'1': '1', '2': '🛎️', '3': '🚨'}
        importance = importance_icon.get(importance, '')
        compare_icon = {True: '⬆️', False: '⬇️'}
        compare = compare_icon.get(row['compare'], '')

        actual_str = f', act:{actual}{compare}' if actual != 'NOTYET' else ''

        str_build += f'{importance}{hour}:{minute:02d} {title} <b>con:{consensus}{actual_str} </b>\n'
    return str_build


def job_that_executes_once(hour, minute):
    def run():
        print('Do once', hour, minute, datetime.now())
        df = get_todays()
        df = df[(df['dt'].dt.hour == hour) & (df['dt'].dt.minute == minute)]
        if len(df):
            str_build = build_str(df, convert_tz='Israel')
            publish(str_build, prod=True)
            # broadcast only results from that specific task
        else:
            print('job_that_executes_once got empty Dataframe after filtering!')
        return schedule.CancelJob

    return run


def create_tasks(df):
    # df = df[df['importance'] == '3']
    time_now = datetime.utcnow()
    dts = df.dt.unique()
    for dt in dts:
        dt = pd.Timestamp(dt)
        if time_now < dt:
            hour = dt.hour
            minute = dt.minute
            # schedule does not support timezone, must make sure the trigger time is UTC!
            # hour = hour + 3
            print('Registering a job to trigger today at time:', dt, f'{hour:02d}:{minute:02d}')
            schedule.every().day.at(f'{hour:02d}:{minute:02d}:01').do(job_that_executes_once(hour, minute))


def job():
    df = get_todays(None)

    create_tasks(df)  # Make this work, later....
    str_build = build_str(df, convert_tz='Israel')
    publish(str_build, prod=True)
    # Build a task to  get data at correct timing


def get_local_tz():
    return int(datetime.utcnow().astimezone().utcoffset().total_seconds() / (60 * 60))


def run_forever():
    # at_time = '18:00'
    at_time = '07:00'  # UTC
    print(f'Running forever... everyday at: {at_time}')
    # publish("Test", prod=True)
    schedule.every().day.at(at_time).do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
        # schedule.get_jobs()


if __name__ == '__main__':
    job()  # do it once, and then go to loop
    run_forever()
