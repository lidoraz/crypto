from abc import abstractmethod, ABC
import json


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
