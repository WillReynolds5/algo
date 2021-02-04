import numpy as np
import pandas as pd
from config import *
from binance.client import Client




def load_market_data(all_tickers, start, end, interval):
    client = Client(API_KEY, API_SECRET, tld='us')
    market_close = []
    market_returns = []
    market_volume = []
    for ticker in all_tickers:
        print("ticker: {}".format(ticker))
        months = pd.date_range(start, end, freq='1D').strftime("%d %b, %Y").tolist()
        close = np.array([])
        volume = np.array([])
        for dates in range(len(months) - 1):
            # data = client.get_historical_klines(ticker, interval, months[dates], months[dates + 1])
            data = client.get_historical_klines(ticker, client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")

            month_closing_prices = []
            month_volume = []
            for i in data:
                month_volume.append(float(i[5]))
                month_closing_prices.append(float(i[4]))

            close = np.hstack([close, month_closing_prices])
            volume = np.hstack([volume, month_volume])

        close = np.array(close)
        volume = np.array(volume)
        returns = (close[:-1] / close[1:]) - 1

        if market_returns == []:
            market_returns = returns
            market_close = close
            market_volume = volume
        else:
            market_returns = np.vstack((market_returns, returns))
            market_close = np.vstack((market_close, close))
            market_volume = np.vstack((market_volume, volume))

    return market_returns, market_close[:, :-1], market_volume