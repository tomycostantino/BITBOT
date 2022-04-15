import csv
import pandas as pd
import datetime as dt
import numpy as np

import requests
import typing


def make_request(method: str, endpoint: str, data: typing.Dict):
    if method == 'GET':
        try:
            public_key = '5CWQHvHfhyU9WWWWiRUaY0xbq6wmQkgO4512GKupzTkrwwdiTphQQxsZQCcB48rM'
            headers = {'X-MBX-APIKEY': public_key}
            response = requests.get("https://api.binance.com" + endpoint, params=data, headers=headers)
        except Exception as e:
            print('Connection error while making %s request to %s: %s', method, endpoint, e)
            return None

        # check if the response is valid, 200 means that
        if response.status_code == 200:
            return response.json()


def get_candlesticks(symbol: str, interval: str, start_time: str):
    """Get all the klines from api"""
    data = dict()
    data['symbol'] = symbol
    data['interval'] = interval
    data['limit'] = 1000

    if start_time is not None:
        data['startTime'] = start_time

    raw_candles = make_request('GET', '/api/v3/klines', data)

    if raw_candles is not None:
        # delete unwanted data - just keep date, open, high, low, close and volume
        for c in raw_candles:
            del c[6:]

    df = pd.DataFrame(raw_candles, columns=['date', 'open', 'high', 'low', 'close', 'volume'])
    for idx in df.columns[1:]:
        df[idx] = df[idx].astype(float)

    return df
