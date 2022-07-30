from Twitter.connector import connect_ppg2
from Twitter.utils import get_lastest_from_db_postgres, print_from_db
from Utils.utils import WaitToMinEveryHour


def get_live():
    wait = WaitToMinEveryHour(range(60), offset_sec=10)
    users = ['unusual_whales', 'cnbc']
    users = []
    with connect_ppg2() as conn:
        while True:
            wait.wait()
            df = get_lastest_from_db_postgres(conn, 1)
            if users:
                df = df[df.name.isin(users)]
            print_from_db(df)
            # break


if __name__ == '__main__':
    get_live()
