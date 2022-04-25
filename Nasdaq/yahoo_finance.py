from Nasdaq.symbols import NASDAQ_PREPATH
from tqdm import tqdm
import yfinance as yf


def get_y_finance_data():
    from Nasdaq.symbols import nasdq_100
    from Nasdaq.symbols import ta_125

    ticker_lst = ta_125[:10]

    tickers = yf.Tickers(','.join(ticker_lst))
    # tickers = yf.Tickers('AAPL,MSFT,AMD,VIX')
    for ticker_str in tqdm(tickers.symbols):
        period = "10y"
        ticker = tickers.tickers[ticker_str]
        df_h = ticker.history(period=period)
        df_h.to_csv(NASDAQ_PREPATH + f'{ticker_str}_{period}.csv')


if __name__ == '__main__':
    get_y_finance_data()
