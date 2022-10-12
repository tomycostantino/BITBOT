import logging

import requests
import typing
import time
from binance.client import Client
from binance.enums import *
from models import *

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

        ''' Timeframe dictionary for Binance API '''
        self._timeframes = {
            '1m': self._client.KLINE_INTERVAL_1MINUTE,
            '5m': self._client.KLINE_INTERVAL_5MINUTE,
            '15m': self._client.KLINE_INTERVAL_15MINUTE,
            '30m': self._client.KLINE_INTERVAL_30MINUTE,
            '1h': self._client.KLINE_INTERVAL_1HOUR
        }

    ''' 
    Logger to document what happens when using the program,
    It appends the logs to the list created previously, does not return anything 
    '''
    def _add_log(self, msg: str):
        '''
        :param msg: message to be added to the logs
        :return:
        '''

        logger.info('%s', msg)
        self.logs.append({'log': msg, 'displayed': False})

    ''' Make requests to the binance API'''
    def _make_request(self, method: str, endpoint: str, data: typing.Dict) -> typing.Union[typing.Dict, None]:
        '''
        :param method: GET or POST
        :param endpoint:
        :param data:
        :return: response from API or None
        '''

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

        ''' Check if the response is valid, 200 means so '''
        if response.status_code == 200:
            return response.json()

        else:
            logger.error("Error while making %s request to %s: %s (error code %s)",
                         method, endpoint, response.json(), response.status_code)
            return None

    ''' 
    Public endpoints
    Get the possible contracts like BTC/USDT or ETH/USDT for example
    '''
    def get_contracts(self) -> typing.Dict[str, Contract]:
        '''
        :return: dict of contracts
        '''

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

    ''' In charge of getting the amount of all cryptos the user has '''
    def get_balances(self) -> typing.Dict[str, Balance]:
        '''
        :return: dict of balances
        '''

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

    ''' Manages to get the historical candlestick, up to 1000 candles '''
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        '''
        :param contract: contract to get the candles from
        :param interval:
        :return: list of candles
        '''

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

    '''
    Returns a nested dict with most recent bid and ask price
    If the symbol passed was not in dict created before, it will be added now, otherwise the prices will be updated
    The output looks like this: {'BTCUSDT':{'bidPrice': 10.0, 'askPrice': 9.0}}
    '''
    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, typing.Dict]:
        '''
        :param contract: contract to get the bid and ask from
        :return:
        '''

        data = dict()
        data['symbol'] = contract.symbol

        if self._futures:
            ob_data = self._make_request('GET', '/fapi/v1/ticker/bookTicker', data)
        else:
            ob_data = self._make_request('GET', '/api/v3/ticker/bookTicker', data)

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
                type=ORDER_TYPE_LIMIT,
                side=SIDE_BUY,
                quantity=data['quantity'],
                timeInForce=TIME_IN_FORCE_GTC,
                price=str(data['price'])
            )

        if order_status is not None:
            if not self._futures:
                if order_status['status'] == 'FILLED':
                    print(order_status['status'])
                    order_status['avgPrice'] = self._get_execution_price(contract, order_status['orderId'])
                    print(order_status['avgPrice'])
                else:
                    order_status['avgPrice'] = 0

            order_status = OrderStatus(order_status, self.platform)
            print(order_status)

        return order_status

    # cancel order when required
    # receives the Contract and the order id to cancel
    # returns an OrderStatus object
    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:

        if self.futures:
            data = dict()
            data['orderId'] = order_id
            data['symbol'] = contract.symbol

            data['timestamp'] = int(time.time() * 1000)
            data['signature'] = self._generate_signature(data)
            order_status = self._make_request('DELETE', '/fapi/v1/order', data)
        else:

            order_status = self._client.cancel_order(symbol=contract.symbol, orderId=order_id)

        if order_status is not None:
            if not self.futures:
                # get average execution price based on the recent trades
                order_status['avgPrice'] = self._get_execution_price(contract, order_id)
            order_status = OrderStatus(order_status, self.platform)

        return order_status

    # check the status of an order
    # gets the contract and the order id
    # returns an OrderStatus
    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:

        if self.futures:
            data = dict()
            data['timestamp'] = int(time.time() * 1000)
            data['symbol'] = contract.symbol
            data['orderId'] = order_id
            data['signature'] = self._generate_signature(data)
            order_status = self._make_request('GET', '/fapi/v1/order', data)
        else:
            order_status = self._client.get_order(symbol=contract.symbol, orderId=order_id)

        if order_status is not None:
            if not self.futures:
                if order_status['status'] == 'FILLED':
                    order_status['avgPrice'] = self._get_execution_price(contract, order_id)
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
            trades = self._client.get_my_trades(symbol=contract.symbol)

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
