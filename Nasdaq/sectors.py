import yfinance as yf
import time
import pandas as pd


def get_daily_data(symbols, n_months=6):
    t0 = time.time()

    months_before = 30 * n_months
    start = int(t0) - 60 * 60 * 24 * months_before  # 1 day before
    start = str(pd.to_datetime(start, unit='s', utc=True).date())
    print('Starting From:', start)
    data = yf.download(' '.join(symbols), start=start, end=None,
                       rounding=True,
                       # group_by='ticker',  # default is on columns. ticker is easier to iterate
                       auto_adjust=False,  # false on default, what does it do?
                       show_errors=True,
                       interval='1d', threads=True, progress=False)
    print(f"start={start}, data: {str(data.index[-1])} took: {time.time() - t0:0.2f}")
    return data


# ETF usually contains 2 giant companies with 20% each, and rest are smaller
all_etf_longname = {
    'SPY': 'S&P500',
    'QQQ': 'Nasdaq100',
    'XLE': 'Enregy(XOM,CVX..)',
    'XLF': 'Finance(BRK.B,JPM..)',
    # 'XLB': 'Materials(LIN,SHW..)',
    # 'XLI': 'Industrial(CAT,LK,GE)',
    # 'XLK': 'Tech(MSFT,AAPL,NVDA..)',
    'XLP': 'Consumer(PG,KO..)',
    # 'XLU': 'Utilities(NEE,DOK..)',
    'XLV': 'Healthcare(JJ,PFE..)',
    'XLY': 'Consumer(AMZN,TSLA..)',
    # 'XLC': 'Communications(META,GOOGL..)',
    # 'XLRE': 'Real Estate',
    'SMH': 'SemiConductor vaneck',
    # 'XSD': 'SemiConductor iShares',
    'JETS': 'Airlines',
    'URTH': 'ACWI World',
}
import plotly.graph_objects as go


def visualize(data, norm=True):
    fig = go.Figure()
    from sklearn.preprocessing import MinMaxScaler, StandardScaler
    # scale =
    data = data['Close']
    data = data.resample('1W').last()
    # for c in data.columns:
    for c in all_etf_longname.keys():
        print(c)
        c_data = data[c]
        if norm:
            c_data = c_data / c_data[0] - 1
            # c_data = StandardScaler().fit_transform(c_data.values.reshape(-1, 1)).reshape(-1)
        name = f'{all_etf_longname[c]}({c})'
        fig.add_trace(go.Scatter(name=name, x=data.index, y=c_data,
                                 hovertemplate=c + ': %{y:.2%}<extra></extra>',
                                 mode='lines'))  # , mode='lines+markers'
    # fig = px.scatter(df, x=df.index, y='volume', name=coin, # color=coin
    #                  )
    since = (data.index[-1] - data.index[0]).days / 30
    fig.update_layout(title_text=f'ETFs, since: {data.index[0].date()}, norm={norm}, {since: 0.1f} Months ago')
    fig.update_layout(hovermode="x unified")
    fig.update_layout(template="plotly_dark", )
    fig.layout.yaxis.tickformat = ',.0%'
    # fig.show()
    return fig

def get_etf_stats():
    tf = [3, 6, 12, 24, 48, 96]
    # tf = [48]
    for n_months in tf:
        data = get_daily_data(list(all_etf_longname.keys()), n_months=n_months)
        visualize(data, norm=True)
    # print(data.head())


def save_to_html():
    n_months = 48
    data = get_daily_data(list(all_etf_longname.keys()), n_months=n_months)
    fig = visualize(data, norm=True)

    fig.write_html(f'etfs_{n_months}.html')

if __name__ == '__main__':
    # get_etf_stats()
    save_to_html()
