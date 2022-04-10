from .traces import get_MAD, get_FibMAD, get_EMA


def add_moving_avgs(fig, ohlc, col='close', loc=(1, 1)):
    lookaheads = [7, 25, 99]
    colors = ['orange', 'purple', 'cyan']
    for lookahead, color in zip(lookaheads, colors):
        fig.add_trace(get_MAD(ohlc, lookahead, col=col, color=color), row=loc[0], col=loc[1])


def add_special_moving_avgs(fig, ohlc, col='close', show=True):
    if show:
        fig.add_trace(get_FibMAD(ohlc, 7, col=col, color='yellow'), row=1, col=1)
        fig.add_trace(get_EMA(ohlc, 7, col=col, color='orange'), row=1, col=1)
