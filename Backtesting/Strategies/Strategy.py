from abc import abstractmethod, ABC


class Strategy(ABC):
    @abstractmethod
    def add_indicators(self, df):
        pass

    @abstractmethod
    def act_buy(self, idx, row):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass
