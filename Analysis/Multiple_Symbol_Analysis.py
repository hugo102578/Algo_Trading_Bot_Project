import pandas as pd
import numpy as np
from math import sqrt

#Create a combined list for specific crypto currency
pair = ['BTC','ETH','BNB','XRP','LTC','DOGE']
Daily_Return = np.array([])
Annual_Return = np.array([])
Sharpe_Ratio = np.array([])
Stand_Deviation = np.array([])
Combined = pd.DataFrame()
Correlation = pd.DataFrame()

for item in pair:
    Dataset = pd.read_csv(r'D:/Python//Binance_Python_Project/Data/'+item+'USDT.csv', parse_dates=True, index_col=0)
    
    Close = Dataset.loc[:,'Close']
    Close = Close.rename(item+' Close')
    
    Return = Close.pct_change(-1)
    Return = Return.rename(item+' % Return')
    
    Combined = pd.concat([Combined,Close,Return],axis=1)
    
#Create Close Price table for Correlation Analysis    
    Correlation = pd.concat([Correlation,Close],axis=1)

    
#Analyze Risk and Return
    Daily_Return = np.append(Daily_Return, Return.mean())
    Annual_Return = np.append(Annual_Return, Return.mean() * sqrt(365))
    Stand_Deviation = np.append(Stand_Deviation, Return.std())
    Sharpe_Ratio = np.append(Sharpe_Ratio, Return.mean() / Return.std() * sqrt(365))
    
array = np.array([Daily_Return, Annual_Return, Stand_Deviation, Sharpe_Ratio])
Risk_And_Return = pd.DataFrame(array, index=['Daily Return', 'Annual Return','Standart Deviation','Sharpe Ratio'], columns = pair)


#Analyze Correlation
Correlation = Correlation.corr()


#Export Result to Excel Table
writer = pd.ExcelWriter(r'D:/Python//Binance_Python_Project/Analysis/Crpyto_Analysis_Result.xlsx', engine = 'xlsxwriter')
Risk_And_Return.to_excel(writer, sheet_name = 'Risk And Return')
Correlation.to_excel(writer, sheet_name = 'Correlation')

writer.save()



#Correlation.to_csv(r'C:/Python/Analysis/Correlation.csv')
Combined.to_csv(r'D:/Python//Binance_Python_Project/Analysis/Comparison_Pair.csv')


