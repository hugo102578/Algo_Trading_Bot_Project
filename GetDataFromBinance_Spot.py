#D:/Python/Binance_Python_Project/Data

from configparser import ConfigParser
from binance.client import Client
import pandas as pd
import csv
config = ConfigParser()
config.read('API_Key.ini')
client = Client(config['Account']['key'],config['Account']['secret'])


#Extract all pair names based on USDT
def Get_All_USDT_Pairs():
    All_USDT_Pairs = []
    tickers = client.get_all_tickers()
    for item in tickers:
        if item['symbol'][-4:] == 'USDT':
            All_USDT_Pairs.append(item['symbol'])
            
    with open(r'D:/Python/Binance_Python_Project/Spot Data/All_USDT_Pairs.csv','w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter =',')
        writer.writerow(All_USDT_Pairs)
    return All_USDT_Pairs

#Extract Data from Binance API
def Data_Extractor(symbol,interval,period, spot):
    for item in symbol:
        klines = client.get_historical_klines(item, interval, period, spot)
        Dataset = pd.DataFrame(klines)
        Dataset = Dataset.astype(float)
        Dataset = Dataset.iloc[:,:6]      
    
    #Assign Column Name 
        try: 
            print(item,' Data Collected!')                                                       
            Dataset.columns = ['Date','Open','High','Low','Close','Volume']                             
            Dataset['Date'] = pd.to_datetime(Dataset['Date'], unit='ms')    
            Dataset.to_csv(r'D:/Python/Binance_Python_Project/Future Data/1Min_180Days/'+item+'_Future.csv', index=False)
        except ValueError:
            print('No Data for',item)

USDT_Pairs = Get_All_USDT_Pairs()
Specific_Pair = ['BNBUSDT','BTCUSDT','ETHUSDT', 'FILUSDT']
#Data_Extractor(Specific_Pair, '15m', '3 days ago UTC',False)
print(client.get_futures_historical_klines(symbol='BNBUSDT'))