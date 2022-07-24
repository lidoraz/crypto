from abc import abstractmethod, ABC
import json
import pandas as pd


class Strategy(ABC):
    def __init__(self, name):
        self.name = name

    @abstractmethod
    def add_indicators(self, df):
        pass

    @abstractmethod
    def act_buy(self, idx, row):
        pass

    def __repr__(self):
        props = vars(self)
        props = {k: props[k] for k in props if not k.startswith('_')}
        return json.dumps(props)

    def __str__(self):
        return self.name


def crossed(a: pd.Series, b: pd.Series, direction):
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


def calc_take_profit_price(side, price, stop_loss, rw_ratio=1.0, pct_to_curr_price=0.005):
    assert side in ('buy', 'sell')
    price_to_stop = abs(price - stop_loss)
    if side == 'buy':  # long
        if price / stop_loss <= 1 + pct_to_curr_price:  # should be larger than 1.001
            print(f'{side} stop price too close to exec_price: less than {pct_to_curr_price}')
            stop_loss = price * (1 - pct_to_curr_price)
            take_profit = price * (1 + pct_to_curr_price)
        else:
            take_profit = price + rw_ratio * price_to_stop
    else:  # short
        if price / stop_loss >= 1 - pct_to_curr_price:  # should be less than 0.999
            print(f'{side} stop price too close to exec_price: less than {pct_to_curr_price}')
            stop_loss = price * (1 + pct_to_curr_price)
            take_profit = price * (1 - pct_to_curr_price)
        else:
            take_profit = price - rw_ratio * price_to_stop

    return stop_loss, take_profit
