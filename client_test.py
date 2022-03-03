
from binance_client import BinanceClient
from api_keys import *

#api_key = '5CWQHvHfhyU9WWWWiRUaY0xbq6wmQkgO4512GKupzTkrwwdiTphQQxsZQCcB48rM'
#api_secret = 'ULgitDDFVLA9RELEXA8nisOUZLi9JVWUZPsKs3ctjMj2iszmMDdx5Kmeg8sz5xik'

api_key = '5CWQHvHfhyU9WWWWiRUaY0xbq6wmQkgO4512GKupzTkrwwdiTphQQxsZQCcB48rM'
api_secret = 'ULgitDDFVLA9RELEXA8nisOUZLi9JVWUZPsKs3ctjMj2iszmMDdx5Kmeg8sz5xik'

client = BinanceClient(api_key, api_secret, testnet=True, futures=False)

contracts = client.get_contracts()

balances = client.get_balances()
for b in balances.items():
    print(b[0])
    print(b[1])
