from plotly import graph_objects as go
from .traces import get_SMA, get_FibMAD, get_EMA


def add_moving_avgs(fig, ohlc, col='close', loc=(1, 1)):
    lookaheads = [7, 25, 99]
    colors = ['orange', 'purple', 'cyan']
    for lookahead, color in zip(lookaheads, colors):
        fig.add_trace(get_SMA(ohlc, lookahead, col=col, color=color), row=loc[0], col=loc[1])


# TODO: deprectead
def add_bollinger_bands(fig, ohlc, col='close', loc=(1, 1)):
    lookahead = 25
    std = 2
    rolling_func = ohlc[col].rolling(lookahead)
    sma = rolling_func.mean()
    top_BB = sma + rolling_func.std() * std
    bot_BB = sma - rolling_func.std() * std
    name = f'BB({lookahead})'
    # fig.add_trace(go.Scatter(x=sma.index, y=sma, name=f'SMA({lookahead})', line_color='purple', legendgroup=name, line_width=1))
    fig.add_trace(go.Scatter(x=top_BB.index, y=top_BB, name=name, line_color='purple', line_width=1, legendgroup=name,
                             opacity=0.2, visible='legendonly'))
    fig.add_trace(go.Scatter(x=bot_BB.index, y=bot_BB, fill='tonexty', name=name, line_color='purple', line_width=1,
                             legendgroup=name, opacity=0.2, visible='legendonly'))


def add_special_moving_avgs(fig, ohlc, col='close'):
    fig.add_trace(get_FibMAD(ohlc, 25, col=col, color='Pink'), row=1, col=1)
    fig.add_trace(get_EMA(ohlc, 25, col=col, color='Red'), row=1, col=1)
