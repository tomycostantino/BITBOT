import logging
import requests
import time
import typing
import hmac
import hashlib
import websocket
import threading
import json

from urllib.parse import urlencode
from models import *
from strategies import TechnicalStrategy, BreakoutStrategy

logger = logging.getLogger()


# HANDLER FOR BINANCE CLIENTS
class BinanceFuturesClient:
    # constructor
    def __init__(self, public_key: str, secret_key: str, testnet: bool):
        if testnet:
            self._base_url = "https://testnet.binancefuture.com"
            self._wss_url = 'wss://stream.binancefuture.com/ws'
        else:
            self._base_url = "https://fapi.binance.com"
            self._wss_url = 'wss://fstream.binance.com/ws'

        self._public_key = public_key
        self._secret_key = secret_key

        self._headers = {'X-MBX-APIKEY': self._public_key}

        # obtain all contracts, BTCUSDT, ETHUSDT, ADAUSDT, etc
        self.contracts = self.get_contracts()

        # obtain balances of all assets
        self.balances = self.get_balances()

        # nested dictionary that will keep track of bid and ask prices of a symbol
        # it will be updated when a func is called and new symbols are to be added when requested
        self.prices = dict()

        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()

        # list of logs
        self.logs = []

        # websocket
        self.ws: websocket.WebSocketApp

        self.reconnect = True
        # websocket id
        self._ws_id = 0

        # start threading for ws manager
        t = threading.Thread(target=self._start_ws)
        t.start()
        logger.info("Binance Futures Client successfully initialized")

    # the signature is required when getting balances, place and cancel orders, and know order status
    # returns the signature
    def _generate_signature(self, data: typing.Dict) -> str:
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()

    # logger to document what happens when using the program
    # it appends the logs to the list created previously, does not return anything
    def _add_log(self, msg: str):
        logger.info('%s', msg)
        self.logs.append({'log': msg, 'displayed': False})

    # this function will communicate with the Binance API
    # it permits requesting, sending and deleting info when interacting with the API
    # returns the response in a JSON format, which would be a dictionary
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
        exchange_info = self._make_request('GET', '/fapi/v1/exchangeInfo', dict())

        contracts = dict()
        if exchange_info is not None:
            # loop through the symbols and add them to the contracts dict
            for contract_data in exchange_info['symbols']:
                contracts[contract_data['symbol']] = Contract(contract_data, 'binance')

        else:
            self._add_log('Data could not be obtained from exchange')

        return contracts

    # manages to get the historical candlestick, up to 1000
    # receives the contract and the time interval, 1m, 5m, 15m and so on
    # returns a list of Candle
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        raw_candles = self._make_request('GET', '/fapi/v1/klines', data)

        candles = []

        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c, interval, "binance"))

        return candles

    # returns a nested dict with most recent bid and ask price
    # if the symbol passed was not in dict created before, it will be added now, otherwise the prices will be updated
    # the output looks like this:
    # {'BTCUSDT':{'bidPrice': 10.0, 'askPrice': 9.0}}
    def get_bid_ask(self, contract: Contract) -> typing.Dict[str, typing.Dict]:
        data = dict()
        data['symbol'] = contract.symbol
        ob_data = self._make_request('GET', '/fapi/v1/ticker/bookTicker', data)

        # 'https://testnet.binancefuture.com/fapi/v1/ticker/bookTicker?symbol=BTCUSDT'

        if ob_data is not None:
            if contract.symbol not in self.prices:
                self.prices[contract.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[contract.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[contract.symbol]['ask'] = float(ob_data['askPrice'])

            return self.prices[contract.symbol]

    # in charge of getting the amount of all cryptos the user has
    # returns a dict of Balance
    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        account_data = self._make_request('GET', '/fapi/v1/account', data)

        balances = dict()

        if account_data is not None:
            for a in account_data['assets']:
                balances[a['asset']] = Balance(a)

        return balances

    # place orders to buy or sell depending on the signal
    # gets the contract, the type: MARKET, the quantity, and the side: buy or sell
    # return the status of the order
    def place_order(self, contract: Contract, order_type: str, quantity: float, side: str, price=None, tif=None) -> \
            OrderStatus:
        data = dict()
        data['symbol'] = contract.symbol
        data['type'] = order_type
        data['quantity'] = quantity
        data['side'] = side.upper()

        if price is not None:
            data['price'] = price

        if tif is not None:
            data['timeInForce'] = tif

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request('POST', '/fapi/v1/order', data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    # cancel order when required
    # receives the Contract and the order id to cancel
    # returns an OrderStatus object
    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['orderId'] = order_id
        data['symbol'] = contract.symbol

        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request('DELETE', '/fapi/v1/order', data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    # check the status of an order
    # gets the contract and the order id
    # returns an OrderStatus
    def get_order_status(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = contract.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)

        order_status = self._make_request('GET', '/fapi/v1/order', data)

        if order_status is not None:
            order_status = OrderStatus(order_status)

        return order_status

    # Websocket manager
    def _start_ws(self):
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close,
                                         on_error=self._on_error, on_message=self._on_message)

        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever()
                else:
                    break
            except Exception as e:
                logger.error('Binance error in run_forever method: %s', e)
            time.sleep(2)

    # these function will be called by the Websocket manager
    # the argument 'ws' is not used but it must be there to avoid rising an error
    def _on_open(self, ws):
        logger.info('Binance connection opened')

        self.subscribe_channel(list(self.contracts.values()), 'bookTicker')

    def _on_close(self, ws, *args, **kwargs):
        logger.warning('Websocket connection closed')

    def _on_error(self, ws, msg: str):
        logger.error('Binance connection error: %s', msg)

    # this is the most important function for the ws manager because it will interpret what the ws is sending
    # read binance documentation to see what the letters mean
    def _on_message(self, ws, msg: str):

        data = json.loads(msg)

        if 'e' in data:
            # if bookTicker, the data received is bid and ask price
            if data['e'] == 'bookTicker':

                symbol = data['s']

                if symbol not in self.prices:
                    self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                else:
                    self.prices[symbol]['bid'] = float(data['b'])
                    self.prices[symbol]['ask'] = float(data['a'])

                # PNL calculation
                # it is done here because everytime the bid and ask are updated, the PNL are calculated to know
                # when to sell when on a position, and check for all ongoing trades as well
                try:
                    for b_index, strat in self.strategies.items():
                        if strat.contract.symbol == symbol:
                            for trade in strat.trades:
                                if trade.status == 'open' and trade.entry_price is not None:
                                    if trade.side == 'long':
                                        trade.pnl = (self.prices[symbol]['bid'] - trade.entry_price) * trade.quantity
                                    elif trade.side == 'short':
                                        trade.pnl = (self.prices[symbol]['ask'] - trade.entry_price) * trade.quantity
                except RuntimeError as e:
                    logger.error('Error while looping through the binance strategies %s:', e)

            # if aggTrade, data received is a new candle to append
            elif data['e'] == 'aggTrade':
                symbol = data['s']

                for key, strat in self.strategies.items():
                    if strat.contract.symbol == symbol:
                        res = strat.parse_trades(float(data['p']), float(data['q']), data['T'])
                        strat.check_trade(res)

    # subscribe channels to receive data from ws
    def subscribe_channel(self, contracts: typing.List[Contract], channel: str):
        data = dict()
        data['method'] = 'SUBSCRIBE'
        data['params'] = []

        for contract in contracts:
            data['params'].append(contract.symbol.lower() + '@' + channel)

        data['id'] = self._ws_id

        try:
            self.ws.send(json.dumps(data))
        except Exception as e:
            logger.error('Connection error while making %s request to %s %s updates: %s', len(contracts), channel, e)

        self._ws_id += 1

    # calculate the size of the trade and return it
    def get_trade_size(self, contract: Contract, price: float, balance_pct: float):

        balance = self.get_balances()
        if balance is not None:
            if 'USDT' in balance:
                balance = balance['USDT'].wallet_balance
            else:
                return None
        else:
            return None

        trade_size = (balance * balance_pct / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)

        logger.info('Binance Futures current USDT balance = %s, trade size = %s', balance, trade_size)

        return trade_size
