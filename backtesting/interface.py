import tkinter as tk

import logging

from backtesting.exchanges.binance import BinanceClient
from exchanges.ftx import FtxClient
from data_collector import collect_all
from utils import TF_EQUIV
import backtester
import datetime
import optimizer


class Root(tk.Tk):
    def __init__(self):
        pass
