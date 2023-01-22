"""
# Collect Tweets logic: Save in db by name and ts, if exists, ignore it, check every 30sec. limit is 900 per 15min
"""
import os
import time
import schedule
from datetime import datetime
import psycopg2 as pg
from forsale.scraper_yad2 import scraper_yad2


def _scraper():
    with pg.connect(
            host="localhost",
            port=5432,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            database="vsdatabase"
    ) as conn:
        print(f"{datetime.today()} Starting to fetch!")
        scraper_yad2(conn)
        print(f"{datetime.today()} Finished !")


def routine_daily_yad2_to_db():
    schedule.every().day.at("00:00").do(_scraper)
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    routine_daily_yad2_to_db()
