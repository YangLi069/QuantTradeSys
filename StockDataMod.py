# 实现数据获取和基础数据的处理
import os
import datetime
import numpy as np
import pandas as pd
import pandas_datareader.data as web
import fix_yahoo_finance as yf
yf.pdr_override()
import talib


# 获取股票数据接口
def GetStockDatApi(stockName=None, stockTimeS=None, stockTimeE=None):
    path = "C:/Users/Lenovo/workspace_python/QuantTradeSys/StockData"
    # stockTimeS/stockTimeE为datetime格式，需要转换为string
    str_stockTimeS = stockTimeS.strftime('%Y-%m-%d')
    str_stockTimeE = stockTimeE.strftime('%Y-%m-%d')
    newname = stockName + '+' + str_stockTimeS + '+' + str_stockTimeE + '.csv'
    newpath = os.path.join(path, newname)

    print(u'当前工作目录:%s' % os.getcwd())
    os.chdir(path)
    print(u'工作目录修改为:%s' % os.getcwd())

    for filename in os.listdir(path):

        if stockName in filename:
            if filename.count('+') == 2:
                # 分割文件名的起止日期，并转化为datetime
                str_dfLoadTimeS = filename.split('+')[1]
                str_dfLoadTimeE = filename.split('+')[2].split('.')[0]

                dtm_dfLoadTimeS = datetime.datetime.strptime(str_dfLoadTimeS, '%Y-%m-%d')
                dtm_dfLoadTimeE = datetime.datetime.strptime(str_dfLoadTimeE, '%Y-%m-%d')

                if ((dtm_dfLoadTimeS - stockTimeS).days <= 0) and ((dtm_dfLoadTimeE - stockTimeE).days >= 0):
                    print("123", (dtm_dfLoadTimeS - stockTimeS).days)
                    print("345", (dtm_dfLoadTimeE - stockTimeE).days)
                    stockDat = pd.read_csv(os.path.join(path, filename),
                                           parse_dates=True, index_col=0,
                                           encoding='gb2312')
                    # print(stockDat.head(), stockDat.tail())
                    stockDat = stockDat.loc[str_stockTimeS:str_stockTimeE]
                    # print(stockDat.head(), stockDat.tail())
                else:
                    # 起止日期不同，重新下载
                    #stockDat = web.DataReader(stockName, 'yahoo', stockTimeS, stockTimeE)
                    stockDat = web.get_data_yahoo(stockName, stockTimeS, stockTimeE)
                    os.rename(filename, newname)
                    stockDat.to_csv(newpath, columns=stockDat.columns, index=True)
                return stockDat
            else:
                break

    #stockDat = web.DataReader(stockName, 'yahoo', stockTimeS, stockTimeE)
    stockDat = web.get_data_yahoo(stockName, stockTimeS, stockTimeE)
    stockDat.to_csv(newpath, columns=stockDat.columns, index=True)

    return stockDat


# 处理股票数据接口
def GetStockDatPro(stockName=None, stockTimeS=None, stockTimeE=None):
    stockPro = GetStockDatApi(stockName, stockTimeS, stockTimeE)

    # 处理移动平均线
    stockPro['Ma20'] = stockPro.Close.rolling(window=20).mean()
    stockPro['Ma60'] = stockPro.Close.rolling(window=60).mean()
    stockPro['Ma120'] = stockPro.Close.rolling(window=120).mean()

    # MACD
    stockPro['macd_dif'], stockPro['macd_dea'], stockPro['macd_bar'] = \
        talib.MACD(stockPro['Close'].values, fastperiod=12, slowperiod=26, signalperiod=9)

    # KDJ
    xd = 9 - 1
    date = stockPro.index.to_series()
    RSV = pd.Series(np.zeros(len(date) - xd), index=date.index[xd:])
    Kvalue = pd.Series(0.0, index=RSV.index)
    Dvalue = pd.Series(0.0, index=RSV.index)
    Kvalue[0] = 50
    Dvalue[0] = 50

    for day_ind in range(xd, len(date)):
        RSV[date[day_ind]] = (stockPro.Close[day_ind] - stockPro.Low[day_ind - xd:day_ind + 1].min()) \
                             / (stockPro.High[day_ind - xd:day_ind + 1].max()
                                - stockPro.Low[day_ind - xd:day_ind + 1].min()) * 100
        if day_ind > xd:
            index = day_ind - xd
            Kvalue[index] = 2.0 / 3 * Kvalue[index - 1] + RSV[date[day_ind]] / 3
            Dvalue[index] = 2.0 / 3 * Dvalue[index - 1] + Kvalue[index] / 3

    stockPro['RSV'] = RSV
    stockPro['K'] = Kvalue
    stockPro['D'] = Dvalue
    stockPro['J'] = 3 * Kvalue - 2 * Dvalue

    return stockPro
