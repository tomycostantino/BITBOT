# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


# See PyCharm help at https://www.jetbrains.com/help/pycharm/
import tkinter as tk
import logging

from connectors.binance import BinanceClient
from connectors.bitmex import BitmexClient
from interface.root_components import Root

# These are the keys for the testnet
binance_api_key = '9b020287e6105b7a91d95bc858ec13c9c3b724377e63c12909095dd934b7ad60'
binance_api_secret = 'b0ffaac2300e0ce792b8fe614599cecd1b454e0ee5cf6da63b4a8b5b2a0ee1a2'

bitmex_api_key = 'QhRkPwfkuRwzD1Rx3aeacOUA'
bitmex_api_secret ='25Sxg2JEgTAorNwe8KxXZO7Rbg_s2yTzYRwPSyiVHi_f3JR0'

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

    binance = BinanceClient(binance_api_key, binance_api_secret, True, True)
    bitmex = BitmexClient(bitmex_api_key, bitmex_api_secret, testnet=True)

    root = Root(binance, bitmex)
    root.mainloop()
