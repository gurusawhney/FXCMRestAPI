
from decimal import Decimal, getcontext, ROUND_HALF_DOWN
import pandas as pd

from event import TickEvent

class HistoricCSVPriceHandler(object):
    """
    HistoricCSVPriceHandler is designed to read CSV files of
    tick data for each requested currency pair and stream those
    to the provided events queue.
    """
    def __init__(self, pairs, events_queue):
        """
        Initialises the historic data handler by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'pair.csv', where "pair" is the currency pair. For
        GBP/USD the filename is GBPUSD.csv.
        """
        self.pairs = pairs
        self.events_queue = events_queue
        self.prices = self.set_up_prices_dict()
        self.pair_frames = {}
        self.continue_backtest = True
        self.cur_date_indx = 0

    def set_up_prices_dict(self):
        price_dict = dict(
            (k, v) for k,v in [
                (p, {"bid": None, "ask": None, "time": None}) for p in self.pairs
            ]
        )
        return price_dict


    def stream_next_tick(self):
        """
        The Backtester has now moved over to a single-threaded
        model in order to fully reproduce results on each run.
        This means that the stream_to_queue method is unable to
        be used and a replacement, called stream_next_tick, is
        used instead.

        This method is called by the backtesting function outside
        of this class and places a single tick onto the queue, as
        well as updating the current bid/ask and inverse bid/ask.
        """
        df = pd.read_csv("%s.csv" % self.pairs[0].replace("/",""))
        end = len(df)
        if(self.cur_date_indx < end):
            row = df[self.cur_date_indx:(self.cur_date_indx + 1)]
            bid = Decimal(str(row["bidopen"][self.cur_date_indx])).quantize(Decimal("0.00001"))
            ask = Decimal(str(row["askopen"][self.cur_date_indx])).quantize(Decimal("0.00001")        )
            time = row["time"][self.cur_date_indx]
            # Create decimalised prices for traded pair
            self.prices[self.pairs[0]]["bid"] = bid
            self.prices[self.pairs[0]]["ask"] = ask
            self.prices[self.pairs[0]]["time"] = time
            # Create the tick event for the queue
            tev = TickEvent(self.pairs[0], time, bid, ask)
            self.events_queue.put(tev)
            self.cur_date_indx += 1
        else:
            self.continue_backtest = False
            return