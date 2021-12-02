from configparser import ConfigParser
from binance.client import Client
from binance.enums import *
import websocket, json, talib, sqlite3, telebot, time
import pandas as pd
import numpy as np
from decimal import *
from multiprocessing import Process

pd.set_option('precision', 2)
pd.set_option('display.max_columns', 20)
pd.set_option('display.width', 10000)
config = ConfigParser()
config.read('.\API_Key.ini')
client = Client(config['Account']['key'], config['Account']['secret'])

def future_balance():
    full_balance = client.futures_account()
    asset = pd.Series(full_balance['assets'][1])
    balance = asset.loc[['updateTime', 'asset', 'walletBalance', 'unrealizedProfit', 'availableBalance']]
    balance['updateTime'] = pd.Timestamp(balance['updateTime'], unit='ms', tz='Asia/Hong_Kong')
    return balance

def main(TRADE_SYMBOL):
    PNL = 0
    buy_price = 0
    cost = 0
    middleband = [0]
    stop_loss = 0
    IN_POSITION = False
    Leverage = 2
    TRADE_SYMBOL = str.lower(TRADE_SYMBOL)
    conn = sqlite3.connect('Binance.db')
    cur = conn.cursor()


    def future_long_order(symbol, side, quantity, positionSide='LONG', type='MARKET'):
        order = client.futures_create_order(symbol=symbol, side=side, quantity=quantity, positionSide=positionSide,
                                            type=type)


    def get_historical_data(TRADE_SYMBOL):
        klines = client.futures_historical_klines(TRADE_SYMBOL, '1m', '30 minutes ago UTC')
        Historical_data = pd.DataFrame(klines)
        Historical_data = Historical_data.iloc[:, :6]
        Historical_data.columns = ['OpenTime', 'Open', 'High', 'Low', 'Close', 'Volume']
        Historical_data['OpenTime'] = pd.to_datetime(Historical_data['OpenTime'], unit='ms')
        return Historical_data


    def min_trade_amount(symbol):
        temp = pd.DataFrame(client.futures_exchange_info()['symbols'])
        temp = temp[temp['symbol'] == str.upper(symbol)]
        temp = temp['filters'].item()
        temp = pd.DataFrame(temp)
        temp = temp[temp['filterType'] == 'LOT_SIZE']
        temp = temp['stepSize'].item()
        return temp


    def quantity(symbol, leverage, min_trade_amount):
        symbol = str.upper(symbol)
        walletBalance = float(future_balance()['walletBalance'])
        budget_per_pair = (walletBalance * 0.95) / 3
        price = float(client.get_symbol_ticker(symbol=symbol)['price'])
        quantity = budget_per_pair / (price / leverage)
        quantity = float(Decimal(quantity).quantize(Decimal(min_trade_amount), rounding=ROUND_DOWN))
        return quantity

    def write_to_sqlite(conn, cur, trade_his):
        cur.execute("INSERT INTO trade_history VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", trade_his)
        conn.commit()

    def on_error(ws):
        print('error')

    def on_open(ws):
        print(f'Trading Pair: {TRADE_SYMBOL} | Quantity: {TRADE_QUANTITY} | Leverage: {Leverage}')

    def on_close(ws):
        print('Stop running')

    def on_message(ws, message):
        nonlocal his_candle, IN_POSITION, TRADE_QUANTITY, Leverage, PNL, buy_price, cost, middleband, stop_loss, conn, cur
        json_message = json.loads(message)
        candle = json_message['k']

        if candle['x'] and pd.to_datetime(candle['t'],unit='ms') > his_candle.iloc[-1, 0]:
            live_candle = pd.DataFrame(
                {'OpenTime': candle['t'], 'Open': candle['o'], 'Close': candle['c'], 'High': candle['h'],
                 'Low': candle['l'], 'Volume': candle['v']}, index=[0])
            live_candle = live_candle.astype(float)
            live_candle['OpenTime'] = pd.to_datetime(live_candle['OpenTime'], unit='ms')
            his_candle = his_candle.append(live_candle)
            his_candle = his_candle.tail(21)

            np_closes = np.array(his_candle['Close'], dtype=float)
            np_high = np.array(his_candle['High'], dtype=float)
            np_low = np.array(his_candle['Low'], dtype=float)
            rsi = talib.RSI(np_closes, timeperiod=14)
            atr = talib.ATR(np_high, np_low, np_closes, timeperiod=14)
            upperband, middleband, lowerband = talib.BBANDS(np_closes, timeperiod=20, nbdevup=2.0, nbdevdn=1.7, matype=1)
            last_close = his_candle.iloc[-1]['Close']
            # print(f'{his_candle.iloc[-1][0]} | Pair: {TRADE_SYMBOL} | Price: {last_close:.2f} | PNL: {PNL:.2f}')


            # Buy
            if not IN_POSITION:
                if last_close < lowerband[-1] and rsi[-1] < 27:
                    future_long_order(symbol=TRADE_SYMBOL, side='BUY', quantity=TRADE_QUANTITY)
                    IN_POSITION = True
                    stop_loss = last_close - (atr[-1] * 3.5)
                    cost = last_close * TRADE_QUANTITY / Leverage
                    buy_price = last_close
                    print(f'{his_candle.iloc[-1][0]} | Pair: {TRADE_SYMBOL} | Buy at:  {last_close:.2f} | Quantity: {TRADE_QUANTITY}')

                    #Store to SQLITE
                    time.sleep(0.1)
                    trade_his = pd.DataFrame(client.futures_account_trades(symbol=TRADE_SYMBOL)).tail(1).values
                    trade_his = tuple(trade_his[0])
                    write_to_sqlite(conn, cur, trade_his)


            # Sell
            elif IN_POSITION:
                if last_close > middleband[-1] or last_close < stop_loss:
                    future_long_order(symbol=TRADE_SYMBOL, side='SELL', quantity=TRADE_QUANTITY)
                    IN_POSITION = False
                    Revenue = (last_close - buy_price) * TRADE_QUANTITY
                    PNL += Revenue
                    PNL_Pct = (PNL / cost) * 100
                    print(f'{his_candle.iloc[-1][0]} | Pair: {TRADE_SYMBOL} | Sell at: {last_close:.2f} | Revenue: {Revenue:.2f} | Total PNL: {PNL:.2f} | Return(%): {PNL_Pct:.2f}')

                    #Store to SQLITE
                    time.sleep(0.1)
                    trade_his = pd.DataFrame(client.futures_account_trades(symbol=TRADE_SYMBOL)).tail(1).values
                    trade_his = tuple(trade_his[0])
                    write_to_sqlite(conn, cur, trade_his)
                    TRADE_QUANTITY = quantity(TRADE_SYMBOL, Leverage, min_trade_amount(TRADE_SYMBOL))


    TRADE_QUANTITY = quantity(TRADE_SYMBOL, Leverage, min_trade_amount(TRADE_SYMBOL))
    client.futures_change_leverage(symbol=TRADE_SYMBOL, leverage=Leverage)

    his_candle = get_historical_data(TRADE_SYMBOL)
    ws = websocket.WebSocketApp(f'wss://fstream.binance.com/ws/{TRADE_SYMBOL}@kline_1m',
                                on_open=on_open,
                                on_message=on_message,
                                on_close=on_close,
                                on_error=on_error)
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        conn.close()
        raise SystemExit

p1 = Process(target=main, args=('ETHUSDT',))
p2 = Process(target=main, args=('BNBUSDT',))
p3 = Process(target=main, args=('BTCUSDT',))

if __name__ == '__main__':
    print(future_balance())
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()







