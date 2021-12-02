from configparser import ConfigParser
from binance.client import Client
import pandas as pd
from binance.enums import *
from pprint import pprint


config = ConfigParser()
config.read('.\API_Key.ini')
client = Client(config['Account']['key'],config['Account']['secret'])
pd.set_option('precision',4)
pd.set_option('display.max_columns',14)
pd.set_option("display.width", 10000)

def Deposit():
    def withdraw():
        withdraw = pd.DataFrame(client.get_withdraw_history()['withdrawList'])
        withdraw = withdraw.loc[:,['applyTime','asset','amount','status']]
        withdraw.rename(columns = {'applyTime':'timestamp'}, inplace=True)
        withdraw['timestamp'] = pd.to_datetime(withdraw['timestamp'], unit='ms')
        withdraw['amount'] = 0 - withdraw['amount']
        withdraw['status'] = 'CONFIRMED'
        withdraw.insert(3,'type','Withdraw')
        return withdraw
    
    Spot_To_Future = client.query_universal_transfer_history(type = "MAIN_UMFUTURE")
    Future_To_Spot = client.query_universal_transfer_history(type = "UMFUTURE_MAIN")
    C2C_To_Spot = pd.DataFrame(client.query_universal_transfer_history(type = "C2C_MAIN")['rows'])
    C2C_To_Future = pd.DataFrame(client.query_universal_transfer_history(type = "C2C_UMFUTURE")['rows'])
    Deposit_History = C2C_To_Spot.append(C2C_To_Future)
    Deposit_History['timestamp'] = pd.to_datetime(Deposit_History['timestamp'],unit = 'ms')
    Deposit_History['amount'] = Deposit_History['amount'].astype(float)
    Deposit_History = Deposit_History.append(withdraw())

    Deposit_History.loc['Total'] = Deposit_History[['amount']].sum()
    return Deposit_History

def future_balance():
    full_balance = client.futures_account()
    asset = pd.Series(full_balance['assets'][1])
    balance = asset.loc[['updateTime','asset','walletBalance','unrealizedProfit', 'availableBalance',]]
    balance['updateTime'] = pd.to_datetime(balance['updateTime'], unit = 'ms')
    return balance

class summary():
    def transaction_history(self, symbol):
        trades = pd.DataFrame(client.get_my_trades(symbol = symbol))
        trades = trades.loc[:,['symbol','time','price','quoteQty','qty','commission','commissionAsset','isBuyer']]
        trades.rename(columns = {'quoteQty':'Cost (USDT)', 'qty':'Quantity'},inplace=True)
        trades[['Cost (USDT)','Quantity','price','commission']] = trades[['Cost (USDT)','Quantity','price','commission']].astype(float)
        
        trades.loc[trades.commissionAsset != 'USDT' , 'Quantity'] = trades['Quantity'] - trades['commission']
        trades.loc[trades.isBuyer == False, ['Cost (USDT)','Quantity',]] = 0-trades.loc[:,['Cost (USDT)','Quantity']] 
        trades.loc[trades.commissionAsset == 'USDT' , 'Cost (USDT)'] = trades['Cost (USDT)'] + trades['commission']     ####
        trades['time'] = pd.to_datetime(trades['time'], unit = 'ms')
        trades.sort_values(by='time', ascending = False, inplace=True)
    
        trades.loc['Total'] = trades[['Cost (USDT)','Quantity']].sum()
        trades.loc['Total','price'] = trades.iloc[-1]['Cost (USDT)'] / trades.iloc[-1]['Quantity']                   #'price' = Average Cost
        return trades
        
    def spot(self):
        spot_asset = pd.DataFrame(client.get_account()['balances'])
        spot_asset.drop(columns = 'locked', inplace = True)
        spot_asset['free'] = spot_asset['free'].astype(float)
        spot_asset = spot_asset[spot_asset['free']>0]
        USDT_row = spot_asset[spot_asset.asset == "USDT"]
        spot_asset = spot_asset[spot_asset.asset != "USDT"]                         #Put USDT to first row
        spot_asset = pd.concat([USDT_row,spot_asset])   
        return spot_asset
   
    def Coin_Except_USDT(self):
        Coin_In_Wallet = self.spot()['asset']
        Coin_Except_USDT = Coin_In_Wallet[~Coin_In_Wallet.isin(["USDT", "USDC"])] + "USDT"
        Coin_Except_USDT = Coin_Except_USDT.tolist()                                #['BTCUSDT', 'FILUSDT' , 'GRTUSDT']
        return Coin_Except_USDT

    def spot_balance(self):
        coin = self.Coin_Except_USDT()                                              #['BTCUSDT', 'FILUSDT' , 'GRTUSDT']
        ticker = pd.DataFrame(client.get_symbol_ticker())                             
        ticker = ticker[ticker.symbol.isin(coin)]
        pair_only = ticker['symbol'].str[0:-4]
        ticker['symbol'] = pair_only                                                #['BTC','FIL','GRT']
        ticker.loc[-1,'symbol'] = 'USDT'
        ticker.loc[-1,'price'] = 1.0
        ticker.rename(columns = {'symbol':'asset'}, inplace = True)
        spot_asset = pd.merge(self.spot(),ticker)                                   #Inner Join
        spot_asset[['free','price']] = spot_asset[['free','price']].astype(float)
        spot_asset.rename(columns = {'price':'Current Ex. Rate','free':'Quantity'},inplace=True)   
        spot_asset['Current Value (USDT)'] = spot_asset['Quantity'] * spot_asset['Current Ex. Rate']
        
        spot_asset.insert(3,'Avg Buy Price',None)
        spot_asset.insert(5,'Cost (USDT)',None)     
        return spot_asset 

#Main Program Started
summary = summary()     

with pd.ExcelWriter(r'D:\Python\Binance_Python_Project\Account_Book.xlsx') as writer:
    dummy = pd.DataFrame()
    dummy.to_excel(writer, "Spot_Balance")
    Overview = summary.spot_balance()
    Deposit().to_excel(writer, sheet_name="Deposit", index=False)
    for symbol in summary.Coin_Except_USDT():
        tran_his = summary.transaction_history(symbol)
        pair_only = symbol[0:-4]
        Overview.loc[Overview.asset == pair_only, 'Cost (USDT)'] = tran_his.loc['Total','Cost (USDT)']          #Extract Avg cost from Transaction History
        Overview.loc[Overview.asset == pair_only, 'Avg Buy Price'] = tran_his.loc['Total','price']
        summary.transaction_history(symbol).to_excel(writer, sheet_name=symbol, index=False)
    Overview.loc[Overview.asset == 'USDT', 'Cost (USDT)'] = Overview['Current Value (USDT)']
    Overview.loc[Overview.asset == 'USDT', 'Avg Buy Price'] = Overview['Current Ex. Rate']
    Overview['PNL'] = Overview['Current Value (USDT)'] - Overview['Cost (USDT)']
    Overview['PNL (%)'] = (Overview['Current Value (USDT)'] / Overview['Cost (USDT)'] -1) * 100
    Overview.loc['Total'] = Overview.loc[:,['Current Value (USDT)','Cost (USDT)']].sum()
    Overview.loc['Total PNL','Current Value (USDT)'] = Overview.loc['Total','Current Value (USDT)'] -  Overview.loc['Total','Cost (USDT)']
    Overview.loc['Total PNL (%)','Current Value (USDT)'] = (Overview.loc['Total','Current Value (USDT)'] / Overview.loc['Total','Cost (USDT)'] - 1) *100  
    
    print(Overview)
    Overview.to_excel(writer, sheet_name="Spot_Balance")



