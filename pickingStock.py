import os
import time
import datetime
import pymysql
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
cursor = db.cursor()

def pickingStocks():
  baseDate = str(datetime.datetime.now())[0:10]
  #baseDate = '2021-04-26' 
  print(baseDate)
  cursor.execute("select deal_date from trade_days where '%s'>=deal_date ORDER BY deal_date desc limit 3" % (baseDate))
  threeDays = cursor.fetchall()
  currentDealDate = str(threeDays[0][0])
  yesterDayDealDate = str(threeDays[1][0])
  yesterAfterDayeDealDate = str(threeDays[2][0])
  # 执行三连阳数据
  effectThreeRedRows = cursor.execute("INSERT INTO stock_picking(stock_code, stock_name, create_date, classify) SELECT A.stock_code,A.stock_name,A.deal_date,1 from (SELECT stock_code,stock_name,rize_amplitude,amplitude,deal_date FROM hold_stock_day_info WHERE deal_date = '%s' and (end_price-open_price)>0 and amplitude>4 and high_price>2) A, (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE deal_date = '%s' and (end_price-open_price)>0 and amplitude>3) B, (SELECT stock_code,stock_name FROM hold_stock_day_info WHERE deal_date = '%s' and (end_price-open_price)>0 and amplitude>4 and rize_amplitude<8) C where A.stock_code = B.stock_code AND A.stock_code = C.stock_code AND A.stock_code not like '68%%'  AND  A.stock_code NOT IN(select stock_code from stock_picking where classify=1 AND create_date='%s')" % (currentDealDate,yesterDayDealDate,yesterAfterDayeDealDate,currentDealDate))
  db.commit()
  # 强势股选/票
  effectStrengthenRows = cursor.execute("INSERT INTO stock_picking(stock_code, stock_name, create_date, classify) select stock_code,stock_name,deal_date,2 from hold_stock_day_info where deal_date='%s' and rize_amplitude>9 AND stock_code not like '68%%' AND  stock_code NOT IN( SELECT stock_code from stock_picking where classify=2 AND create_date='%s')" % (currentDealDate,currentDealDate))
  db.commit()
  # 短周期两日回调幅度选票 排除跌停股 回撤幅度大于10
  callbackRows = cursor.execute("INSERT INTO stock_picking(stock_code, stock_name, create_date, classify,description) SELECT A.stock_code,A.stock_name,A.deal_date,4,round(((B.high_price-A.end_price)/A.yesterday_price)*100,2) as 回撤幅度 FROM (SELECT * FROM hold_stock_day_info where deal_date = '%s') A,(SELECT * FROM hold_stock_day_info WHERE deal_date = '%s') B WHERE A.stock_code = B.stock_code AND A.rize_amplitude>-18  AND ((B.high_price-A.end_price)/A.yesterday_price)*100>10 AND A.stock_code not like '68%%' AND A.stock_code NOT IN(SELECT stock_code FROM stock_picking WHERE classify=4 AND create_date='%s' )" % (currentDealDate,yesterDayDealDate,currentDealDate))
  #弱转强选票

  # 十字星选股
  tenStartRows = cursor.execute("INSERT INTO stock_picking(stock_code, stock_name, create_date, classify) select stock_code,stock_name,deal_date,5 from hold_stock_day_info where deal_date='%s' and ((high_price-low_price)/yesterday_price)*100>6 and abs(((end_price-open_price)/yesterday_price)*100)<2 AND stock_code not like '68%%' AND  stock_code NOT IN( SELECT stock_code from stock_picking where classify=5 AND create_date='%s')" % (currentDealDate,currentDealDate))
  db.commit()
  
  #回撤25%的股票
  sevenFiveBackRows = cursor.execute("INSERT INTO stock_picking(stock_code, stock_name, create_date, classify,description) SELECT B.stock_code,B.stock_name,B.deal_date,6,round((B.end_price/A.maxPrice),2) FROM (select max(high_price) as maxPrice,stock_code,stock_name from hold_stock_day_info where deal_date>=(SELECT * FROM (select deal_date from trade_days where deal_date<='%s' ORDER BY deal_date DESC limit 12) A ORDER BY A.deal_date limit 1) GROUP BY  stock_code) A, (select * from hold_stock_day_info WHERE deal_date='%s' and ((stock_code not like '30%%' and rize_amplitude>-9.5) or  (stock_code like '30%%' and rize_amplitude>-13)) )  B where A.stock_code = B.stock_code AND B.low_price/A.maxPrice<0.76 AND B.high_price>2 AND B.stock_code not like '68%%' AND A.stock_code not IN((SELECT stock_code FROM stock_picking WHERE classify=6 AND create_date='%s'))" % (baseDate,currentDealDate,currentDealDate))
  db.commit()
  print("三连阳选: "+str(effectThreeRedRows) +" 强势股:"+str(effectStrengthenRows) +" 十字星:"+str(tenStartRows)+ " 短周期回调:"+str(callbackRows) + " 75回撤选股:"+str(sevenFiveBackRows))
  processLianBanStock(baseDate)

def processLianBanStock(baseDate):
  cursor.execute("SELECT stock_code,stock_name FROM hold_stock_day_info where rize_amplitude>9 and stock_code not like '688%%'  and deal_date='%s' " % (baseDate))
  raisingLimitStockArray = cursor.fetchall()
  cursor.execute("select deal_date from trade_days where deal_date<now() ORDER BY deal_date desc limit 20")
  tradeDaysArray = cursor.fetchall()
  dictData = {}
  for raisingLimit in raisingLimitStockArray:
    stockCode = raisingLimit[0]
    i = 0
    for tradeDays in tradeDaysArray:
      cursor.execute("SELECT stock_code,stock_name,deal_date,rize_amplitude FROM hold_stock_day_info where rize_amplitude>9 and stock_code='%s' and deal_date='%s'" % (stockCode,tradeDays[0]))
      existFlag = cursor.fetchone()
      #print(existFlag)
      if existFlag is None:
        break
      i = i+1
    dictData[stockCode] = i
    cursor.execute("SELECT * FROM stock_picking where create_date='%s' and classify='%s' and stock_code='%s'" % (baseDate,3,stockCode))
    pickingStockExistFlag =  cursor.fetchone()
    if pickingStockExistFlag is None:
      cursor.execute("insert into stock_picking(stock_code, stock_name, create_date, classify, description) VALUES ('%s','%s','%s',3,'%s')" % (stockCode,raisingLimit[1],baseDate,i))
      db.commit()
  #print(dictData)

if __name__ == '__main__':
  pickingStocks()
