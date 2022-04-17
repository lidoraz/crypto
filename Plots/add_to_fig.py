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
    plot_kwargs = dict(name=name, line_color='DarkViolet', line_width=0.2, legendgroup=name, visible='legendonly')
    fig.add_trace(go.Scatter(x=sma.index, y=sma, name=f'SMA({lookahead})',
                             line_color='purple', legendgroup=name, line_width=0.2))
    fig.add_trace(go.Scatter(x=top_BB.index, y=top_BB, fill=None, mode='lines',
                             **plot_kwargs))
    fig.add_trace(go.Scatter(x=bot_BB.index, y=bot_BB, fill='tonexty', mode='lines',
                             fillcolor="rgba(148, 0, 211, 0.15)",
                             **plot_kwargs))


def add_special_moving_avgs(fig, ohlc, col='close'):
    fig.add_trace(get_FibMAD(ohlc, 25, col=col, color='Pink'), row=1, col=1)
    fig.add_trace(get_EMA(ohlc, 25, col=col, color='Red'), row=1, col=1)
