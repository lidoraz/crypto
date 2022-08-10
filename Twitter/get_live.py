from Twitter.connector import connect_ppg2
from Twitter.utils import get_lastest_from_db_postgres, print_from_db
from Utils.utils import WaitToMinEveryHour
from collections import deque


def get_live():
    wait = WaitToMinEveryHour(range(60), offset_sec=5)
    users = ['unusual_whales', 'cnbc']
    users = []
    if len(users):
        print('Getting live tweets only from:', users)
    already_seen = deque(maxlen=100)
    conn = connect_ppg2()
    socket_error = True
    while True:
        try:
            if socket_error:
                conn = connect_ppg2()
            wait.wait()
            df = get_lastest_from_db_postgres(conn, 5)
            if len(df):
                ids = df.apply(lambda row: f"{row['ts']}_{row['name']}", axis=1)
                df = df[ids.apply(lambda x: x not in already_seen)]
                already_seen.extend(ids.values)
                if users:
                    df = df[df.name.isin(users)]
                print_from_db(df)
            socket_error = False
        except Exception as e:
            socket_error = True
            print(f'ERROR - {e}')
    # conn.close()


if __name__ == '__main__':
    get_live()
