import json
import logging
from event import TickEvent

class StreamingForexPrices(object):
    def __init__(self, RESTaccess, instrument, events_queue):
        self.RESTaccess = RESTaccess
        self.instruments = instrument
        self.events_queue = events_queue
        self.prices = self.set_up_prices_dict()
        self.logger = logging.getLogger(__name__)

    def stream_to_queue(self):
        print(self.RESTaccess.ACCESS_TOKEN)
        for key in self.instruments:
            status,response = self.RESTaccess.post_request_processor('/subscribe', {'pairs': key})
            if status is True:
                self.RESTaccess.socketIO.on(key, self.on_price_update)
                print(response)
            else:
                print(("Error processing request: /subscribe: " + str(response)))

    def set_up_prices_dict(self):
        price_dict = dict(
            (k, v) for k,v in [
                (p, {"bid": None, "ask": None, "time": None}) for p in self.instruments
            ]
        )
        return price_dict

    def on_price_update(self, msg):
        response = json.loads(msg)
        self.logger.info(response)
        print(response)
        time = response["Updated"]
        bid = response["Rates"][0]
        ask = response["Rates"][1]
        symbol = response["Symbol"]
        self.cur_ask = ask
        self.cur_bid = bid
        self.prices[symbol]["bid"] = bid
        self.prices[symbol]["ask"] = ask
        self.prices[symbol]["time"] = time
        tev = TickEvent(symbol, time, bid, ask)
        self.events_queue.put(tev)