import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import time

from connectors.binance import BinanceClient
from data_extractor import get_candlesticks

# ML imports
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score

df = get_candlesticks('BTCUSDT', '30m', None)

sns.set(font_scale=1.5)
plt.figure(figsize=(12, 10))
sns.regplot(x=df.index, y='close', data=df, ci=None, color='r')


plt.show()

# print(df.head(50))
