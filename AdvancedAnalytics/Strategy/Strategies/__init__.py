# from .utils import mark_enter_exit_points
from .RSI_BB import RsiBB
from .BB import BB
from .MACross import MACross
from .Strategy import Strategy

All_STRATEGIES = dict(RSIBB=RsiBB,
                      BB=BB,
                      MACROSS=MACross)
