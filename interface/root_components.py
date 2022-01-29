import typing

from api_keys import *
import tkinter as tk
import json
from connectors.binance import BinanceClient
from connectors.bitmex import BitmexClient

import logging
import tkmacosx as tkmac
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

        self._show_popup()
        self._init_clients(True, True)

        self.title('Trading Bot')

        self.protocol('WM_DELETE_WINDOW', self._ask_before_close)

        # background color
        self.configure(bg=BG_COLOR_2)

        self.main_menu = tk.Menu(self)
        self.configure(menu=self.main_menu)

        self.workspace_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label="Workspace", menu=self.workspace_menu)
        self.workspace_menu.add_command(label="Save workspace", command=self._save_workspace)
        self.workspace_menu.add_command(label="Load workspace", command=self._load_workspace)

        self.testnet_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label='Testnet', menu=self.testnet_menu)
        self.testnet_menu.add_command(label='Testnet', command=self._set_testnet)
        self.testnet_menu.add_command(label='Spot', command=self._set_spot)

        self.futures_menu = tk.Menu(self.main_menu, tearoff=False)
        self.main_menu.add_cascade(label='Futures', menu=self.futures_menu)
        self.futures_menu.add_command(label='Binance', command=self._set_binance_normal)
        self.futures_menu.add_command(label='Binance Futures', command=self._set_binance_future)

        # create left frame
        self._left_frame = tk.Frame(self, bg=BG_COLOR)
        self._left_frame.pack(side=tk.LEFT)

        # create right frame
        self._right_frame = tk.Frame(self, bg=BG_COLOR)
        self._right_frame.pack(side=tk.LEFT)

        self._watchlist_frame = Watchlist(self.binance.contracts, self.bitmex.contracts, self._left_frame, bg=BG_COLOR_2)
        self._watchlist_frame.pack(side=tk.TOP, padx=10)

        self.logging_frame = Logging(self._left_frame, bg=BG_COLOR)
        self.logging_frame.pack(side=tk.TOP, pady=15)

        self._strategy_frame = StrategyEditor(self, self.binance, self.bitmex, self._right_frame, bg=BG_COLOR)
        self._strategy_frame.pack(side=tk.TOP)

        self._trades_frame = TradesWatch(self._right_frame, bg=BG_COLOR)
        self._trades_frame.pack(side=tk.TOP)

        self._update_ui()

    def _show_popup(self) -> typing.Union[str, str]:
        self._popup_window = tk.Toplevel(self)
        self._popup_window.wm_title('Start in Testnet or Spot')

        self._popup_window.config(bg=BG_COLOR)
        self._popup_window.attributes('-topmost', 'true')
        self._popup_window.grab_set()

        testnet_f = tkmac.Button(self._popup_window, text="Testnet futures",
                                 command=lambda: self._init_clients(True, True))
        testnet_f.pack(side=tk.TOP, anchor='center')

        testnet_nf = tkmac.Button(self._popup_window, text="Testnet normal",
                                  command=lambda: self._init_clients(True, False))
        testnet_nf.pack(side=tk.TOP, anchor='center')

        spot_f = tkmac.Button(self._popup_window, text='Spot futures', command=lambda: self._init_clients(False, True))
        spot_f.pack(side=tk.TOP, anchor='center')

        spot_nf = tkmac.Button(self._popup_window, text='Spot normal', command=lambda: self._init_clients(False, False))
        spot_nf.pack(side=tk.TOP, anchor='center')

    def _init_clients(self, testnet: bool, futures: bool):
        if testnet and futures:
            self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, True)
            self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
            # self.logging_frame.add_log('Clients initialized in testnet and futures')

        elif testnet and not futures:
            self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, False)
            self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
            # self.logging_frame.add_log('Clients initialized in testnet and not futures')

        elif not testnet and futures:
            self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, False, True)
            self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
            # self.logging_frame.add_log('Clients initialized in normal net and futures')

        else:
            self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, False, False)
            self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
            # self.logging_frame.add_log('Clients initialized in normal net and not futures')

    def _ask_before_close(self):
        result = askquestion('Confirmation', 'Do you really want to exit the application?')
        if result == 'yes':
            self.binance.reconnect = False
            self.bitmex.reconnect = False
            self.binance.ws.close()
            self.bitmex.ws.close()

            self.destroy()

    def _update_ui(self):

        """
        Called by itself every 1500 seconds. It is similar to an infinite loop but runs within the same Thread
        as .mainloop() thanks to the .after() method, thus it is "thread-safe" to update elements of the interface
        in this method. Do not update Tkinter elements from another Thread like the websocket thread.
        :return:
        """

        # Logs

        for log in self.bitmex.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        for log in self.binance.logs:
            if not log['displayed']:
                self.logging_frame.add_log(log['log'])
                log['displayed'] = True

        # Trades and Logs

        for client in [self.binance, self.bitmex]:

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
                    if symbol not in self.binance.contracts:
                        continue

                    if symbol not in self.binance.ws_subscriptions["bookTicker"] and self.binance.ws_connected:
                        self.binance.subscribe_channel([self.binance.contracts[symbol]], "bookTicker")

                    if symbol not in self.binance.prices:
                        self.binance.get_bid_ask(self.binance.contracts[symbol])
                        continue

                    precision = self.binance.contracts[symbol].price_decimals

                    prices = self.binance.prices[symbol]

                elif exchange == "Bitmex":
                    if symbol not in self.bitmex.contracts:
                        continue

                    if symbol not in self.bitmex.prices:
                        continue

                    precision = self.bitmex.contracts[symbol].price_decimals

                    prices = self.bitmex.prices[symbol]

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

        self._watchlist_frame.db.save("watchlist", watchlist_symbols)

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

        self._strategy_frame.db.save("strategies", strategies)

        self.logging_frame.add_log("Workspace saved")

    def _load_workspace(self):
        # filename = filedialog.askopenfilename() # Returns the name of the file
        # print(filename)
        # self._watchlist_frame.db.open_file(self.db)
        # self._strategy_frame.db.open_file(self.db)

        self._watchlist_frame.load_workspace()
        self._strategy_frame.load_workspace()
        self.logging_frame.add_log('Workspace loaded')

    def _set_testnet(self):
        if not self.binance.testnet:
            self.binance.ws_connected = False
            self.binance.reconnect = False

            del self.binance

            self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, True)

        else:
            self.logging_frame.add_log('Binance Client already on testnet')
        '''
        if not self.bitmex.testnet:
            self.bitmex.reconnect = False

            del self.bitmex

            self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)

        else:
            self.logging_frame.add_log('Bitmex Client already on testnet')
        
        '''

    def _set_spot(self):

        if self.binance.testnet:
            self.binance.ws_connected = False
            self.binance.reconnect = False

            del self.binance

            self.logging_frame.add_log('Binance Testnet Client deleted')

            self.binance = BinanceClient(binance_api_key, binance_api_secret, False, False)

            self.logging_frame.add_log('Binance Spot client started')
        '''
        if self.bitmex.testnet:
            self.bitmex.testnet = False

            del self.bitmex

            self.logging_frame.add_log('Bitmex Testnet Client deleted')

            self.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)

            self.logging_frame.add_log('Binance Spot client started')
            
        '''

    def _set_binance_normal(self):
        if self.binance.futures:
            if self.binance.testnet:
                del self.binance
                self.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, False)
                self.logging_frame.add_log('Binance client set on testnet normal')

            elif not self.binance.testnet:
                del self.binance
                self.binance = BinanceClient(binance_api_key, binance_api_secret, False, False)
                self.logging_frame.add_log('Binance client set on spot normal')
        else:
            self.logging_frame.add_log('Binance client is already normal')

    def _set_binance_future(self):
        if self.binance.futures:
            self.logging_frame.add_log('Binance client is already on Futures')
        else:
            if self.binance.testnet:
                del self.binance
                self.binance = BinanceClient(binance_api_key, binance_api_secret, True, True)
                self.logging_frame.add_log('Binance client set on testnet futures')
            else:
                del self.binance
                self.binance = BinanceClient(binance_api_key, binance_api_secret, False, True)
                self.logging_frame.add_log('Binance client set on futures')

