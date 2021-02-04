from LiveTrader import LiveTrader
import datetime
import websocket
import schedule
import asyncio
try:
    import thread
except ImportError:
    import _thread as thread
import json
trader = LiveTrader()


def update_trader(ticker):
    try:
        trader.update(ticker)
    except Exception as e:
        print(e)





if __name__ == '__main__':

    tickers = []
    usd = [tickers.append(tick) for tick in trader.USD_tickers]
    udst = [tickers.append(tick) for tick in trader.USDT_tickers]

    for t in tickers:
        schedule.every(20).seconds.do(update_trader, ticker=t)

    while True:
        schedule.run_pending()