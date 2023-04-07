"""
# Collect Tweets logic: Save in db by name and ts, if exists, ignore it, check every 30sec. limit is 900 per 15min
"""
import os
import time
import grequests  # allowd multi threaded download but, this fucks up SSH_TUNNEL
from datetime import datetime
import pandas as pd
import psycopg2 as pg
from Utils.utils import WaitToMinEveryHour
# from Twitter.users import users
from Twitter.utils import print_from_db, load_from_txt

# https://www.investopedia.com/financial-edge/0712/10-twitter-feeds-investors-should-follow.aspx
TWITTER_URL_HIST = 'https://api.twitter.com/2/users/{}/tweets?max_results={}'
TWITTER_URL_LIVE = 'https://api.twitter.com/2/users/{}/tweets?start_time={}'
users_path = 'Twitter/users.txt'


def create_headers(bearer_token):
    headers = {"Authorization": "Bearer {}".format(bearer_token)}
    return headers


def auth():
    return os.getenv('TWITTER_BEARER_TOKEN')


def tweetId2epoch(id):
    return (id >> 22) + 1288834974657


def ts2dt(ts):
    return datetime.fromtimestamp(ts // 1000)


# https://tweeterid.com/
# url='https://api.twitter.com/2/users/by/us...{}'.format(username)
# API -> https://developer.twitter.com/en/docs/twitter-api/tweets/timelines/api-reference/get-users-id-tweets
# cannot accept less than 5

def go_over_multiple(users, live=True):
    headers = create_headers(auth())
    n_tweets_hist = 100

    def handle_data(res, name):
        if res.status_code != 200:
            print(f'BAD STATUS CODE for {name} got {res.status_code}')
            return []
        tweets_data = res.json()
        if tweets_data['meta']['result_count'] == 0:
            return []
        data = tweets_data['data']
        for tweet in data:
            tweet['ts'] = tweetId2epoch(int(tweet['id']))
            tweet['text'] = tweet['text'].replace('\n', ' ')
            tweet['name'] = name
        return data

    min_back = pd.to_timedelta('1T')
    start_time = pd.to_datetime(int(time.time()), unit='s', utc=True) - min_back
    start_time = start_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    try:
        if live:
            urls = [TWITTER_URL_LIVE.format(userid, start_time) for userid in users.values()]
        else:
            urls = [TWITTER_URL_HIST.format(userid, n_tweets_hist) for userid in users.values()]
        rs = [grequests.get(u, headers=headers) for u in urls]
        results = grequests.map(rs)
        users_tweets = [handle_data(res, name) for res, name in zip(results, users.keys())]
        res = []
        for tweets in users_tweets:
            for tweet in tweets:
                res.append(tweet)
        df = pd.DataFrame(res)
        return df

    except Exception as e:
        print(f'get_latest encountered {e}')
        return None


# class TweetDB:
#     def __init__(self):
#         self.con = sqlite3.connect('tweets.db')
#         cur = self.con.cursor()
#         q_create = "CREATE TABLE IF NOT EXISTS tweets (ts int not null, name varchar not null, text varchar, PRIMARY KEY(ts, name))"
#         cur.execute(q_create)
#         self.con.commit()
#
#     def save_to_db(self, df):
#         """Saves to db, ignore dup, returns df with rows that have been inserted"""
#         cur = self.con.cursor()
#         q = "INSERT OR IGNORE INTO tweets VALUES({}, '{}', '{}')"
#         new_idxs = []
#         for i, row in df.iterrows():
#             res = cur.execute(q.format(row['ts'], row['name'], row['text'].replace("'", "''")))
#             if res.rowcount > 0:
#                 new_idxs.append(i)
#         self.con.commit()
#         return df.loc[new_idxs]


class TwitterDBPostgres:

    def __init__(self):
        port = 5432
        conn = pg.connect(
            host="localhost",
            port=port,
            user=os.getenv("PGUSER"),
            password=os.getenv("PGPASSWORD"),
            database="vsdatabase"
        )
        self.con = conn
        cur = self.con.cursor()
        q_create = "CREATE TABLE IF NOT EXISTS tweets (ts bigint not null, name varchar not null, text varchar, PRIMARY KEY(ts, name))"
        cur.execute(q_create)
        self.con.commit()

    def save_to_db(self, df):
        """Saves to db, ignore dup, returns df with rows that have been inserted"""
        cur = self.con.cursor()
        q = "INSERT INTO tweets VALUES({}, '{}', '{}')"
        new_idxs = []
        for i, row in df.iterrows():
            try:
                cur.execute(q.format(row['ts'], row['name'], row['text'].replace("'", "''")))
                self.con.commit()
                # print(cur.rowcount, row)
                new_idxs.append(i)
            except Exception as e:
                cur.execute("rollback")
        cur.close()
        return df.loc[new_idxs]


def run_once():
    users = load_from_txt(path=users_path)
    df = go_over_multiple(users, live=False)
    print_from_db(df)


def realtime_to_db():
    # once will download hist of 100 recent tweets, then it will only fetch last 3 min
    live = False
    wait = WaitToMinEveryHour(range(60), offset_sec=0)
    db = TwitterDBPostgres()
    past_users = {}
    while True:
        wait.wait()
        users = load_from_txt(path=users_path)
        if past_users != users:
            print(f'Loading from {len(users)=}: {users}')
            past_users = users
        df = go_over_multiple(users, live=live)
        live = True
        if df is not None and len(df):
            df_new = db.save_to_db(df)
            if len(df_new):
                print_from_db(df_new)


if __name__ == '__main__':
    assert auth()
    realtime_to_db()
    # run_once()
