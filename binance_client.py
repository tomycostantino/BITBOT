import logging
import requests
import typing
from binance.client import Client
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

    def get_balances(self, assets):
        balances = {}
        for asset in assets:
            balance = self._client.get_asset_balance(asset=asset)
            balances[asset] = balance
        return balances
