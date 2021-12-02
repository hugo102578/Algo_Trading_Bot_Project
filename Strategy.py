import backtrader as bt
import scipy.stats as stats
import numpy as np
from talib import MA_Type

class BBRSI(bt.Strategy):
    params = dict(sd_up = 0.0 , sd_low = 2.0, OVER_SOLD = 30, Stop_Loss = 3, ATR_Period = 14, RSI_Period = 14)
    
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0) 
        #print('%s, %s' % (dt.isoformat(), txt))
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
        # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

    # Check if an order has been completed
    # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)
    
            self.bar_executed = len(self)
    
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
    
        # Write down: no pending order
        self.order = None
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))    
    
    def __init__(self):
        self.BB = bt.talib.BBANDS(self.data.close, timeperiod = 20, nbdevup = self.params.sd_up, nbdevdn = self.params.sd_low, matype = 1)
        self.rsi = bt.talib.RSI(self.data.close, timeperiod = self.params.RSI_Period)
        self.atr = bt.talib.ATR(self.data.high, self.data.low, self.data.close, timperiod = self.params.ATR_Period)
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high

    def next(self):
        if self.position.size == 0:         #No Position
            if self.dataclose[0] < self.BB.lowerband[0] and self.rsi[0] < self.params.OVER_SOLD:
                self.buy()
                self.stop_loss = self.dataclose[0] - (self.atr[0] * self.params.Stop_Loss)
                #self.stop_loss = self.dataclose[0] * 0.7

        else:
            if self.dataclose[0] > self.BB.middleband[0] or self.dataclose[0] < self.stop_loss:
                self.close()


class BBRSI_Long_Short(bt.Strategy):
    params = dict(sd_up=2.0, sd_low=2.0, OVER_SOLD=30, OVER_BOUGHT=70, Stop_Loss=3.0, RSI_Period=14, BB_Period=20)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        # print('%s, %s' % (dt.isoformat(), txt))

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def __init__(self):
        #self.BB = bt.talib.BBANDS(self.data.close, timeperiod=self.params.BB_Period, nbdevup=self.params.sd_up, nbdevdn=self.params.sd_low, matype=0)
        self.rsi = bt.talib.RSI(self.data.close, timeperiod=self.params.RSI_Period)
        #self.atr = bt.talib.ATR(self.data.high, self.data.low, self.data.close, timperiod=20)
        self.sma = bt.talib.SMA(self.data.close, timeperiod=20)
        self.sd = bt.talib.STDDEV(self.data.close, timeperiod=20, nbdev=1.0)
        self.dataclose = self.datas[0].close
        self.datahigh = self.datas[0].high

    def next(self):
        self.zscore = (self.dataclose[0] - self.sma[0]) / self.sd
        if self.position.size == 0:  # No Position
            if self.zscore < -2 and self.rsi[0] < 30: #self.dataclose[0] < self.BB.lowerband[0] and self.rsi[0] < self.params.OVER_SOLD:  # Open Long
                self.buy()
                #self.stop_loss = self.dataclose[0] - (self.atr[0] * self.params.Stop_Loss)

            elif self.zscore > 2 and self.rsi[0] > 70: #self.dataclose[0] > self.BB.upperband[0] and self.rsi[0] > self.params.OVER_BOUGHT:  # Open Short
                self.sell()
                #self.stop_loss = self.dataclose[0] + (self.atr[0] * self.params.Stop_Loss)

        elif self.position.size > 0:  # Close Long
            if self.zscore >= 0: #self.dataclose[0] > self.BB.middleband[0] or self.dataclose[0] < self.stop_loss:
                self.close()

        elif self.position.size < 0:  # Close Short
            if self.zscore <= 0: #self.dataclose[0] < self.BB.middleband[0] or self.dataclose[0] > self.stop_loss:
                self.close()














           
class Ketler(bt.Strategy):
    params = dict(ema = 20, atr = 20)
    lines = ('expo', 'atr','upper','lower')
    plotinfo = dict(subplot = False)
    plotlines = dict(upper = dict(ls = '--'),
                     lower = dict(_samecolor = True))
        
    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0) 
        print('%s, %s' % (dt.isoformat(), txt))
        
    def __init__(self):
        self.expo = bt.talib.EMA(self.datas[0].close, timeperiod = self.params.ema)
        self.atr = bt.talib.ATR(self.data.high, self.data.low, self.data.close, timeperiod = self.params.atr)
        self.upper = self.expo + 2 *self.atr        
        self.lower = self.expo - 2 *self.atr
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
           
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None
        
    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
        
        if self.order:
            return
        
        if not self.position:
            if self.dataclose[0] < self.lower:
                self.order = self.buy()
                 
        else:
            if self.dataclose[0] > self.upper:
                self.order = self.sell()          



   



