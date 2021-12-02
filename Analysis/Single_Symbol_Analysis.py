import pandas as pd
from math import sqrt
pair = 'XRP'
Dataset = pd.read_csv(r'D:/Python//Binance_Python_Project/Data/'+pair+'USDT.csv', parse_dates=True, index_col=0)

#Autocorrelation Analysis
from statsmodels.graphics.tsaplots import plot_acf
plot_acf(Dataset['Close'], title=pair+' Autocorrelation')

#Historical Volatility Analysis (Daily)
Dataset['Daily Return'] = Dataset['Close'].pct_change()
Dataset['Historical Volatility'] = Dataset['Daily Return'].rolling(30).std() * sqrt(365)
#Dataset['Historical Volatility'].plot()
#plt.plot(Dataset['Historical Volatility'])

