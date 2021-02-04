import pandas as pd
import numpy as np
from binance.client import Client
from LiveTrader import LiveTrader
from config import *

class LSTM:

    def __init__(self):
        self.client = Client(API_KEY, API_SECRET, tld='us')

    def get_multi_aggregate(self, tickers, start_date, end_date):
        ticker_stack = []
        for t in tickers:

            months = pd.date_range(start_date, end_date, freq='1W').strftime("%d %b, %Y").tolist()
            assert len(months) > 2, "Date range must be greater than one month"
            close = np.array([])
            volume = np.array([])
            for dates in range(len(months) - 1):
                data = self.client.get_historical_klines(t, Client.KLINE_INTERVAL_1HOUR, months[dates], months[dates + 1])

                if len(data) == 0:
                    print('no data')
                    break
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

            # moving average of volume
            vol_20_day = []
            moving_average = 10
            for v in range(len(volume)):
                if v > (moving_average - 1):
                    mean = np.mean(volume[(v - moving_average):v])
                    vol_20_day.append(mean)

            volume = volume[moving_average:] / np.array(vol_20_day)

            if len(volume) > 0 and len(close) > 0:
                print(t)
                one_stack = np.array([volume[4:], returns[(moving_average - 1 + 4):]])
                ticker_stack.append(one_stack.T)
            else:
                print('{}: Returned Zero Results'.format(t))

        return np.array(ticker_stack)





if __name__ == '__main__':

    trader = LiveTrader()
    tickers = []
    usd = [tickers.append(tick) for tick in trader.USD_tickers]
    udst = [tickers.append(tick) for tick in trader.USDT_tickers]


    training = ['20201201', '20210201']
    testing = ['20200301', '20200701']

    lstm = LSTM()
    lstm.get_multi_aggregate(tickers, training[0], training[1])

