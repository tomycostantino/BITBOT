from connectors.binance import BinanceClient


class Login:

    '''Class that creates Binance client and passes it to the root component'''

    def __init__(self, api_key, api_secret, testnet, futures):
        self._binance = BinanceClient(api_key, api_secret, testnet, futures)

    def return_client(self):
        '''
        Returns the BinanceClient object
        :return:
        '''
        return self._binance
