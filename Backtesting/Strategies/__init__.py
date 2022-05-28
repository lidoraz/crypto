# from .utils import mark_enter_exit_points
from .RSI_BB import RSIBB
from .BB import BB
from .MACross import MACross
from .SMAStochRSI import SMAStochRSI
from .SMAMACD import SMAMACD
from .Strategy import Strategy

All_STRATEGIES = dict(RSIBB=RSIBB,
                      BB=BB,
                      MACROSS=MACross,
                      RSISTO=SMAStochRSI,
                      SMAMACD=SMAMACD)
