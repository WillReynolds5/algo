import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import talib
from binance.client import Client
from simulation.data import load_market_data


class Trader:


    def __init__(self, tickers, start, end):
        self.tickers = tickers
        self.start = start
        self.end = end
        self.cash_balance = 100



    def simulate(self):


        returns, prices, volume = load_market_data(tickers, start, end, Client.KLINE_INTERVAL_5MINUTE)
        highest_return = {'return': 0, 'time_period_bb': 0, 'time_period_rsi': 0, 'return_limit': 0, 'stop_limit': 0}

        for sim in range(1):
            print(sim)

            ticker_balances = []
            ticker_returns = []
            tickers_closes = []
            all_returns = []

            # time_period_bb = random.randint(10, 40)
            time_period_bb = 20
            # time_period_rsi = random.randint(5, 25)
            time_period_rsi = 10
            # return_limit = random.randint(2, 7) / 100
            return_limit = 0.015
            # rsi_buy_limit = random.randint(5, 25)
            rsi_buy_limit = 20

            # stop_limit = random.randint(1, 10) / -100
            stop_limit = -0.1

            # .08 = 1.4
            # .11 = 2.7
            # 0.10 = 5.7

            for t in range(len(tickers)):

                # Update Ticker Sell Limit
                # self.current_positions[ticker]['time'] += 1
                # current_sell_limit = self.current_positions[ticker]['sell_limit']
                # updated_sell_limit = current_sell_limit - (self.current_positions[ticker]['time']/5)
                # if updated_sell_limit < 0.01:
                #     self.current_positions[ticker]['sell_limit'] = 0.015
                # else:
                #     self.current_positions[ticker]['sell_limit'] = updated_sell_limit

                upper, middle, lower = talib.BBANDS(prices[t], timeperiod=time_period_bb, nbdevup=2, nbdevdn=2, matype=0)
                rsi = talib.RSI(prices[t], timeperiod=time_period_rsi)

                # agent info
                balance = 1000
                shares = 0
                trading_fee = 0.001
                position_open = False
                position_open_index = 0

                num_buys = 0
                num_sells = 0
                returns = []
                sell_markers = []
                buy_markers = []

                position_buy_price = 0
                minute_counter = 0
                # loop through time
                for i in range(len(prices[t])):

                    buy_fee = balance * trading_fee
                    traded_shares = (balance - buy_fee) / prices[t][i]

                    portfolio_value = shares * prices[t][i]
                    sell_fee = portfolio_value * trading_fee
                    traded_dollars = portfolio_value - sell_fee

                    # RUN EVERY 30 MINUTES
                    # if minute_counter % 1 == 0:
                    current_return = (prices[t][i] / position_buy_price) - 1

                    # BUY WHEN DROPS
                    if position_open == False and prices[t][i] < lower[i] and rsi[i] < rsi_buy_limit:
                        # print('Buy')
                        shares += traded_shares
                        balance = 0
                        position_open = True
                        position_open_index = i
                        position_buy_price = prices[t][i]
                        buy_markers.append(i)
                        num_buys += 1

                    # SELL WHEN RETURN IS MADE
                    elif position_open == True and current_return >= return_limit:

                        balance += traded_dollars
                        shares = 0
                        position_open = False
                        num_sells += 1

                        sell_return = (prices[t][i] / position_buy_price) - 1
                        # print('RETURN: {}'.format(sell_return))

                        returns.append(sell_return)
                        sell_markers.append(i)

                    # SEELL WHEN STOPPING LIMMIT HITS
                    elif position_open == True and current_return <= stop_limit:

                        balance += traded_dollars
                        shares = 0
                        position_open = False
                        num_sells += 1

                        sell_return = (prices[t][i] / position_buy_price) - 1
                        # print('STOP LIMIT RETURN: {}'.format(sell_return))

                        returns.append(sell_return)
                        sell_markers.append(i)


                    # IF END IS HIT SELL ALL SHARES
                    if i == len(prices[t])-1 and position_open == True:

                        balance += traded_dollars
                        shares = 0
                        position_open = False
                        num_sells += 1
                        sell_return = (prices[t][i] / position_buy_price) - 1

                        returns.append(sell_return)
                        sell_markers.append(i)

                    minute_counter += 1



                if (num_buys) > 0:
                    average_return = np.mean(returns)
                    [all_returns.append(ret) for ret in returns]
                    ticker_balances.append(balance)
                    ticker_returns.append(average_return)
                    tickers_closes.append(num_sells)


                    print('Ticker: {}, Balance: {}, Average Return: {}, Num Buys: {}'.format(tickers[t], balance, average_return, num_buys))
                    #
                    plt.plot(prices[t], '-b')
                    plt.plot(prices[t], 'gs', markevery=buy_markers,  markersize=4)
                    plt.plot(prices[t], 'rs', markevery=sell_markers, markersize=4)
                    # plt.plot(lower)
                    plt.show()


            average_balance = np.mean(ticker_balances)
            average_return = np.mean(ticker_returns)
            average_sells = np.mean(tickers_closes)


            print('Overall Report -- Balance: {}, Average Return: {}, Num Sell: {}'.format(average_balance, average_return, average_sells))
            if highest_return['return'] == 0:
                highest_return['return'] = average_balance
                highest_return['time_period_bb'] = time_period_bb
                highest_return['rsi_buy_limit'] = rsi_buy_limit
                highest_return['return_limit'] = return_limit
            elif average_balance > highest_return['return']:
                highest_return['return'] = average_balance
                highest_return['time_period_bb'] = time_period_bb
                highest_return['rsi_buy_limit'] = rsi_buy_limit
                highest_return['return_limit'] = return_limit
                highest_return['stop_limit'] = stop_limit


            print('')
            print(highest_return)


if __name__ == "__main__":


    load_method = 'api'
    start = '20210129'
    end = '20210231'

    tickers = pd.read_csv('../tickers/USDT_tickers.csv').to_numpy().flatten().tolist()
    # tickers = ['ZILUSDT', 'BTCUSDT']
    trade_bot = Trader(tickers, start, end)
    trade_bot.simulate()


