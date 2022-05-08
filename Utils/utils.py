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


class WaitToMinEveryHour:
    def __init__(self, trigger_minutes):
        self.trigger_minutes = trigger_minutes
        self._last_triggered = None

    def wait(self):
        while True:
            dt_now = datetime.now()
            # TODO: waiting 45 sec to update db with new hour data. maybe better is just to close it to the right
            if dt_now.minute in self.trigger_minutes:  # and dt_now.second > 45
                if not self._last_triggered or (dt_now - self._last_triggered).total_seconds() > 60:
                    self._last_triggered = dt_now
                    return
            time.sleep(5)

# def wait_to_min_every_hour(trigger_minutes, last_triggered=None):
#     # trigger_minutes=[0, 15, 30, 45]
#     while True:
#         dt_now = datetime.now()
#         if dt_now.minute in trigger_minutes:
#             if
#             dt_now
#         time.sleep(5)
