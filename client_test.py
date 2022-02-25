
from binance_client import BinanceClient
from api_keys import *

#api_key = '5CWQHvHfhyU9WWWWiRUaY0xbq6wmQkgO4512GKupzTkrwwdiTphQQxsZQCcB48rM'
#api_secret = 'ULgitDDFVLA9RELEXA8nisOUZLi9JVWUZPsKs3ctjMj2iszmMDdx5Kmeg8sz5xik'

api_key = '8p2nKptA6L4nWtyYsb4a5DSBe6u9G5myqhtJMI9ZTanlHCeaUCilFZFW5G15tdyf'
api_secret = 'SlosYFeFvkhKc6JJ6y6tMdgHgt83cXgI2A2y0wvSj1QgLiFQ7PkKchwDPAzbrlUJ'

client = BinanceClient(api_key, api_secret, testnet=True, futures=False)

c = client.get_contracts()

b = client.get_balances(c)

print(b)


