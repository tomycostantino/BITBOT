# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
import tkinter as tk
import logging

from connectors.binance_futures import BinanceFuturesClient
from interface.root_components import Root

# These are the keys for the testnet
api_key = '9b020287e6105b7a91d95bc858ec13c9c3b724377e63c12909095dd934b7ad60'
api_secret = 'b0ffaac2300e0ce792b8fe614599cecd1b454e0ee5cf6da63b4a8b5b2a0ee1a2'

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

    binance = BinanceFuturesClient(api_key, api_secret, True)

    root = Root(binance)
    root.mainloop()
