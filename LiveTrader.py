import os
import json
import datetime as dt
import pytz
import math
import numpy as np
import talib as ta
import pandas as pd

from binance.websockets import BinanceSocketManager
from binance.client import Client
from binance.enums import *
from config import *
import matplotlib.pyplot as plt
from twilio.rest import Client as twillio_client

# data_client = Client(API_KEY, API_SECRET)
trading_client = Client(API_KEY, API_SECRET, tld='us')
bm = BinanceSocketManager(trading_client)

# Your Account Sid and Auth Token from twilio.com/console
# and set the environment variables. See http://twil.io/secure
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
twillio_client = twillio_client(account_sid, auth_token)
phone_numbers = ['+12134004041', '+18024974614']  #, '+13014489928''+18024974614',  '+13014489928', '+16033202307', '+16177943074'
admin_numbers = ['+12134004041']
file_names = ['BUSD_tickers.csv', 'USD_tickers.csv', 'USDT_tickers.csv']

class LiveTrader:

    def __init__(self):
        self.USDT_tickers = pd.read_csv('tickers/USDT_tickers.csv', header=None).to_numpy().flatten().tolist()
        self.USD_tickers = pd.read_csv('tickers/USD_tickers.csv', header=None).to_numpy().flatten().tolist()
        # self.BUSD_tickers = pd.read_csv('tickers/BUSD_tickers.csv', header=None).to_numpy().flatten().tolist()
        self.tickers = {'USDT': self.USDT_tickers, 'USD': self.USD_tickers}
        self.sell_limit = 0.015
        self.stop_limit = -0.10
        self.buy_limit_rsi = 20
        self.account_info = {}
        self.check_balance()
        self.return_history = {}

        for type in self.tickers.keys():
            for ticker in self.tickers[type]:
                self.account_info[ticker] = {'position_open': False, 'type': type, 'price': 0, 'time': 0,
                                             'sell_limit': self.sell_limit, 'amount_traded': 0, 'order_filled': False}
                self.account_info[ticker]['filters'] = trading_client.get_symbol_info(ticker)['filters']

        with open('account_info.json') as acc_info:
            existing_positions = json.load(acc_info)
            for ex_pos in existing_positions.keys():
                for keys in existing_positions[ex_pos]:
                    self.account_info[ex_pos][keys] = existing_positions[ex_pos][keys]

    def get_data(self, ticker, bar_level):
        try:
            if bar_level == 'minute':
                data = trading_client.get_historical_klines(ticker, trading_client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
            elif bar_level == '5minute':
                data = trading_client.get_historical_klines(ticker, trading_client.KLINE_INTERVAL_5MINUTE, "1 day ago UTC")

            closing_prices = []
            volume = []
            for i in data:

                volume.append(float(i[5]))
                closing_prices.append(float(i[4]))

            closing_prices = np.array(closing_prices)
            upper, middle, lower = ta.BBANDS(closing_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            rsi = ta.RSI(closing_prices, timeperiod=10)
            return closing_prices, upper, lower, rsi, volume

        except Exception as e:
            assert ConnectionRefusedError, e

    def build_data(self, ticker):
        minute_prices, _, _, _, _ = self.get_data(ticker, 'minute')
        five_minute_prices = []
        counter = 5

        for p in reversed(range(len(minute_prices))):
            if p >= 5 and counter % 5 == 0:
                # avg = np.mean(minute_prices[p - 4:p])
                five_minute_prices.append(minute_prices[p])
            counter += 1

        five_minute_prices = np.flip(five_minute_prices)
        upper, middle, lower = ta.BBANDS(five_minute_prices, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
        rsi = ta.RSI(five_minute_prices, timeperiod=10)

        # plt.plot(lower)
        # plt.plot(five_minute_prices)
        # plt.show()
        return minute_prices, upper, lower, rsi

    def get_coin_balance(self, ticker):
        return trading_client.get_asset_balance(asset=ticker[:-4])

    def pair_to_ticker(self, pair):

        if pair[-4:] == "USDT":
            return pair[:-4]
        elif pair[-3:] == "USD":
            return pair[:-3]

    def get_ticker_type(self, pair):
        if pair[-4:] == "USDT":
            return pair[-4:]
        elif pair[-3:] == "USD":
            return pair[-3:]


    def update(self, ticker):

        # start = dt.datetime.now()
        type = self.get_ticker_type(ticker)
        if type == 'USD':
            type_balance = self.USD_balance
        elif type == 'USDT':
            type_balance = self.USDT_balance
        try:
            # print(ticker)
            self.count_account_position(type)
            closing_prices, _, lower, rsi = self.build_data(ticker)

            # If Position is Closed
            if ticker not in self.account_info.keys() or self.account_info[ticker]['position_open'] == False:
                # CHECK FOR BUY SIGNAL
                if closing_prices[-1] < lower[-1] and rsi[-1] < self.buy_limit_rsi:
                    self.buy(type_balance, ticker, closing_prices, lower, rsi)

            # If position is open but not filled
            elif ticker in self.account_info.keys() and self.account_info[ticker]['position_open'] == True and self.account_info[ticker]['order_filled'] == False:
                self.check_order(ticker, self.account_info[ticker]['time'])

            # If Position is Open and Filled
            elif ticker in self.account_info.keys() and self.account_info[ticker]['position_open'] == True and self.account_info[ticker]['order_filled'] == True:

                current_return = (closing_prices[-1] / self.account_info[ticker]['price']) - 1
                # CHECK FOR SELL LIMIT
                # print(current_return)
                if current_return >= self.sell_limit:
                    self.sell(ticker, current_return, closing_prices)

                # CHECK FOR STOP LIMIT
                if current_return <= self.stop_limit:
                    self.sell(ticker, current_return, closing_prices)

                if ticker in self.return_history.keys():
                    self.return_history[ticker].append(current_return)
                else:
                    self.return_history[ticker] = [current_return]

            # print((dt.datetime.now() - start).total_seconds())

        except Exception as e:
            print(e)

        #
        # for key in self.return_history.keys():
        #     if len(self.return_history[key]) > 11:
        #         self.return_history[key] = self.return_history[key][-10:]
        #
        #     plt.plot(self.return_history[key], label=key)

        # plt.draw()
        # plt.pause(0.001)

        # write account info
        with open('account_info.json', 'w') as json_file:
            json.dump(self.account_info, json_file, sort_keys=True, indent=4)


    def buy(self, type_balance, ticker, closing_prices, lower, rsi):

        print('Bought {}'.format(ticker))
        try:
            if type_balance > 200:
                dollars_traded = 200
            elif type_balance > 11:
                dollars_traded = type_balance
            else:
                return
            # dollars_traded = int(type_balance / self.closed_positions)
            shares_traded = float(dollars_traded) / float(closing_prices[-1])*0.9998
            print('Shares Traded: {}, Dollars Traded: {}'.format(shares_traded, dollars_traded))
            minQty = float(self.account_info[ticker]['filters'][2]['minQty'])
            maxQty = float(self.account_info[ticker]['filters'][2]['maxQty'])

            step = self.account_info[ticker]['filters'][2]['stepSize']
            minNotional = float(self.account_info[ticker]['filters'][3]['minNotional'])
            precision = int(round(-math.log(float(step), 10), 0))
            shares_traded = round(shares_traded, precision)

            if shares_traded > minQty and shares_traded < maxQty and dollars_traded > minNotional:

                order = trading_client.order_limit_buy(
                    symbol=ticker,
                    quantity=shares_traded,
                    price=closing_prices[-1]
                )

                tz = pytz.timezone('America/Denver')
                time = dt.datetime.now(tz=tz)

                # Reset Dollar Balances after Sale
                self.check_balance()

                self.account_info[ticker]['position_open'] = True
                self.account_info[ticker]['order_filled'] = False
                self.account_info[ticker]['price'] = closing_prices[-1]
                self.account_info[ticker]['time'] = time.strftime("%m/%d/%Y, %H:%M:%S")
                self.account_info[ticker]['amount_traded'] = shares_traded
                self.account_info[ticker]['order_id'] = order['orderId']

                # Reset Dollar Balances after Sale
                self.check_balance()

                for number in phone_numbers:
                    message = twillio_client.messages \
                        .create(
                        body="Order Placed on {} @ ~${} - {}".format(
                            ticker, self.account_info[ticker]['price'],
                            self.account_info[ticker]['amount_traded'],
                            self.account_info[ticker]['time']),
                        from_='+16787125007',
                        to=number
                    )

            else:

                assert shares_traded > minQty, 'below min'
                assert shares_traded < maxQty, 'above max'
                assert dollars_traded > minNotional, 'less then 10 USD'
                assert shares_traded % step == 0, 'wrong step size'

        except Exception as e:
            self.communicate_error('{}: {}'.format('BuyError', e))
            print(ConnectionRefusedError, e)

    def check_order(self, ticker, time):

        time_bought = dt.datetime.strptime(time, "%m/%d/%Y, %H:%M:%S")
        time_delta = dt.datetime.now() - time_bought
        if time_delta > dt.timedelta(seconds=60):
            order_status = trading_client.get_all_orders(symbol=ticker, limit=1)[0]['status']
            if order_status == 'FILLED' or order_status == 'PARTIALLY_FILLED':
                # Reset Dollar Balances after Sale
                self.check_balance()
                self.account_info[ticker]['order_filled'] = True

                for number in phone_numbers:
                    message = twillio_client.messages \
                        .create(
                        body="Order Filled on {} @ ~${}. for {} - {}".format(
                            ticker, self.account_info[ticker]['price'],
                            self.account_info[ticker]['amount_traded'],
                            self.account_info[ticker]['time']),
                        from_='+16787125007',
                        to=number
                    )
            else:

                print('cancel order')
                self.account_info[ticker]['position_open'] = False
                self.account_info[ticker]['order_filled'] = False
                result = trading_client.cancel_order(
                    symbol=ticker,
                    orderId=self.account_info[ticker]['order_id'])

    def sell(self, ticker, current_return, closing_prices):

        print('Sold {}'.format(ticker))
        try:
            # amount_traded = self.account_info[ticker]['amount_traded']
            balance = float(trading_client.get_asset_balance(asset=self.pair_to_ticker(ticker))['free'])
            step = self.account_info[ticker]['filters'][2]['stepSize']
            precision = int(round(-math.log(float(step), 10), 0))
            amount_traded = balance*0.9980
            amount_traded = round(amount_traded, precision)

            order = trading_client.order_market_sell(
                symbol=ticker,
                quantity=amount_traded,
            )

            # Reset Dollar Balances after Sale
            self.check_balance()
            self.account_info[ticker]['position_open'] = False

            for number in phone_numbers:
                message = twillio_client.messages \
                    .create(
                    body="Sold {} {} @ ~${} for {}% return.".format(amount_traded, ticker, closing_prices[-1], round(current_return * 100, 4)),
                    from_='+16787125007',
                    to=number
                )

        except Exception as e:
            self.communicate_error('{}: {}'.format('SellError', e))
            assert ConnectionRefusedError, e

    def count_account_position(self, type):

        closed_positions = 0
        for ticker in self.account_info:
            if self.account_info[ticker]['type'] == type and self.account_info[ticker]['position_open'] == False:
                closed_positions += 1

        self.closed_positions = closed_positions


    def check_balance(self):

        self.USDT_balance = int(trading_client.get_asset_balance(asset='USDT')['free'].split('.')[0])
        self.USD_balance = int(trading_client.get_asset_balance(asset='USD')['free'].split('.')[0])
        # self.BUSD_balance = int(trading_client.get_asset_balance(asset='BUSD')['free'].split('.')[0])


    def communicate_error(self, error):
        for number in admin_numbers:
            message = twillio_client.messages \
                .create(
                body=error,
                from_='+16787125007',
                to=number
            )