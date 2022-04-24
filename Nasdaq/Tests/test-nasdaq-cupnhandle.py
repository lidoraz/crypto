import pandas as pd
from tqdm import tqdm
from AdvancedAnalytics.Cupnhandle import find_cupnhandle_and_show_on_data
from Nasdaq.symbols import prepath
import os

# level 2 up
new_path = '/'.join(os.getcwd().split('/')[:-2])
os.chdir(new_path)


# ------------------------------------------------------------------------

def run_on_nasdaq():
    print('filtering to last 2 years.')
    for idx, f in tqdm(enumerate(os.listdir(prepath))):
        # print(f)
        symbol = f.split('_')[0]
        df = pd.read_csv(prepath + f, index_col='Date')
        df.index = pd.to_datetime(df.index)
        df = df[df.index > pd.to_datetime('2019-01-01')]
        df = df.resample('1D').interpolate()
        df.columns = [c.lower() for c in df.columns]
        detected_parts = find_cupnhandle_and_show_on_data(symbol, df, col='close', cupnhandle_treshold=0.017,
                                                          show=True)  # =0.0185
        if idx > 1000:
            break


run_on_nasdaq()
