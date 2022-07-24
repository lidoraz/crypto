import yfinance as yf
import time
import pandas as pd

from AStock.gaps import snp500_stocks, selected_stocks


def get_daily_data(symbols, days_before):
    t0 = time.time()
    end = int(time.time())
    # days_before = 720  # 2 years
    start = end - 60 * 60 * 24 * days_before
    start = pd.to_datetime(start, unit='s', utc=True)

    data = yf.download(' '.join(symbols), start=start, end=None,
                       # prepost=True,  # include pre/post market data
                       rounding=True,
                       actions=True,  # dividend + stock splits data
                       group_by='ticker',  # default is on columns. ticker is easier to iterate
                       auto_adjust=False,  # false on default, what does it do?
                       show_errors=True,
                       interval='1d', threads=True, progress=False)
    print(f"start={start}, data: {str(data.index[-1])} took: {time.time() - t0:0.2f}")
    data['DT'] = data.index
    data['Date'] = data.index.date
    # data['Type'] = data['DT'].apply(extract_market_type)
    return data


def find_gaps_daily(symbol, data, show_old_gaps=False):
    # symbol = 'AMZN'
    df = data[symbol].copy()
    # Gaps are formed when there is a gap between prev low to next high, or from prev ligh to next low.
    df['prev_High'] = df['High'].shift(1)
    df['prev_Low'] = df['Low'].shift(1)
    min_gap_pct = 0.03
    gap_up_pct = df['Low'] / df['prev_High'] - 1
    gap_down_pct = df['High'] / df['prev_Low'] - 1
    df['is_gap_up'] = (gap_up_pct > min_gap_pct)
    df['is_gap_down'] = (gap_down_pct < -min_gap_pct)
    df['has_gap'] = df['is_gap_up'] | df['is_gap_down']
    df['gap_up_pct'] = gap_up_pct
    df['gap_down_pct'] = gap_down_pct
    # Has closed gap?
    df_gaps = df[df['has_gap']]
    n_closed = 0
    n_gaps = len(df_gaps)
    for gap_time, row in df_gaps.iterrows():
        if row['is_gap_up']:
            is_closed_lst = df[df.index > gap_time]['Low'] < row['prev_High']
            gap_pct = row['gap_up_pct']
        elif row['is_gap_down']:
            is_closed_lst = df[df.index > gap_time]['High'] > row['prev_Low']
            gap_pct = row['gap_down_pct']
        else:
            raise ValueError
        if is_closed_lst.any():
            close_time = is_closed_lst[is_closed_lst].index[0].date()
            n_closed += 1
            if show_old_gaps:
                print(f'{symbol}, had Gap at: {gap_time.date()}, of {gap_pct:0.2%} Closed at: {close_time}')
        else:
            close_time = None
            print(f'{symbol}, has unclosed Gap at: {gap_time.date()}, of {gap_pct:0.2%}')
    if show_old_gaps:
        if n_gaps == 0:
            print(f'{symbol} - No gaps')
        else:
            print(f'{symbol}, gaps: {n_gaps}, closed: {n_closed}, {n_closed / n_gaps : 0.2%}')
    return n_gaps, n_closed


def find_daily_gaps(symbols, days_before, show_old_gaps):
    data = get_daily_data(symbols, days_before)
    total_gaps = 0
    total_closed = 0
    # Check on all snp500 /
    for symbol in symbols:
        n_gaps, n_closed = find_gaps_daily(symbol, data, show_old_gaps)
        total_gaps += n_gaps
        total_closed += n_closed
    print(f'TOTAL closed gaps: {total_gaps}, {total_closed}, {total_closed / total_gaps:0.2%}')


if __name__ == '__main__':
    # MAYBE ADD VOLATILITY DURING PREMARKT - something like the GAP rules for snp500
    symbols = snp500_stocks(150)
    symbols = set(symbols + selected_stocks())
    # FILTER STOCKS WITH VOLUME HIGHER THAN 1M STOCKS PER DAY.
    pd.set_option('display.max_rows', 500)
    days_from = 365
    show_old_gaps = False
    find_daily_gaps(symbols, days_from, show_old_gaps)
    # find_gaps(symbols)
