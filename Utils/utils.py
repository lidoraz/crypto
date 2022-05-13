from datetime import datetime
import pandas as pd
import time


def wait_until(end_datetime):
    while True:
        diff = (end_datetime - datetime.now()).total_seconds()
        if diff < 0:
            return  # In case end_datetime was in past to begin with
        time.sleep(diff / 2)
        if diff <= 0.1:
            return


# will trigger on every minute provided, with and offset option
class WaitToMinEveryHour:
    def __init__(self, trigger_minutes, offset_sec=15):
        self.trigger_minutes = trigger_minutes
        self.offset_sec = offset_sec
        print(f'WaitToMinEveryHour: trigger_minutes={trigger_minutes}, offset_sec={offset_sec}')

    def wait(self):
        while True:
            dt_now = datetime.now()
            time_to_sleep = 60 - dt_now.second + self.offset_sec
            print(f'wait: {dt_now}, {time_to_sleep}')
            time.sleep(time_to_sleep)
            # shift 1 min later as sleeps and then triggers exactly at trigger_minute.
            if int((dt_now.minute + 1) % 60) in self.trigger_minutes:
                return
