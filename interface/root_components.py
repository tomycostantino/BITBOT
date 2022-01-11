import tkinter as tk

from connectors.binance_futures import BinanceFuturesClient

import logging
from tkinter.messagebox import askquestion
from interface.styling import *
from interface.logging_component import Logging
from interface.watchlist_components import Watchlist
from interface.trades_component import TradesWatch
from interface.strategy_components import StrategyEditor
logger = logging.getLogger()


class Root(tk.Tk):
    def __init__(self, binance: BinanceFuturesClient):
        super().__init__()

        self.binance = binance

        self.title('Trading Bot')

        self.protocol('WM_DELETE_WINDOW', self._ask_before_close)

        # background color
        self.configure(bg=BG_COLOR_2)

        # create left frame
        self._left_frame = tk.Frame(self, bg=BG_COLOR)
        self._left_frame.pack(side=tk.LEFT)

        # create right frame
        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tk.LEFT)

        self._watchlist_frame = Watchlist(self.binance.contracts, self._left_frame, bg=BG_COLOR_2)
        self._watchlist_frame.pack(side=tk.TOP)

        self.logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self.logging_frame.pack(side=tk.TOP)

        self._strategy_frame = StrategyEditor(self, self.binance, self._right_frame, bg=BG_COLOR)
        self._strategy_frame.pack(side=tk.TOP)

        self._trades_frame = TradesWatch(self._right_frame, bg=BG_COLOR)
        self._trades_frame.pack(side=tk.TOP)

        self.update_ui()

    def _ask_before_close(self):
        result = askquestion('Confirmation', 'Do you really want to exit the application?')
        if result == 'yes':
            self.binance.reconnect = False
            self.binance.ws.close()

            self.destroy()

    def update_ui(self):

        for log in self.binance.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        # trades and logs

        try:

            for b_index, strat in self.binance.strategies.items():
                for log in strat.logs:
                    if not log['displayed']:
                        self.logging_frame.add_log(log['log'])
                        log['displayed'] = True

                for trade in strat.trades:
                    if trade.time not in self._trades_frame.body_widgets['symbol']:
                        self._trades_frame.add_trade(trade)

                    if trade.contract.exchange == 'binance':
                        precision = trade.contract.price_decimals
                    else:
                        precision = 8

                    pnl_str = '{0:.{prec}f}'.format(trade.pnl, prec=precision)
                    self._trades_frame.body_widgets['pnl_var'][trade.time].set(pnl_str)
                    self._trades_frame.body_widgets['status_var'][trade.time].set(trade.status.capitalize())

        except RuntimeError as e:
            logger.error('Error while looping through strategies dictionary')

        # watchlist prices

        try:
            for key, value in self._watchlist_frame.body_widgets['symbol'].items():

                symbol = self._watchlist_frame.body_widgets['symbol'][key].cget('text')
                exchange = self._watchlist_frame.body_widgets['exchange'][key].cget('text')

                if exchange == 'Binance':
                    if symbol not in self.binance.contracts:
                        continue

                    if symbol not in self.binance.prices:
                        self.binance.get_bid_ask(self.binance.contracts[symbol])

                    # precision = self.binance.prices[symbol].price_decimals

                    prices = self.binance.prices[symbol]

                if prices['bid'] is not None:
                    # price_str = '{0:.{prec}f}'.format(prices['bid'], prec=precision)
                    self._watchlist_frame.body_widgets['bid_var'][key].set(prices['bid'])

                if prices['ask'] is not None:
                    # price_str = '{0:.{prec}f}'.format(prices['bid'], prec=precision)
                    self._watchlist_frame.body_widgets['ask_var'][key].set(prices['ask'])

        except RuntimeError as e:
            logger.error('Error while looping through watchlist dictionary')

        self.after(1500, self.update_ui)
