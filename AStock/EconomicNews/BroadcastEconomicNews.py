# TELEGRAM_GROUP_NEWS
import schedule
import pandas as pd
from AStock.EconomicNews.util import scrape_data
from datetime import datetime
import requests
import os
import time

_PROD = True
_sec_offset = 1  # always 1 as there is a retry mechanism

print('PROD IS:', _PROD)


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
        # url = "https://api.telegram.org/bot{token}/sendMessage?chat_id={group_id}&text={msg}&parse_mode=HTML"
        url = "https://api.telegram.org/bot{}/sendMessage"
        token = os.environ.get('TELEGRAM_TOKEN')
        group_id = os.environ.get('TELEGRAM_GROUP_NEWS')
        params = {
            "chat_id": group_id,
            "text": msg,
            "parse_mode": "HTML",
        }
        # print(url.format(token=token, group_id=group_id, msg=msg))
        res = requests.get(url.format(token),
                           params=params)
        print(res.status_code)
        print(res.content)
    else:
        print(msg)


def build_str(df, convert_tz=None):
    df['dt'] = df['dt'].dt.tz_localize('UTC').dt.tz_convert(convert_tz)
    today = str(datetime.now().date())
    str_build = f"<u><b>Today's ({today})</b></u>\n"
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
        compare_icon = {'+': '⬆️', '-': '⬇️', '=': '⬅️'}
        # compare_icon = {'+': '🟢️', '-': '🔴️', '=': '⚪'}
        compare = compare_icon.get(row['compare'], '')

        actual_str = f', act:{actual}{compare}' if actual != 'NOTYET' else ''

        str_build += f'{importance}{hour}:{minute:02d} {title} <b>con:{consensus}{actual_str} </b>\n'
    return str_build


def job_that_executes_once(hour, minute):
    def check_is_all_filled(df):
        for idx, row in df.iterrows():
            # graceful, this forces all rows to be filled before publishing
            if row['previous'] != '' and row['actual'] == 'NOTYET':
                return False
            # TODO: REMOVE HOUR MIN before, and better to push notification new events.
        return True

    def filter_not_filled(df, rows_got):
        use_rows = []
        for idx, row in df.iterrows():
            if row['previous'] == '' or row['actual'] != 'NOTYET':  # filled or not having previous
                if row['title'] not in rows_got:
                    use_rows.append(idx)
                    rows_got.append(row['title'])
        return df.loc[use_rows], rows_got

    def _job_that_executes_once():
        print('Do once', hour, minute, datetime.now())
        tried = 0
        tries = 45
        rows_got = []
        while tried < tries:
            tried += 1
            df = get_todays()
            df = df[(df['dt'].dt.hour == hour) & (df['dt'].dt.minute == minute)]
            if len(df):
                # if is_all_filled:
                # is_all_filled = check_is_all_filled(df)
                df, total_got = filter_not_filled(df, rows_got)
                if len(df):
                    str_build = build_str(df, convert_tz='Israel')
                    publish(str_build, prod=_PROD)
                    return schedule.CancelJob
                else:
                    print(f'Still not filled {tried}/{tries}, but published rows: {rows_got}')
                # broadcast only results from that specific task
            else:
                print(f'job_that_executes_once got empty Dataframe after filtering! {tried}/{tries}')
            time.sleep(1.5)

    return _job_that_executes_once


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
            print(
                f"Registering a job to trigger {(df['dt'] == dt).sum()} events, Today at: {hour:02d}:{minute:02d}, ({dt})")
            schedule.every().day.at(f'{hour:02d}:{minute:02d}:{_sec_offset:02d}').do(
                job_that_executes_once(hour, minute))


def job():
    df = get_todays(None)
    if df is not None and len(df):
        create_tasks(df)  # Make this work, later....
        str_build = build_str(df, convert_tz='Israel')
        publish(str_build, prod=_PROD)
    else:
        print('get_todays, df is empty, or having a problem')
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
        # print(schedule.get_jobs())


if __name__ == '__main__':
    # job_that_executes_once(12, 30)()
    job()  # do it once, and then go to loop
    run_forever()
