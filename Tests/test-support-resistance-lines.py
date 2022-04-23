import plotly.graph_objects as go
from Indicators import SupportResistanceLines


def get_candle(df):
    fig = go.Figure(go.Candlestick(x=df.index,
                                   open=df.open,
                                   high=df.high,
                                   low=df.low,
                                   close=df.close))
    return fig


def run_on_nasdaq_support_lines():
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
        df = df[df.index > pd.to_datetime('2019-01-01')]
        df = df.resample('1D').interpolate()
        df.columns = [c.lower() for c in df.columns]

        fig = get_candle(df)
        ind = SupportResistanceLines()
        ind.calc(df)

        ind.plot(fig)
        fig.update_layout(title=f)
        fig.show()
        if idx > 4:
            break


if __name__ == '__main__':
    # get_y_finance_data()
    run_on_nasdaq_support_lines()
