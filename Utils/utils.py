from datetime import datetime
import time
import math


def _pretty_remainder(n, precision):
    idx_first_digit_decimal = int(math.log10(abs(n))) * -1
    # add precision after first digit not zero
    out_str = str(f'{n:.{idx_first_digit_decimal + precision}f}')[2:]  # skip 0.
    last_digit_not_zero = len(out_str) - 1
    for i in reversed(range(len(out_str))):
        if out_str[i] != '0':
            last_digit_not_zero = i + 1  # inclusive
            break
    out = out_str[:last_digit_not_zero]
    if len(out):
        return '.' + out
    else:
        return ''


def format_num(n, digits=0):
    try:
        fraction = n - math.floor(n)
        whole = str(math.floor(n))
        if fraction == 0:
            return round(n)
        elif n > 999:
            return f'{whole}'
        elif n > 99:
            return f'{whole}{_pretty_remainder(fraction, digits)}'
        elif n > 9:
            return f'{whole}{_pretty_remainder(fraction, digits+1)}'
        elif n > 1:
            return f'{whole}{_pretty_remainder(fraction, digits+2)}'
        else:
            return f'{whole}{_pretty_remainder(fraction, digits+3)}'
    except ValueError as e:
        return 'nan'


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
