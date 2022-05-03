from abc import abstractmethod, ABC


class ProviderData(ABC):

    @abstractmethod
    def get_data(self, symbol: str, tf: str):
        pass

    @abstractmethod
    def get_symbols(self):
        pass

    @abstractmethod
    def get_preloaded(self, tfs):
        pass

    @staticmethod
    def get_wrapper(*args, **kwargs):
        pass


class PreLoaded(ProviderData):
    def __init__(self, data, symbols):
        self.data = data
        self.symbols = symbols

    def get_data(self, symbol: str, tf: str):
        return self.data[f'{symbol}{tf}']

    def get_symbols(self):
        return self.symbols

    def get_preloaded(self, tfs):
        pass

    def get_wrapper(*args, **kwargs):
        pass
