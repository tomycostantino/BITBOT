
# from binance_client import BinanceClient
from api_keys import *

from connectors.binance import BinanceClient

#api_key = '5CWQHvHfhyU9WWWWiRUaY0xbq6wmQkgO4512GKupzTkrwwdiTphQQxsZQCcB48rM'
#api_secret = 'ULgitDDFVLA9RELEXA8nisOUZLi9JVWUZPsKs3ctjMj2iszmMDdx5Kmeg8sz5xik'

api_key = '5CWQHvHfhyU9WWWWiRUaY0xbq6wmQkgO4512GKupzTkrwwdiTphQQxsZQCcB48rM'
api_secret = 'ULgitDDFVLA9RELEXA8nisOUZLi9JVWUZPsKs3ctjMj2iszmMDdx5Kmeg8sz5xik'

client = BinanceClient(api_key, api_secret, testnet=True, futures=False)


contracts = client.get_contracts()
for contract in contracts:
    print(contract)

balances = client.get_balances()
#for b in balances.items():
#    print(b[0])
#    print(b[1])

#candles = client.get_historical_candles(contracts['BTCUSDT'], '5m')
#for c in candles:
#    print(c)

#order = client.place_order(contracts['ETHUSDT'], 'MARKET', 0.0001000, 'BUY')

#print(order)

client.get_filters()
