from abc import abstractmethod, ABC


class ProviderData(ABC):

    @abstractmethod
    def get_data(self, symbol: str, tf: str):
        pass

    @abstractmethod
    def get_symbols(self):
        pass

    # @abstractmethod
    @staticmethod
    def get_wrapper():
        pass
