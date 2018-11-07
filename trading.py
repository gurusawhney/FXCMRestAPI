import queue
import threading
import time
from socketIO_client import SocketIO
import logging

from execution import Execution
from strategy import TestRandomStrategy, MovingAverageCrossStrategy, NewsDrivenStrategy
from streaming import StreamingForexPrices
from restful import RESTaccessor
from portfolio import Portfolio


def trade(events, strategy, portfolio, execution, heartbeat):
    """
    Carries out an infinite while loop that polls the
    events queue and directs each event to either the
    strategy component of the execution handler. The
    loop will then pause for "heartbeat" seconds and
    continue.
    """
    while True:
        try:
            event = events.get(False)
        except queue.Empty:
            pass
        else:
            if event is not None:
                if event.type == 'TICK':
                    strategy.calculate_signals(event)
                    portfolio.update_portfolio(event)
                elif event.type == 'SIGNAL':
                    portfolio.execute_signal(event)
                elif event.type == 'ORDER':
                    execution.execute_order(event)
        time.sleep(heartbeat)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(filename = 'trading.log', level = logging.INFO)
    logger = logging.getLogger('EventDrivenBacktester.trading.log')

    # Half a second between polling
    heartbeat = 0.5
    # Events for trading
    events = queue.Queue()

    # Trade 1000 units of EUR/USD
    instrument = ["EUR/USD"]
    units = 1000

    #Authenticating the connection to REST API service
    RESTaccess = RESTaccessor('1583865',
                              'https://api-demo.fxcm.com:443',
                              443,
                              '4fd104ad7e3086df1e07cd8c9f5c53df94ced618')

    RESTaccess.socketIO = SocketIO(RESTaccess.TRADING_API_URL, RESTaccess.WEBSOCKET_PORT, params={'access_token': RESTaccess.ACCESS_TOKEN})
    RESTaccess.socketIO.on('connect', RESTaccess.on_connect)
    RESTaccess.socketIO.on('disconnect', RESTaccess.on_close)
    RESTaccess.bearer_access_token = RESTaccess.create_bearer_token(RESTaccess.ACCESS_TOKEN, RESTaccess.socketIO._engineIO_session.id)
    # Create the FXCM market price streaming class
    # making sure to provide authentication commands
    prices = StreamingForexPrices(RESTaccess, instrument, events)

    # Create the portfolio object that will be used to
    # compare the OANDA positions with the local, to
    # ensure backtesting integrity.
    portfolio = Portfolio(prices, events, backtest = False, equity=1000000.0)

    # Create the execution handler making sure to
    # provide authentication commands
    execution = Execution(RESTaccess)

    # Create the strategy/signal generator, passing the
    # instrument, quantity of units and the events queue
    #strategy = TestRandomStrategy(instrument, events)
    strategy = MovingAverageCrossStrategy(instrument,events)
    #strategy = NewsDrivenStrategy(instrument,events)

    # Create two separate threads: One for the trading loop
    # and another for the market price streaming class
    trade_thread = threading.Thread(target=trade, args=(events, strategy, portfolio, execution, heartbeat))
    price_thread = threading.Thread(target=prices.stream_to_queue, args=[])
    # Start both threads
    logger.info("Starting trading thread")
    trade_thread.start()
    logger.info("Starting price streaming thread")
    price_thread.start()
    RESTaccess.socketIO.wait()

