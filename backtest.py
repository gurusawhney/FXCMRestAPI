try:
    import Queue as queue
except ImportError:
    import queue
import time
import pandas as pd
from socketIO_client import SocketIO

from strategy import TestRandomStrategy, MovingAverageCrossStrategy
from portfolio import Portfolio
from execution import SimulatedExecution
from price import HistoricCSVPriceHandler
from restful import RESTaccessor

class Backtest(object):
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest on the foreign exchange markets.
    """
    def __init__(
        self, pairs, data_handler, strategy,
        strategy_params, portfolio, execution,
        equity=1000000.0, heartbeat=0.0,
        max_iters=10000000000
    ):
        """
        Initialises the backtest.
        """
        self.pairs = pairs
        self.events = queue.Queue()
        self.ticker = data_handler(self.pairs, self.events)
        self.strategy_params = strategy_params
        self.strategy = strategy(
            self.pairs, self.events, **self.strategy_params
        )
        self.equity = equity
        self.heartbeat = heartbeat
        self.max_iters = max_iters
        self.portfolio = portfolio(self.ticker, self.events, backtest=True, equity=self.equity)
        self.execution = execution()

    def _run_backtest(self):
        """
        Carries out an infinite while loop that polls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop will then pause for "heartbeat" seconds and
        continue unti the maximum number of iterations is
        exceeded.
        """
        print("Running Backtest...")
        iters = 0
        while iters < self.max_iters and self.ticker.continue_backtest:
            try:
                event = self.events.get(False)
            except queue.Empty:
                self.ticker.stream_next_tick()
            else:
                if event is not None:
                    if event.type == 'TICK':
                        self.strategy.calculate_signals(event)
                        self.portfolio.update_portfolio(event)
                    elif event.type == 'SIGNAL':
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER':
                        self.execution.execute_order(event)
            time.sleep(self.heartbeat)
            iters += 1

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """
        print("Calculating Performance Metrics...")
        self.portfolio.output_results()

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        self._output_performance()
        print("Backtest complete.")

def generate_historical(pairs):
    RESTaccess = RESTaccessor('1583865',
                              'https://api-demo.fxcm.com:443',
                              443,
                              '4fd104ad7e3086df1e07cd8c9f5c53df94ced618')

    RESTaccess.socketIO = SocketIO(RESTaccess.TRADING_API_URL, RESTaccess.WEBSOCKET_PORT,
                                   params={'access_token': RESTaccess.ACCESS_TOKEN})
    RESTaccess.socketIO.on('connect', RESTaccess.on_connect)
    RESTaccess.socketIO.on('disconnect', RESTaccess.on_close)
    RESTaccess.bearer_access_token = RESTaccess.create_bearer_token(RESTaccess.ACCESS_TOKEN,
                                                                    RESTaccess.socketIO._engineIO_session.id)
    # after /candles the number 1 is the offer ID (instrument EUR/USD) and the D1 is the candlestick period
    hist_status, hist_response = RESTaccess.request_processor('/candles/1/H1', {
        'num': 1000,
        'from': 1494086400,
        'to': 1503835200
    })
    if hist_status is True:
        hist_data = hist_response['candles']
        df = pd.DataFrame(hist_data)
        df.columns = ["time", "bidopen", "bidclose", "bidhigh", "bidlow", "askopen", "askclose", "askhigh",
                      "asklow", "TickQty"]
        df["time"] = pd.to_datetime(df["time"], unit='s')
        df["time"] = df["time"].values.astype('datetime64[D]')
        df.set_index("time", inplace=True)
        df.to_csv("%s.csv" % pairs[0].replace("/",""))

if __name__ == "__main__":
    # Trade on EUR/USD
    pairs = ["EUR/USD"]
    # Create the strategy parameters for the
    # MovingAverageCrossStrategy
    strategy_params = {
        "short_window": 10,
        "long_window": 50
    }
    generate_historical(pairs)
    # Create and execute the backtest
    backtest = Backtest(
        pairs, HistoricCSVPriceHandler, MovingAverageCrossStrategy,
        strategy_params, Portfolio, SimulatedExecution
    )
    backtest.simulate_trading()