import logging

import binance.client
import requests
import typing
import time
from binance.client import Client
from binance.enums import *
from models import *
from strategies import TechnicalStrategy, BreakoutStrategy

logger = logging.getLogger()


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool, futures: bool):
        self._client = Client(api_key, api_secret)
        self._client.API_URL = 'https://testnet.binance.vision/api'
        self._api_key = api_key
        self._testnet = testnet
        self._futures = futures

        if self._futures:
            self.platform = 'binance_futures'
            if self._testnet:
                self._base_url = "https://testnet.binancefuture.com"
                self._wss_url = 'wss://stream.binancefuture.com/ws'
            else:
                self._base_url = "https://fapi.binance.com"
                self._wss_url = 'wss://fstream.binance.com/ws'
        else:
            self.platform = "binance_spot"
            if self._testnet:
                self._base_url = "https://testnet.binance.vision"
                self._wss_url = "wss://testnet.binance.vision/ws"
            else:
                self._base_url = "https://api.binance.com"
                self._wss_url = "wss://stream.binance.com:9443/ws"

        self._headers = {'X-MBX-APIKEY': self._api_key}

        self.logs = []

        self._timeframes = {
            '1m': self._client.KLINE_INTERVAL_1MINUTE,
            '5m': self._client.KLINE_INTERVAL_5MINUTE,
            '15m': self._client.KLINE_INTERVAL_15MINUTE,
            '30m': self._client.KLINE_INTERVAL_30MINUTE,
            '1h': self._client.KLINE_INTERVAL_1HOUR
        }

    # logger to document what happens when using the program
    # it appends the logs to the list created previously, does not return anything
    def _add_log(self, msg: str):
        logger.info('%s', msg)
        self.logs.append({'log': msg, 'displayed': False})

    def _make_request(self, method: str, endpoint: str, data: typing.Dict):
        if method == 'GET':
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error('Connection error while making %s request to %s: %s', method, endpoint, e)
                return None

        elif method == 'POST':
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error('Connection error while making %s request to %s: %s', method, endpoint, e)
                return None

        elif method == 'DELETE':
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error('Connection error while making %s request to %s: %s', method, endpoint, e)
                return None

        else:
            raise ValueError

        # check if the response is valid, 200 means that
        if response.status_code == 200:
            return response.json()

        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    # public endpoints
    # get the possible contracts like BTC/USDT or ETH/USDT for example
    # returns a dictionary of contracts
    def get_contracts(self) -> typing.Dict[str, Contract]:
        if self._futures:
            exchange_info = self._make_request('GET', '/fapi/v1/exchangeInfo', dict())
        else:
            exchange_info = self._make_request('GET', '/api/v3/exchangeInfo', dict())

        contracts = dict()
        if exchange_info is not None:
            # loop through the symbols and add them to the contracts dict
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['symbol']] = Contract(contract_data, self.platform)

        else:
            self._add_log('Data could not be obtained from exchange')

        return contracts

    # in charge of getting the amount of all cryptos the user has
    # returns a dict of Balance
    def get_balances(self) -> typing.Dict[str, Balance]:

        balances = dict()

        if self._futures:
            data = dict()
            data['timestamp'] = int(time.time() * 1000)
            data['signature'] = self._generate_signature(data)
            account_data = self._make_request('GET', '/fapi/v1/account', data)
            if account_data is not None:
                for a in account_data['assets']:
                    balances[a['asset']] = Balance(a, self.platform)

        else:
            info = self._client.get_account()
            for i in info['balances']:
                balances[i['asset']] = Balance(i, self.platform)
        return balances

    # manages to get the historical candlestick, up to 1000
    # receives the contract and the time interval, 1m, 5m, 15m and so on
    # returns a list of Candle
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        candles = []

        if self._futures:
            data = dict()
            data['symbol'] = contract.symbol
            data['interval'] = interval
            data['limit'] = 1000
            raw_candles = self._make_request('GET', '/fapi/v1/klines', data)
            if raw_candles is not None:
                for c in raw_candles:
                    candles.append(Candle(c, interval, self.platform))
        else:
            raw_candles = self._client.get_klines(symbol=contract.symbol, interval=self._timeframes[interval])
            if candles is not None:
                for c in raw_candles:
                    candles.append(Candle(c, interval, self.platform))

        return candles

    # returns a nested dict with most recent bid and ask price
    # if the symbol passed was not in dict created before, it will be added now, otherwise the prices will be updated
    # the output looks like this:
    # {'BTCUSDT':{'bidPrice': 10.0, 'askPrice': 9.0}}
    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, typing.Dict]:
        data = dict()
        data['symbol'] = contract.symbol

        if self.futures:
            ob_data = self._make_request('GET', '/fapi/v1/ticker/bookTicker', data)
        else:
            ob_data = self._make_request('GET', '/api/v3/ticker/bookTicker', data)

        # 'https://testnet.binancefuture.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT'

        if ob_data is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])

            return self.prices[contract.symbol]

    # place orders to buy or sell depending on the signal
    # gets the contract, the type: MARKET, the quantity, and the side: buy or sell
    # return the status of the order
    def place_order(self, contract: Contract, order_type: str, quantity: float, side: str, price=None, tif=None) -> \
            OrderStatus:

        data = dict()
        data['symbol'] = contract.symbol
        data['type'] = order_type

        ''' come back to this part (quantity)'''
        data['quantity'] = quantity
        data['side'] = side.upper()

        if price is not None:
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)
            data['price'] = '%.*f' % (contract.price_decimals, data['price'])

        if tif is not None:
            data['timeInForce'] = tif

        if self._futures:
            data['timestamp'] = int(time.time() * 1000)
            data['signature'] = self._generate_signature(data)
            order_status = self._make_request('POST', '/fapi/v1/order', data)

        else:
            order_status = self._client.create_order(
                symbol=data['symbol'],
                type=data['type'],
                side=data['side'],
                quantity=data['quantity']
            )

        if order_status is not None:
            if not self._futures:
                if order_status['status'] == 'FILLED':
                    order_status['avgPrice'] = self._get_execution_price(contract, order_status['orderId'])
                else:
                    order_status['avgPrice'] = 0

            order_status = OrderStatus(order_status, self.platform)

        return order_status

    def _get_execution_price(self, contract: Contract, order_id: int) -> float:
        """
                For Binance Spot only, find the equivalent of the 'avgPrice' key on the futures side.
                The average price is the weighted sum of each trade price related to the order_id
                :param contract:
                :param order_id:
                :return:
        """
        data = dict()
        data['symbol'] = contract.symbol

        if self._futures:
            data['timestamp'] = int(time.time() * 1000)
            data['signature'] = self._generate_signature(data)
            trades = self._make_request('GET', '/api/v3/myTrades', data)

        else:
            trades = self._client.get_my_trades(symbol=data['symbol'])

        avg_price = 0

        if trades is not None:
            executed_qty = 0
            for t in trades:
                if t['orderId'] == order_id:
                    executed_qty += float(t['qty'])

            for t in trades:
                if t['orderId'] == order_id:
                    fill_pct = float(t['qty']) / executed_qty
                    avg_price += (float(t['price']) * fill_pct)

        return round(round(avg_price / contract.tick_size) * contract.tick_size, 8)

    def get_info(self):
        return self._client.get_account()
