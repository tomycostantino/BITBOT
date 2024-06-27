from connectors.binance import BinanceClient
from database.login_database import LoginDatabase


class Login:

    '''Class that creates Binance client and passes it to the root component'''

    def __init__(self, api_key='', api_secret='', testnet=True, futures=True):

        self._binance = None
        self._db = LoginDatabase()

    def return_client(self):
        '''
        Returns the BinanceClient object
        :return:
        '''
        return self._binance

    def create_user(self, username: str, password: str, testnet: bool, futures: bool, api_key: str, api_secret: str):
        if self._db.user_exists(username):
            return False
        else:
            self._db.create_user(username, password, testnet, futures, api_key, api_secret)
            return True

    def login(self, username: str, password: str):
        self._binance = BinanceClient(api_key, api_secret, testnet, futures)
