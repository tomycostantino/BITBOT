import typing

from keys import *
import tkinter as tk
import json
from connectors.binance import BinanceClient
from connectors.bitmex import BitmexClient

import logging
import variables
from tkinter.messagebox import askquestion
from interface.styling import *
from interface.logging_component import Logging
from interface.watchlist_components import Watchlist
from interface.trades_component import TradesWatch
from interface.strategy_components import StrategyEditor
logger = logging.getLogger()


class Root(tk.Tk):
    def __init__(self):
        super().__init__()

        self._binance = variables.binance
        self._bitmex = variables.bitmex

        self.title('Trading Bot')

        self.protocol('WM_DELETE_WINDOW', self._ask_before_close)

        # background color
        self.configure(bg=BG_COLOR_2)

        # menu bar on top
        self._main_menu = tk.Menu(self)
        self.configure(menu=self._main_menu)

        # sub menu to save and load workspace on database
        self._workspace_menu = tk.Menu(self._main_menu, tearoff=False)
        self._main_menu.add_cascade(label="Workspace", menu=self._workspace_menu)
        self._workspace_menu.add_command(label="Save workspace", command=self._save_workspace)
        self._workspace_menu.add_command(label="Load workspace", command=self._load_workspace)

        self._restart = tk.Menu(self._main_menu, tearoff=False)
        self._main_menu.add_cascade(label='Restart', menu=self._restart)
        self._restart.add_cascade(label='Restart program', command=self._restart_code)

        # create left frame
        self._left_frame = tk.Frame(self, bg=BG_COLOR, borderwidth=2, relief=tk.RAISED)
        self._left_frame.pack(side=tk.LEFT, fill=tk.Y)

        # create right frame
        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tk.LEFT, fill=tk.Y)

        # create watchlist component
        self._watchlist_frame = Watchlist(self._binance.contracts, self._bitmex.contracts, self._left_frame,
                                          bg=BG_COLOR, borderwidth=1, relief=tk.RAISED)
        self._watchlist_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # create logging frame under watchlist
        self.logging_frame = Logging(self._left_frame, bg=BG_COLOR, borderwidth=1, relief=tk.RAISED)
        self.logging_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # create the strategy component
        self._strategy_frame = StrategyEditor(self, self._binance, self._bitmex, self._right_frame, bg=BG_COLOR,
                                              borderwidth=1, relief=tk.RAISED)
        self._strategy_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # create the trade component under strategy
        self._trades_frame = TradesWatch(self._right_frame, bg=BG_COLOR, borderwidth=1, relief=tk.RAISED)
        self._trades_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._update_ui()

    def _ask_before_close(self):
        result = askquestion('Confirmation', 'Do you really want to exit the application?')
        if result == 'yes':
            variables.restart = False
            self._binance.reconnect = False
            self._bitmex.reconnect = False
            self._binance.ws.close()
            self._bitmex.ws.close()

            self.destroy()

    def _update_ui(self):

        """
        Called by itself every 1500 seconds. It is similar to an infinite loop but runs within the same Thread
        as .mainloop() thanks to the .after() method, thus it is "thread-safe" to update elements of the interface
        in this method. Do not update Tkinter elements from another Thread like the websocket thread.
        :return:
        """

        # Logs

        for log in self._bitmex.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self._binance.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        # Trades and Logs

        for client in [self._binance, self._bitmex]:

            try:  # try...except statement to handle the case when a dictionary is updated during the following loops

                for b_index, strat in client.strategies.items():
                    for log in strat.logs:
                        if not log['displayed']:
                            self.logging_frame.add_log(log['log'])
                            log['displayed'] = True

                    # Update the Trades component (add a new trade, change status/PNL)

                    for trade in strat.trades:
                        if trade.time not in self._trades_frame.body_widgets['symbol']:
                            self._trades_frame.add_trade(trade)

                        if "binance" in trade.contract.exchange:
                            precision = trade.contract.price_decimals
                        else:
                            precision = 8  # The Bitmex PNL is always is BTC, thus 8 decimals

                        pnl_str = "{0:.{prec}f}".format(trade.pnl, prec=precision)
                        self._trades_frame.body_widgets['pnl_var'][trade.time].set(pnl_str)
                        self._trades_frame.body_widgets['status_var'][trade.time].set(trade.status.capitalize())
                        self._trades_frame.body_widgets['quantity_var'][trade.time].set(trade.quantity)

            except RuntimeError as e:
                logger.error("Error while looping through strategies dictionary: %s", e)

        # Watchlist prices

        try:
            for key, value in self._watchlist_frame.body_widgets['symbol'].items():

                symbol = self._watchlist_frame.body_widgets['symbol'][key].cget("text")
                exchange = self._watchlist_frame.body_widgets['exchange'][key].cget("text")

                if exchange == "Binance":
                    if symbol not in self._binance.contracts:
                        continue

                    if symbol not in self._binance.ws_subscriptions["bookTicker"] and self._binance.ws_connected:
                        self._binance.subscribe_channel([self._binance.contracts[symbol]], "bookTicker")

                    if symbol not in self._binance.prices:
                        self._binance.get_bid_ask(self._binance.contracts[symbol])
                        continue

                    precision = self._binance.contracts[symbol].price_decimals

                    prices = self._binance.prices[symbol]

                elif exchange == "Bitmex":
                    if symbol not in self._bitmex.contracts:
                        continue

                    if symbol not in self._bitmex.prices:
                        continue

                    precision = self._bitmex.contracts[symbol].price_decimals

                    prices = self._bitmex.prices[symbol]

                else:
                    continue

                if prices['bid'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['bid'], prec=precision)
                    self._watchlist_frame.body_widgets['bid_var'][key].set(price_str)
                if prices['ask'] is not None:
                    price_str = "{0:.{prec}f}".format(prices['ask'], prec=precision)
                    self._watchlist_frame.body_widgets['ask_var'][key].set(price_str)

        except RuntimeError as e:
            logger.error("Error while looping through watchlist dictionary: %s", e)

        self.after(1500, self._update_ui)

    def _save_workspace(self):

        """
        Collect the current data on the interface and saves it to the SQLite database to avoid setting up everything
        again everytime you open the program.
        Triggered from a Menu command.
        :return:
        """

        # Watchlist

        watchlist_symbols = []

        for key, value in self._watchlist_frame.body_widgets['symbol'].items():
            symbol = value.cget("text")
            exchange = self._watchlist_frame.body_widgets['exchange'][key].cget("text")

            watchlist_symbols.append((symbol, exchange,))

        self._watchlist_frame.db.save_workspace_data("watchlist", watchlist_symbols)

        # Strategies

        strategies = []

        strat_widgets = self._strategy_frame.body_widgets

        for b_index in strat_widgets['contract']:  # Loops through the rows of a column (not necessarily the 'contract' one

            strategy_type = strat_widgets['strategy_type_var'][b_index].get()
            contract = strat_widgets['contract_var'][b_index].get()
            timeframe = strat_widgets['timeframe_var'][b_index].get()
            balance_pct = strat_widgets['balance_pct'][b_index].get()
            take_profit = strat_widgets['take_profit'][b_index].get()
            stop_loss = strat_widgets['stop_loss'][b_index].get()

            # Extra parameters are all saved in one column as a JSON string because they change based on the strategy

            extra_params = dict()

            for param in self._strategy_frame.extra_params[strategy_type]:
                code_name = param['code_name']

                extra_params[code_name] = self._strategy_frame.additional_parameters[b_index][code_name]

            strategies.append((strategy_type, contract, timeframe, balance_pct, take_profit, stop_loss,
                               json.dumps(extra_params),))

        self._strategy_frame.db.save_workspace_data("strategies", strategies)

        self.logging_frame.add_log("Workspace saved")

    def _load_workspace(self):
        # filename = filedialog.askopenfilename() # Returns the name of the file
        # print(filename)
        # self._watchlist_frame.db.open_file(self.db)
        # self._strategy_frame.db.open_file(self.db)

        self._watchlist_frame.load_workspace()
        self._strategy_frame.load_workspace()
        self.logging_frame.add_log('Workspace loaded')
    '''
    def _reset_client(self, mode: str):

        if mode == 'testnet':
            if not self.binance.testnet:
                self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True,
                                             self.binance.futures)
                self.logging_frame.add_log('Binance client initialized on Testnet')
            else:
                self.logging_frame.add_log('Binance client already on Testnet')

            if not self.bitmex.testnet:
                self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
                self.logging_frame.add_log('Bitmex client initialized on Testnet')
            else:
                self.logging_frame.add_log('Bitmex client already on Testnet')

        elif mode == 'spot':
            if self.binance.testnet:
                self.binance.ws_connected = False
                self.binance.reconnect = False
                self.binance = BinanceClient(binance_api_key, binance_api_secret, False,
                                             self.binance.futures)
                self.logging_frame.add_log('Binance client initialized on Spot')
            else:
                self.logging_frame.add_log('Binance client already on Spot')

            if self.bitmex.testnet:
                self.bitmex.ws_connected = False
                self.bitmex.reconnect = False
                self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
            else:
                self.logging_frame.add_log('Bitmex client already on Spot')
    '''

    def _restart_code(self):
        result = askquestion('Confirmation', 'Do you really want to restart the application?')
        if result == 'yes':
            variables.restart = True
            self.destroy()
