import backtrader as bt
import Strategy
import pandas as pd
from numpy import arange
import winsound
from sklearn.model_selection import train_test_split

Pairs = ['BNBUSDT','BTCUSDT','ETHUSDT', 'FILUSDT','TRXUSDT','UNIUSDT','LTCUSDT','XRPUSDT']
Pair = ['BTCUSDT']
time_interval = '1Min_30Days'
Opt_List = pd.DataFrame(data=None,columns = ['Pair','sd_low / OverSold / Stop_Loss','Annual Return','Sharpe Ratio','DrawDown','Total Order'])

def Pivot_Table():
    Opt_List['sd_low / OverSold / Stop_Loss']=Opt_List['sd_low / OverSold / Stop_Loss'].astype(str)
    Opt_List['Total Order'] = Opt_List['Total Order'].astype(int)
    pt = pd.pivot_table(Opt_List, index=['sd_low / OverSold / Stop_Loss'],
                        aggfunc = {'Pair':'count',
                                   'Annual Return':'mean',
                                   'Sharpe Ratio':'mean',
                                   'DrawDown':'mean',
                                   'Total Order':'mean'})   
    pt = pt[pt.Pair>=5]
    pt = pt.dropna()
    pt.sort_values(by=['Annual Return','DrawDown'],ascending = [False,True],inplace=True)
    return pt
    
if __name__ == '__main__':
    for symbol in  Pairs:
    
        cerebro = bt.Cerebro()
        cerebro.broker.setcommission(commission=0.0002)   
        Dataset = pd.read_csv(rf'D:/Python/Binance_Python_Project/Future Data/{time_interval}/{symbol}.csv',parse_dates=True, index_col=0)    
        train, test = train_test_split(Dataset, test_size=0.5, shuffle=False)
        data = bt.feeds.PandasData(dataname = Dataset,
                                   timeframe = bt.TimeFrame.TFrame("Minutes"),
                                   compression = 1,
                                   openinterest=-1)
        cerebro.adddata(data)
        cerebro.optstrategy(Strategy.BBRSI,
                            sd_low = [1.8, 2.0],
                            OVER_SOLD = [27, 30],
                            Stop_Loss = [2.5, 3.0, 3.5],
                            )
        cerebro.broker.set_cash(1000000)
        cerebro.addsizer(bt.sizers.PercentSizer, percents = 98)
        
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0, factor = 365, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
        cerebro.addanalyzer(bt.analyzers.Returns, timeframe=bt.TimeFrame.Days, tann = 365, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade')
    
        Result = cerebro.run()
      
        Result_List =[[
            [Temp[0].params.sd_low,Temp[0].params.OVER_SOLD,Temp[0].params.Stop_Loss, Temp[0].params.RSI_Period],
            Temp[0].analyzers.returns.get_analysis()['rnorm'],    
            Temp[0].analyzers.sharpe.get_analysis()['sharperatio'],
            Temp[0].analyzers.dd.get_analysis()['max']['drawdown'],
            Temp[0].analyzers.trade.get_analysis()['total']['total'],
            ] for Temp in Result]
        
        Result_List = pd.DataFrame(Result_List, columns = ['sd_low / OverSold / Stop_Loss','Annual Return','Sharpe Ratio','DrawDown','Total Order'])
       # Result_List = Result_List[Result_List['DrawDown']<10]    #Filtering
       # Result_List = Result_List[Result_List['Sharpe Ratio'] > 3]
        Result_List = Result_List[Result_List['Annual Return']<3000]
        Result_List = Result_List.dropna()
        Result_List.insert(0, 'Pair', symbol+'_'+time_interval)
        Opt_List = Opt_List.append(Result_List)
        print(symbol,' Optimized! No. of Result: ',len(Result_List.index))
        
    winsound.Beep(500,1000)
    Opt_List.sort_values(by=['Annual Return','DrawDown'], ascending=[False,True], inplace=True)
    
    with pd.ExcelWriter(rf'D:/Python/Binance_Python_Project/Opt_Result/BBRSI_{Pair}_Training_Set_{time_interval}_Opt_Summary.xlsx') as writer:
        Opt_List.to_excel(writer, sheet_name = 'Data', index = False)
        Pivot_Table().to_excel(writer, sheet_name = 'Pivot Table')
    