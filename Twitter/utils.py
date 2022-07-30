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


def get_lastest_from_db_postgres(con, minback:int, free_text_filter=None):
    epoch_from = f"(cast(extract(epoch from now()) as BIGINT) - {minback} * 60) * 1000"
    q = f"Select * from tweets where ts > {epoch_from} {free_text_filter if free_text_filter else ''} order by ts"
    df = pd.read_sql(q, con)
    return df