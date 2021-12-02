import backtrader as bt
import Strategy
import matplotlib
import pandas as pd
import pyfolio as pf
import winsound
from sklearn.model_selection import train_test_split
pd.set_option('display.width',10000)
pd.set_option('display.max_columns',14)
Pairs = ['BNBUSDT','BTCUSDT','ETHUSDT', 'FILUSDT','TRXUSDT','UNIUSDT','LTCUSDT','XRPUSDT']
Pair = ['ETHUSDT']
time_interval = '1Min_30Days'
Backtest_List = pd.DataFrame(data=None,columns = ['Pair','sd_low / OverSold / Stop_Loss','Annual Return','Sharpe Ratio','DrawDown','Total Order','Win Rate'])

def Pivot_Table():
    Backtest_List['sd_low / OverSold / Stop_Loss'] = Backtest_List['sd_low / OverSold / Stop_Loss'].astype(str)
    Backtest_List['Total Order'] = Backtest_List['Total Order'].astype(int)
    pt = pd.pivot_table(Backtest_List, index=['sd_low / OverSold / Stop_Loss'],
                        aggfunc = {'Pair':'count',
                                   'Annual Return':'mean',
                                   'Sharpe Ratio':'mean',
                                   'DrawDown':'mean',
                                   'Total Order':'mean',
                                   'Win Rate':'mean'})   
    pt = pt[pt.Pair>=7]
    pt = pt.dropna()
    pt.sort_values(by=['Annual Return','DrawDown'],ascending = [False,True],inplace=True)
    return pt

for symbol in  Pairs:
    #matplotlib.use('Qt5Agg')
    Dataset = pd.read_csv(rf'D:/Python/Binance_Python_Project/Future Data/{time_interval}/{symbol}.csv',parse_dates=True, index_col=0)
    train, test = train_test_split(Dataset, test_size=0.4, shuffle=False)
    cerebro = bt.Cerebro()
    cerebro.broker.setcommission(commission=0.0002)
    data = bt.feeds.PandasData(dataname = test,
                               timeframe=bt.TimeFrame.TFrame("Minutes"),
                               compression=1,
                               openinterest=-1)   

    cerebro.adddata(data)
    cerebro.addstrategy(Strategy.BBRSI, sd_low=2.0, OVER_SOLD=27, Stop_Loss=3.5, ATR_Period=14, RSI_Period=14)
    #cerebro.addstrategy(Strategy.BBRSI_Long_Short)
    
    cerebro.broker.set_cash(1000000)
    cerebro.addsizer(bt.sizers.PercentSizer, percents = 99)
   # cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, timeframe=bt.TimeFrame.Days, annualize=True, riskfreerate=0, factor = 365, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='dd')
    cerebro.addanalyzer(bt.analyzers.Returns,timeframe=bt.TimeFrame.Days, tann = 365, _name='returns')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade')

    print(symbol)
    print('Start Portfolio Value: %.2f' % cerebro.broker.getvalue())
    Result = cerebro.run()    
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    Result_List = pd.DataFrame([[
        [Temp.params.sd_low,Temp.params.OVER_SOLD,Temp.params.Stop_Loss],
        Temp.analyzers.returns.get_analysis()['rnorm'],    
        Temp.analyzers.sharpe.get_analysis()['sharperatio'],
        Temp.analyzers.dd.get_analysis()['max']['drawdown'],
        Temp.analyzers.trade.get_analysis()['total']['total'],
        Temp.analyzers.trade.get_analysis()['won']['total'] / Temp.analyzers.trade.get_analysis()['total']['total']
        ] for Temp in Result], columns = ['sd_low / OverSold / Stop_Loss','Annual Return','Sharpe Ratio','DrawDown','Total Order','Win Rate'])

    Result_List.insert(0, 'Pair', symbol+'_'+time_interval)
    Backtest_List = Backtest_List.append(Result_List)

Backtest_List.sort_values(by=['Annual Return','DrawDown'], ascending=[False,True], inplace=True)
print(Backtest_List)
# cerebro.plot(style='candle',iplot= False, volume=True)
winsound.Beep(500,500)

with pd.ExcelWriter(rf'D:/Python/Binance_Python_Project/Opt_Result/Backtest/BBRSI_{Pair}_TestSet_{time_interval}_Backtest_Summary.xlsx') as writer:
        Pivot_Table().to_excel(writer, sheet_name = 'Pivot Table')
        Backtest_List.to_excel(writer, sheet_name = 'Data', index = False)
        
    #pyfoliozer = Result[0].analyzers.getbyname('pyfolio')
    #returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    #pf.create_full_tear_sheet(returns,positions=positions,transactions=transactions,round_trips=False)

