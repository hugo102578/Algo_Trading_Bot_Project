from configparser import ConfigParser
from binance.client import Client
import pandas as pd
import winsound

config = ConfigParser()
config.read('.\API_Key.ini')
client = Client(config['Account']['key'],config['Account']['secret'])

Pairs = ['BNBUSDT','BTCUSDT','ETHUSDT', 'FILUSDT','TRXUSDT','UNIUSDT','LTCUSDT','XRPUSDT']
Pair = ['BTCUSDT']
# time_interval = '1Min_30Days'

#Extract Data from Binance API
def Data_Extractor(symbol,interval,period, time_interval):
    for item in symbol:
        klines = client.futures_historical_klines(item, interval, period)
        Dataset = pd.DataFrame(klines)
        Dataset = Dataset.astype(float)
        Dataset = Dataset.iloc[:,:6]      
    
    #Assign Column Name 
        try:
            Dataset.columns = ['Date','Open','High','Low','Close','Volume']                             
            Dataset['Date'] = pd.to_datetime(Dataset['Date'], unit='ms')    
            Dataset.to_csv(rf'D:/Python/Binance_Python_Project/Future Data/{time_interval}/'+item+'.csv', index=False)
            print(item, interval, ' Data Collected!')

        except ValueError:
            print('No Data for',item)
    winsound.Beep(500, 500)

# Data_Extractor(Pairs, '1m', '30 days ago UTC', '1Min_30Days')
