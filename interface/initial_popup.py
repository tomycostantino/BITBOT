import tkinter as tk
import tkmacosx as tkmac
from interface.styling import *
from connectors.binance import BinanceClient
from api_keys import *
from connectors.bitmex import BitmexClient
import variables


class InitialPopup(tk.Tk):
    def __init__(self):
        super().__init__()

        self.eval('tk::PlaceWindow . center')

        self.title('Start in mode:')

        self._frame = tk.Frame(self)
        self._frame.config(width=200, height=110)
        self._frame.pack_propagate(0)
        self._frame.pack(side=tk.TOP, expand=True, fill='both')

        testnet_f = tkmac.Button(self._frame, text="Testnet futures",
                                 command=self._testnet_f)
        testnet_f.pack(side=tk.TOP, anchor='center', fill='both')

        testnet_nf = tkmac.Button(self._frame, text="Testnet normal",
                                  command=self._testnet_n)
        testnet_nf.pack(side=tk.TOP, anchor='center', fill='both')

        spot_f = tkmac.Button(self._frame, text='Spot futures',
                              command=self._spot_f)
        spot_f.pack(side=tk.TOP, anchor='center', fill='both')

        spot_nf = tkmac.Button(self._frame, text='Spot normal',
                               command=self._spot_n)
        spot_nf.pack(side=tk.TOP, anchor='center', fill='both')

    def _testnet_f(self):
        variables.binance = BinanceClient(binance_futures_api_key, binance_futures_api_secret, True, True)
        variables.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
        self.destroy()

    def _testnet_n(self):
        variables.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, False)
        variables.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
        self.destroy()

    def _spot_f(self):
        variables.binance = BinanceClient(binance_futures_api_key, binance_futures_api_secret, False, True)
        variables.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
        self.destroy()

    def _spot_n(self):
        variables.binance = BinanceClient(binance_api_key, binance_api_secret, False, False)
        variables.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
        self.destroy()
