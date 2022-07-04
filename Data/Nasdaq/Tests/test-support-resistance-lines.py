import plotly.graph_objects as go
from Indicators import SupportResistanceLines2
from tqdm import tqdm
import pandas as pd
from AStock.symbols import NASDAQ_PREPATH
import os

# level 2 up
new_path = '/'.join(os.getcwd().split('/')[:-2])
os.chdir(new_path)


# ------------------------------------------------------------------------


def get_candle(df):
    fig = go.Figure(go.Candlestick(x=df.index,
                                   open=df.open,
                                   high=df.high,
                                   low=df.low,
                                   close=df.close))
    return fig


def run_on_nasdaq_support_lines():
    print('filtering to last 2 years.')
    for idx, f in tqdm(enumerate(os.listdir(NASDAQ_PREPATH))):
        # print(f)
        symbol = f.split('_')[0]
        df = pd.read_csv(NASDAQ_PREPATH + f, index_col='Date')
        df.index = pd.to_datetime(df.index)
        df = df[df.index > pd.to_datetime('2019-01-01')]
        df = df.resample('1D').interpolate()
        df.columns = [c.lower() for c in df.columns]

        fig = get_candle(df)
        ind = SupportResistanceLines2()
        ind.calc(df)

        ind.plot(fig)
        fig.update_layout(title=f)
        fig.show()
        if idx > 4:
            break


if __name__ == '__main__':
    run_on_nasdaq_support_lines()
