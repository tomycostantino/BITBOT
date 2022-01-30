# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
import tkinter as tk
import logging

from connectors.binance import BinanceClient
from connectors.bitmex import BitmexClient
from interface.root_components import Root
from interface.initial_popup import InitialPopup

# Create logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the stream handler
stream_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(levelname)s :: %(message)s')
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.INFO)

# create the file handler
file_handler = logging.FileHandler('info.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(stream_handler)
logger.addHandler(file_handler)

if __name__ == '__main__':

    popup = InitialPopup()
    popup.mainloop()
    root = Root()
    root.mainloop()
