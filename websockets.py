from LiveTrader import LiveTrader
import datetime
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import time
import json
from binance.websockets import BinanceSocketManager
from binance.client import Client
from config import *

trader = LiveTrader()
client = Client(API_KEY, API_SECRET, tld='us')
bm = BinanceSocketManager(client)


def on_message(ws, message):
    try:
        ticker = json.loads(message)['data']['s']
        trader.update(ticker)
    except Exception as e:
        print(e)

def on_error(ws, error):
    print(error)

def on_close(ws):
    print("### closed ###")
    start_websockets()


def on_open(ws):
    print('Open')


def start_websockets():
    tickers = []
    usd = [tickers.append(tick.lower()) for tick in trader.USD_tickers]
    udst = [tickers.append(tick.lower()) for tick in trader.USDT_tickers]

    kline_ticker = '{}@kline_1m'
    kline_tickers = [kline_ticker.format(t) for t in tickers]

    wss = "wss://fstream.binance.com/stream?streams="
    for t in kline_tickers:
        wss += '{}/'.format(t)

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp(wss,
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open
    ws.run_forever()

if __name__ == '__main__':
    start_websockets()
