import copy
from event import SignalEvent

import pandas as pd
from newsmanaging import FXCMEconCal

class Strategy(object):
    pass

class TestRandomStrategy(Strategy):
    def __init__(self, instrument, events):
        self.instrument = instrument
        self.events = events
        self.ticks = 0
        self.invested = False

    def calculate_signals(self, event):
        if event.type == 'TICK':
            self.ticks += 1
            if self.ticks % 5 == 0:
                if self.invested == False:
                    signal = SignalEvent(event.instrument, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    self.invested = True
                else:
                    signal = SignalEvent(event.instrument, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    self.invested = False


class MovingAverageCrossStrategy(Strategy):
    def __init__(
        self, pairs, events,
        short_window = 5, long_window = 20
    ):
        self.pairs = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

    def create_pairs_dict(self):
        attr_dict = {
            "ticks": 0,
            "invested": False,
            "short_sma": None,
            "long_sma": None
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calc_rolling_sma(self, sma_m_1, window, price):
        return ((sma_m_1 * (window - 1)) + price) / window

    def calculate_signals(self, event):
        if event.type == 'TICK':
            pair = event.instrument
            price = event.bid
            pd = self.pairs_dict[pair]
            print(str(pd["short_sma"]) + " & " + str(pd["long_sma"]))
            if pd["ticks"] == 0:
                pd["short_sma"] = price
                pd["long_sma"] = price
            else:
                pd["short_sma"] = self.calc_rolling_sma(
                    pd["short_sma"], self.short_window, price
                )
                pd["long_sma"] = self.calc_rolling_sma(
                    pd["long_sma"], self.long_window, price
                )
            # Only start the strategy when we have created an accurate short window
            if pd["ticks"] > self.short_window:
                if pd["short_sma"] > pd["long_sma"] and not pd["invested"]:
                    signal = SignalEvent(pair, "AtMarket", "true", event.time)
                    self.events.put(signal)
                    pd["invested"] = True
                if pd["short_sma"] < pd["long_sma"] and pd["invested"]:
                    signal = SignalEvent(pair, "AtMarket", "false", event.time)
                    self.events.put(signal)
                    pd["invested"] = False
            pd["ticks"] += 1

class NewsDrivenStrategy(Strategy):
    def __init__(self, instrument, events):
        self.quote = instrument[:3]
        self.base = instrument[4:]
        self.events = events
        self.news = FXCMEconCal(instrument)

    def UpdateData(self):
        self.news = self.news.createNewsData()

    def calculate_signals(self,event):
        if event.type == 'TICK':
            self.UpdateData()
            data = self.news.data
            event = data.tail(1)
            if(event['trading'].iloc[0] == False):
                if(event['actual'].iloc[0] < event['previous'].iloc[0]):
                    if(event['currency'] == self.base):
                        signal = SignalEvent(event.instrument, "AtMarket", "true", event.time)
                        self.events.put(signal)
                    if(event['currency'] == self.quote):
                        signal = SignalEvent(event.instrument, "AtMarket", "false", event.time)
                        self.events.put(signal)
                if (event['actual'].iloc[0] > event['previous'].iloc[0]):
                    if (event['currency'] == self.base):
                        signal = SignalEvent(event.instrument, "AtMarket", "false", event.time)
                        self.events.put(signal)
                    if (event['currency'] == self.quote):
                        signal = SignalEvent(event.instrument, "AtMarket", "true", event.time)
                        self.events.put(signal)
                self.news.data.set_value(event.index, 'trader', True)
