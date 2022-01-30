import tkinter as tk
import tkmacosx as tkmac
from interface.styling import *
from connectors.binance import BinanceClient
from api_keys import *
from connectors.bitmex import BitmexClient
import clients


class InitialPopup(tk.Tk):
    def __init__(self):
        super().__init__()

        self.eval('tk::PlaceWindow . center')

        self.title('Start in mode:')

        self._frame = tk.Frame(self, bg=BG_COLOR)
        self._frame.config(width=200, height=120)
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
        clients.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, True)
        clients.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
        self.destroy()

    def _testnet_n(self):
        clients.binance = BinanceClient(binance_testnet_api_key, binance_testnet_api_secret, True, False)
        clients.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)
        self.destroy()

    def _spot_f(self):
        clients.binance = BinanceClient(binance_api_key, binance_api_secret, False, True)
        clients.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
        self.destroy()

    def _spot_n(self):
        clients.binance = BinanceClient(binance_api_key, binance_api_secret, False, False)
        clients.bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=False)
        self.destroy()
