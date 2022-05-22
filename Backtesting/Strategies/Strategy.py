from abc import abstractmethod, ABC


class Strategy(ABC):
    @abstractmethod
    def add_indicators(self, df):
        pass

    @abstractmethod
    def act_buy(self, idx, row):
        pass
