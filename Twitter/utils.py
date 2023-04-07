import pandas as pd


def print_from_db(df):
    dt_tz = pd.to_datetime(df['ts'], unit='ms', utc=True).dt.tz_convert('Israel')
    df = df.set_index(dt_tz).drop(columns='ts')
    df = df.sort_index()
    for dt, row in df.iterrows():
        print(f"{dt.strftime('%Y-%m-%d %H:%M:%S')}, {row['name']} => {row['text']}")


def get_latest_from_db(db, min_back):
    q = "Select *  from tweets where ts  > (strftime('%s', 'now') - {} * 60) * 1000"
    df = pd.read_sql(q.format(min_back), db.con)
    return df


def get_lastest_from_db_postgres(con, min_back: int, free_text_filter=None):
    import time
    # Should take 1 min before + few seconds prior to that, could be 6 but needs to check.
    # time_now = (int(time.time()) - min_back * 60 + 12) * 1000
    time_now = (int(time.time()) - min_back * 60) * 1000
    # print(pd.to_datetime(time_now, unit='ms'), time_now)
    if free_text_filter:
        q = f'Select * from tweets where ts >= {time_now} {free_text_filter} order by ts'
    else:
        q = f'Select * from tweets where ts >= {time_now} order by ts'
    # epoch_from = f"(cast(extract(epoch from now()) as BIGINT) - {minback} * 60) * 1000"
    # q = f"Select * from tweets where ts > {epoch_from} {free_text_filter if free_text_filter else ''} order by ts"
    print(q)
    df = pd.read_sql(q, con)
    return df


def load_from_txt(path='users.txt'):
    with open(path, 'r') as f:
        lines = f.readlines()
    remove_comments = lambda x: x if '#' not in x else x.split('#')[0]
    lines = [remove_comments(l.replace('\n', '')) for l in lines]
    users = {}
    for line in lines:
        try:
            if '#' in line:
                continue
            k, v = line.split('=')
            k = k.strip()
            v = int(v)
            users[k] = v
        except:
            pass
    return users
