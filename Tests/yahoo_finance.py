import yfinance as yf

from AdvancedAnalytics.Cupnhandle import find_cupnhandle_and_show_on_data

nasdq_100 = ['VIX', 'AAPL', 'MSFT', 'GOOG', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'FB', 'COST', 'ASML', 'AVGO', 'PEP',
             'NTES', 'CSCO', 'CMCSA', 'AZN',
             'ADBE', 'INTC', 'TMUS', 'TXN', 'QCOM', 'AMD', 'AMGN', 'INTU', 'HON', 'PYPL', 'CHTR', 'ISRG', 'AMAT',
             'NFLX', 'ABNB', 'ADP',
             'SBUX', 'BKNG', 'MDLZ', 'ADI', 'JD', 'MU', 'GILD', 'REGN', 'CSX', 'VRTX', 'TEAM', 'LRCX', 'FISV', 'MAR',
             'PANW', 'ATVI', 'MRNA',
             'WDAY', 'FTNT', 'MELI', 'ILMN', 'KDP', 'MRVL', 'KHC', 'KLAC', 'AEP', 'CRWD', 'PAYX', 'ORLY', 'LULU', 'EXC',
             'DXCM', 'NXPI', 'SNPS',
             'PDD', 'CTSH', 'MNST', 'ADSK', 'CDNS', 'IDXX', 'CTAS', 'BIDU', 'DDOG', 'XEL', 'WBA', 'DLTR', 'MCHP',
             'ROST', 'EA', 'VRSK', 'LCID',
             'ALGN', 'FAST', 'BIIB', 'EBAY', 'ODFL', 'ZS', 'ZM', 'PCAR', 'CPRT', 'SGEN', 'ANSS', 'SIRI', 'MTCH', 'VRSN',
             'OKTA', 'SPLK', 'CEG', 'SWKS', 'DOCU', ]
# msft = yf.Ticker("MSFT")
#
# hist = msft.history(period="max")
# print(hist)


# data = yf.download("SPY AAPL", start="2017-01-01", end="2017-04-30")


print()


def get_y_finance_data():
    tickers = yf.Tickers(','.join(nasdq_100))
    # tickers = yf.Tickers('AAPL,MSFT,AMD,VIX')
    hist = []
    for ticker_str in tickers.symbols:
        period = "10y"
        ticker = tickers.tickers[ticker_str]
        df_h = ticker.history(period=period)
        hist.append((ticker_str, df_h))  # "max"
        df_h.to_csv(f'Tests/yahoo_data/{ticker_str}_{period}.csv')


def run_on_nasdaq():
    from tqdm import tqdm
    import pandas as pd
    import os
    prepath = 'Tests/yahoo_data/'

    print('filtering to last 2 years.')
    for idx, f in tqdm(enumerate(os.listdir(prepath))):
        # print(f)
        symbol = f.split('_')[0]
        df = pd.read_csv(prepath + f, index_col='Date')
        df.index = pd.to_datetime(df.index)
        df = df[df.index > pd.to_datetime('2020-01-01')]
        df.columns = [c.lower() for c in df.columns]
        detected_parts = find_cupnhandle_and_show_on_data(symbol, df, col='close', cupnhandle_treshold=0.017,
                                                          show=True)  # =0.0185
        if idx > 1000:
            break


if __name__ == '__main__':
    # get_y_finance_data()
    run_on_nasdaq()
