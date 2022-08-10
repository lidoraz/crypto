from abc import abstractmethod, ABC
import json
import pandas as pd
import numpy as np


class Strategy(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def add_indicators(self, df):
        pass

    @abstractmethod
    def act_buy(self, idx, row):
        pass

    @abstractmethod
    def act_sell(self, idx, row):
        pass

    def calc_indicators(self, df, dropna=True):
        attrs = df.attrs
        indicators = [ind for ind in dir(self) if ind.startswith('_ind_')]
        for ind in indicators:
            df = df.join(getattr(self, ind).calc(df))
        if dropna:
            df = df.dropna()
        df.attrs = attrs
        return df

    def __repr__(self):
        props = vars(self)
        props = {k: props[k] for k in props if not k.startswith('_')}
        return json.dumps(props)

    def __str__(self):
        return self.name


def crossed(a: pd.Series, b: [pd.Series, int], direction):
    if direction == "above":
        return (a > b) & (a.shift(1) <= b.shift(1))

    elif direction == "below":
        return (a < b) & (a.shift(1) >= b.shift(1))
    else:
        raise ValueError()


def crossed_above(a, b, n_back=1):
    """
    a crossed b and now its above b, n_back candles recently
    """
    return crossed(a, b, "above").rolling(n_back).sum() > 0


def crossed_below(a, b, n_back=1):
    """
    a crossed b and now its below b, n_back candles recently
    """
    return crossed(a, b, "below").rolling(n_back).sum() > 0


def check_all_ind(ind_bool_list):
    return pd.concat(ind_bool_list, axis=1).all(axis=1)


def calc_take_profit_price(side, price, stop_loss, rw_ratio=1.0, max_stop_pct=0.08):
    """
    # Stop loss is calculated by last swing low, however, it is adujsted in case it is too high with max_stop_pct
    # TP is calculated by last swing low diff from current price, multiplied by rw_ratio, depending on amount, usually 1-1.5
    # risk management, need to split tp to 3 tp stages, for better securing profits
    """
    assert side in ('buy', 'sell')
    assert max_stop_pct is None or max_stop_pct is not None and 0.01 < max_stop_pct < 0.15
    if max_stop_pct in (None, 0):
        max_stop_pct = 1
    pct_to_curr_price = 0.005
    price_to_stop = abs(price - stop_loss)
    if side == 'buy':  # long
        if max_stop_pct:
            stop_loss = max(price * (1 - max_stop_pct), stop_loss)
        if price / stop_loss <= 1 + pct_to_curr_price:  # should be larger than 1.001
            print(f'{side} stop price too close to exec_price: less than {pct_to_curr_price}')
            stop_loss = price * (1 - pct_to_curr_price)
            take_profit = price * (1 + pct_to_curr_price)
        else:
            take_profit = price + rw_ratio * price_to_stop
    else:  # short
        if max_stop_pct:
            stop_loss = min(price * (1 + max_stop_pct), stop_loss)
        if price / stop_loss >= 1 - pct_to_curr_price:  # should be less than 0.999
            print(f'{side} stop price too close to exec_price: less than {pct_to_curr_price}')
            stop_loss = price * (1 + pct_to_curr_price)
            take_profit = price * (1 - pct_to_curr_price)
        else:
            take_profit = price - rw_ratio * price_to_stop

    return stop_loss, take_profit
