import logging
import pandas as pd

from copy import deepcopy
from event import OrderEvent
from position import Position

class Portfolio(object):
    def __init__(
            self, ticker, events, backtest, base="USD", leverage=1,
            equity= 1000000.00, risk_per_trade = 0.002,
    ):
        self.ticker = ticker
        self.events = events
        self.base = base
        self.leverage = leverage
        self.equity = equity
        self.balance = deepcopy(self.equity)
        self.risk_per_trade = risk_per_trade
        self.backtest = backtest
        self.trade_units = self.calc_risk_position_size()
        self.positions = {}
        if self.backtest:
            self.backtest_file = self.create_equity_file()
        self.logger = logging.getLogger(__name__)

    def calc_risk_position_size(self):
        #the amount size per trade is per 1k
        return (self.equity * self.risk_per_trade)/1000

    def add_new_position(self, position_type, currency_pair, units):
        ps = Position(self.base, position_type, currency_pair, units, self.ticker)
        self.positions[currency_pair] = ps

    def add_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            ps.add_units(units)
            return True

#TODO allow the removal of units in a position
    def remove_position_units(self, currency_pair, units):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            pnl = ps.remove_units(units)
            self.balance += pnl
            return True

    def close_position(self, currency_pair):
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            pnl = float(ps.close_position())
            self.balance += pnl
            del [self.positions[currency_pair]]
            return True

    def update_portfolio(self, tick_event):
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (PnL).
        """
        currency_pair = tick_event.instrument
        if currency_pair in self.positions:
           ps = self.positions[currency_pair]
           ps.update_position_price()
        if self.backtest:
            out_line = "%s,%s" % (tick_event.time, self.balance)
            for pair in self.ticker.pairs:
                if pair in self.positions:
                    out_line += ",%s" % self.positions[pair].profit_base
                else:
                    out_line += ",0.00"
            out_line += "\n"
            print(out_line[:-2])
            self.backtest_file.write(out_line)

    def create_equity_file(self):
        filename = "backtest.csv"
        out_file = open(filename, "w")
        header = "Timestamp,Balance"
        for pair in self.ticker.pairs:
            header += ",%s" % pair
        header += "\n"
        out_file.write(header)
        if self.backtest:
            print(header[:-2])
        return out_file

    def output_results(self):
        # Closes off the Backtest.csv file so it can be
        # read via Pandas without problems
        self.backtest_file.close()
        in_filename = "backtest.csv"
        out_filename = "equity.csv"
        in_file = in_filename
        out_file = out_filename
        # Create equity curve dataframe
        df = pd.read_csv(in_file, index_col=0)
        df.dropna(inplace=True)
        df["Total"] = df.sum(axis=1)
        df["Returns"] = df["Total"].pct_change()
        df["Equity"] = (1.0 + df["Returns"]).cumprod()
        # Create drawdown statistics
        drawdown, max_dd, dd_duration = self.create_drawdowns(df["Equity"])
        df["Drawdown"] = drawdown
        df.to_csv(out_file, index=True)
        print("Simulation complete and results exported to %s" % out_filename)

    def create_drawdowns(self, pnl):
        """
        Calculate the largest peak-to-trough drawdown of the PnL curve
        as well as the duration of the drawdown. Requires that the
        pnl_returns is a pandas Series.
        Parameters:
        pnl - A pandas Series representing period percentage returns.
        Returns:
        drawdown, duration - Highest peak-to-trough drawdown and duration.
        """
        # Calculate the cumulative returns curve
        # and set up the High Water Mark
        hwm = [0]
        # Create the drawdown and duration series
        idx = pnl.index
        drawdown = pd.Series(index=idx)
        duration = pd.Series(index=idx)
        # Loop over the index range
        for t in range(1, len(idx)):
           hwm.append(max(hwm[t - 1], pnl.iloc[t]))
           drawdown.iloc[t] = (hwm[t] - pnl.iloc[t])
           duration.iloc[t] = (0 if drawdown.iloc[t] == 0 else duration.iloc[t - 1] + 1)
        return drawdown, drawdown.max(), duration.max()

    def execute_signal(self, signal_event):
        side = signal_event.side
        currency_pair = signal_event.instrument
        units = int(self.trade_units)
        # If there is no position, create one
        if currency_pair not in self.positions:
            if side == "true":
                position_type = "long"
            else:
                position_type = "short"
            self.add_new_position( position_type, currency_pair, units)
        # If a position exists add or remove units
        else:
            ps = self.positions[currency_pair]
            if side == "true" and ps.position_type == "long":
                self.add_position_units(currency_pair, units)
            elif side == "false" and ps.position_type == "long":
                self.close_position(currency_pair)
            elif side == "true" and ps.position_type == "short":
                self.close_position(currency_pair)
            elif side == "false" and ps.position_type == "short":
                self.add_position_units(currency_pair, units)

        order = OrderEvent(currency_pair, units, "AtMarket", side)
        self.logger.info(order)
        self.events.put(order)
        self.logger.info("Portfolio Balance: %0.2f" % self.balance)
