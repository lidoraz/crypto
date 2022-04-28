from abc import abstractmethod, ABC


class Strategy(ABC):
    # @abstractmethod
    def __init__(self, params, *args, **kwargs):
        self.tf = params['tf']
        self.set_profit_pct = params['set_profit_pct']
        pass

    @abstractmethod
    def add_indicators(self, df):
        pass

    @abstractmethod
    def act(self, *args, **kwargs):
        pass
