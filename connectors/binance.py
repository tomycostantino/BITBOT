import logging
import requests
import time
import typing
import hmac
import hashlib
import websocket
import threading
import json
import prices

from urllib.parse import urlencode

from models import *
from strategies import TechnicalStrategy, BreakoutStrategy
from utils import *

logger = logging.getLogger()


# HANDLER FOR BINANCE CLIENTS
class BinanceClient:
    # constructor
    def __init__(self, public_key: str, secret_key: str, testnet: bool, futures: bool):
        self.futures = futures
        self.testnet = testnet
        if self.futures:
            self.platform = 'binance_futures'
            if self.testnet:
                self._base_url = "https://testnet.binancefuture.com"
                self._wss_url = 'wss://stream.binancefuture.com/ws'
            else:
                self._base_url = "https://fapi.binance.com"
                self._wss_url = 'wss://fstream.binance.com/ws'

            logger.info("Binance Futures Client successfully initialized")

        else:
            self.platform = "binance_spot"
            if self.testnet:
                self._base_url = "https://testnet.binance.vision"
                self._wss_url = "wss://testnet.binance.vision/ws"
            else:
                self._base_url = "https://api.binance.com"
                self._wss_url = "wss://stream.binance.com:9443/ws"

            logger.info("Binance Spot Client successfully initialized")

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
        self.ws = None
        self._ws_id = 1
        self.reconnect = True
        self.ws_connected = False
        self.ws_subscriptions = {'bookTicker': [], 'aggTrade': []}

        # start threading for ws manager
        t = threading.Thread(target=self.start_ws)
        t.start()


    def _hashing(self, query_string: str):
        return hmac.new(
            self._secret_key.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256
        ).hexdigest()

    def _get_timestamp(self):
        return int(time.time() * 1000)

    def _dispatch_request(self, http_method: str):
        session = requests.Session()
        session.headers.update(
            {"Content-Type": "application/json;charset=utf-8", "X-MBX-APIKEY": self._public_key}
        )
        return {
            "GET": session.get,
            "DELETE": session.delete,
            "PUT": session.put,
            "POST": session.post,
        }.get(http_method, "GET")

    # for signed endpoints
    def _send_signed_request(self, http_method: str, url_path: str, payload={}):
        query_string = urlencode(payload, True)
        if query_string:
            query_string = "{}&timestamp={}".format(query_string, self._get_timestamp())
        else:
            query_string = "timestamp={}".format(self._get_timestamp())

        url = (
            self._base_url + url_path + "?" + query_string + "&signature=" + self._hashing(query_string)
        )

        # print("{} {}".format(http_method, url))
        params = {"url": url, "params": {}}
        response = self._dispatch_request(http_method)(**params)
        return response.json()

    # for public endpoints
    def _send_public_request(self, url_path: str, payload={}):
        query_string = urlencode(payload, True)
        url = self._base_url + url_path
        if query_string:
            url = url + '?' + query_string
        # print('{}'.format(url))
        response = self._dispatch_request('GET')(url=url)
        return response.json()

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

        if self.futures:
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

    # manages to get the historical candlestick, up to 1000
    # receives the contract and the time interval, 1m, 5m, 15m and so on
    # returns a list of Candle
    def get_historical_candles(self, contract: Contract, interval: str) -> typing.List[Candle]:
        data = dict()
        data['symbol'] = contract.symbol
        data['interval'] = interval
        data['limit'] = 1000

        if self.futures:
            raw_candles = self._make_request('GET', '/fapi/v1/klines', data)
        else:
            raw_candles = self._make_request('GET', '/api/v3/klines', data)

        candles = []

        if raw_candles is not None:
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

    # in charge of getting the amount of all cryptos the user has
    # returns a dict of Balance
    def get_balances(self) -> typing.Dict[str, Balance]:
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)

        balances = dict()

        if self.futures:
            account_data = self._send_signed_request('GET', '/fapi/v1/account')
        else:
            account_data = self._send_signed_request('GET', '/api/v3/account')

        if account_data is not None:

            if self.futures:
                for a in account_data['assets']:
                    balances[a['asset']] = Balance(a, self.platform)
            else:
                for a in account_data['balances']:
                    balances[a['asset']] = Balance(a, self.platform)

        return balances

    # place orders to buy or sell depending on the signal
    # gets the contract, the type: MARKET, the quantity, and the side: buy or sell
    # return the status of the order
    def place_order(self, contract: Contract, order_type: str, quantity: float, side: str, price=None, tif=None) -> \
            OrderStatus:

        data = dict()
        data['symbol'] = contract.symbol
        data['side'] = side.upper()
        data['quantity'] = round(int(quantity / contract.lot_size) * contract.lot_size, 8)  # int() to round down
        data['type'] = order_type.upper()

        if price is not None:
            data['price'] = round(round(price / contract.tick_size) * contract.tick_size, 8)
            data['price'] = '%.*f' % (contract.price_decimals, data['price'])

        if tif is not None:
            data['timeInForce'] = tif

        if self.futures:
            # data['timestamp'] = int(time.time() * 1000)
            # data['signature'] = self._generate_signature(data)
            order_status = self._send_signed_request('POST', '/fapi/v1/order', data)
            print(order_status)
        else:
            order_status = self._send_signed_request('POST', '/api/v3/order', data)
            print(order_status)

        '''
        if order_status is not None:
            if not self.futures:
                if order_status['status'] == 'FILLED':
                    order_status['avgPrice'] = self._get_execution_price(contract, order_status['orderId'])
                else:
                    order_status['avgPrice'] = 0

            order_status = OrderStatus(order_status, self.platform)
        
        return order_status
        '''
    # cancel order when required
    # receives the Contract and the order id to cancel
    # returns an OrderStatus object
    def cancel_order(self, contract: Contract, order_id: int) -> OrderStatus:
        data = dict()
        data['orderId'] = order_id
        data['symbol'] = contract.symbol

        if self.futures:
            order_status = self._send_signed_request('DELETE', '/fapi/v1/order', data)
        else:
            order_status = self._send_signed_request('DELETE', '/api/v3/order', data)

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
        data = dict()
        data['symbol'] = contract.symbol
        data['orderId'] = order_id

        if self.futures:
            order_status = self._send_signed_request('GET', '/fapi/v1/order', data)
        else:
            order_status = self._send_signed_request('GET', '/api/v3/order', data)

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

        trades = self._send_signed_request('GET', '/api/v3/myTrades', data)

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

    # Websocket manager
    def start_ws(self):

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

        self.ws_connected = True

        for channel in ['bookTicker', 'aggTrade']:
            for symbol in self.ws_subscriptions[channel]:
                self.subscribe_channel([self.contracts[symbol]], channel, reconnection=True)

        if 'BTCUSDT' not in self.ws_subscriptions['bookTicker']:
            self.subscribe_channel([self.contracts['BTCUSDT']], 'bookTicker')

    def _on_close(self, ws, *args, **kwargs):
        logger.warning('Websocket connection closed')
        self.ws_connected = False

    def _on_error(self, ws, msg: str):
        logger.error('Binance connection error: %s', msg)

    # this is the most important function for the ws manager because it will interpret what the ws is sending
    # read binance documentation to see what the letters mean
    def _on_message(self, ws, msg: str):

        data = json.loads(msg)

        if 'u' in data and 'A' in data:
            data['e'] = 'bookTicker'  # For Binance Spot, to make the data structure uniform with Binance Futures
            # See the data structure difference here:
            # https://binance-docs.github.io/apidocs/spot/en/#individual-symbol-book-ticker-streams

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
            if data['e'] == 'aggTrade':
                symbol = data['s']

                for key, strat in self.strategies.items():
                    if strat.contract.symbol == symbol:
                        prices.prices[symbol] = float(data['p'])
                        res = strat.parse_trades(float(data['p']), float(data['q']), data['T'])
                        strat.check_trade(res)

    # subscribe channels to receive data from ws
    def subscribe_channel(self, contracts: typing.List[Contract], channel: str, reconnection=False):

        if len(contracts) > 200:
            logger.warning("Subscribing to more than 200 symbols will most likely fail. "
                           "Consider subscribing only when adding a symbol to your Watchlist or when starting a "
                           "strategy for a symbol.")

        data = dict()
        data['method'] = 'SUBSCRIBE'
        data['params'] = []

        if len(contracts) == 0:
            data['params'].append(channel)
        else:
            for contract in contracts:
                if contract.symbol not in self.ws_subscriptions[channel] or reconnection:
                    data['params'].append(contract.symbol.lower() + '@' + channel)
                    if contract.symbol not in self.ws_subscriptions[channel]:
                        self.ws_subscriptions[channel].append(contract.symbol)

            if len(data['params']) == 0:
                return

        data['id'] = self._ws_id

        try:
            self.ws.send(json.dumps(data))
            logger.info("Binance: subscribing to: %s", ','.join(data['params']))
        except Exception as e:
            logger.error("Websocket error while subscribing to @bookTicker and @aggTrade: %s", e)

        self._ws_id += 1

    # calculate the size of the trade and return it
    def get_trade_size(self, contract: Contract, price: float, balance_pct: float):

        logger.info('Getting Binance trade size...')
        balance = self.get_balances()
        if balance is not None:
            if contract.quote_asset in balance:
                if self.futures:
                    balance = balance[contract.quote_asset].wallet_balance
                else:
                    balance = balance[contract.quote_asset].free
            else:
                return None
        else:
            return None

        trade_size = (balance * balance_pct / 100) / price

        trade_size = round(round(trade_size / contract.lot_size) * contract.lot_size, 8)

        logger.info('Binance current %s balance = %s, trade size = %s', contract.quote_asset, balance, trade_size)

        return trade_size

    def _check_for_filters(self, contract: Contract, qty_to_order: float, asset_price: float) -> float:
        # rules to pass LOT_SIZE filter
        '''
        {
            "filterType": "LOT_SIZE",
            "minQty": "0.00100000",
            "maxQty": "100000.00000000",
            "stepSize": "0.00100000"
          }
        quantity >= minQty
        quantity <= maxQty
        (quantity - minQty) % stepSize == 0
        '''

        new_quantity: float = 0.0

        if qty_to_order <= contract.min_ls:
            print('Not passed, qty wanted: %s qty expected: %s', qty_to_order, contract.min_ls)
            while True:
                new_quantity += round(float((abs(contract.min_ls - qty_to_order) * (new_quantity * 0.5))), 8)
                if new_quantity % contract.lot_size == 0:
                    print('New quantity: ', new_quantity)
                    break

        trade_price = calculate_trade_value(qty_to_order, new_quantity)

        if trade_price <= contract.minNotional:
            print('Not passed, min Notional: %s qty expected: %s', contract.minNotional, trade_price)

        return new_quantity
