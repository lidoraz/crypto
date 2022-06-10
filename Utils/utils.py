from datetime import datetime
import time
import math


def format_num(n, precision=3):
    if n > 99:
        return f'{n:.1f}'
    elif n > 9:
        return f'{n:.2f}'
    elif n > 1:
        return f'{n:.3f}'
    idx_first_digit_decimal = int(math.log10(abs(n))) * -1
    # add precision after first digit not zero
    out_str = str(f'{n:.{idx_first_digit_decimal + precision}f}')
    last_digit_not_zero = len(out_str) - 1
    for i in reversed(range(len(out_str))):
        if out_str[i] != '0':
            last_digit_not_zero = i + 1  # inclusive
            break
    out_str = out_str[:last_digit_not_zero]
    return out_str


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
            time.sleep(time_to_sleep)
            dt_now = datetime.now()  # take time again
            if dt_now.minute in self.trigger_minutes:
                return
