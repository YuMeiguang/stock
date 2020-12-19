# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
from dayInfo import execute
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
cursor = db.cursor()

baseDate = "2020-10-23"

def processSyn(baseDate):
  closeTime = baseDate + " 14:59:00"
  cursor.execute("SELECT stock_code,stock_name FROM stock_day_base_info where close_price is null")
  stockList = cursor.fetchall()
  # 如果找不到对应的则不需要同步
  if stockList:
    print("###############同步当天数据开始##############")
    for stock in stockList:
       processSinbleSyn(stock[0],stock[1],baseDate,closeTime)
    print("###############同步当天数据结束##############")
  print("###############同步当天所有股票的涨跌幅数据开始##########")
  execute(baseDate)  
  print("###############同步当天所有股票的涨跌幅数据结束##########")
  print("###############插入当天强势股 开始##########")
  insertAllStrengthenStock(baseDate)
  print("###############插入当天强势股 结束##########")
  #cursor.close()
  #db.close()

def insertAllStrengthenStock(baseDate):
  cursor.execute("SELECT stock_code FROM hold_stock_day_info where deal_date='%s'  and rize_amplitude>11 and stock_code not in (SELECT  stock_code FROM hold_stock)" %(baseDate))
  allStock=cursor.fetchall()
  for stockInfo in allStock:
    if stockInfo[0][0:2]=='68':
      print(stockInfo[0]+"不满足")
      pass
    else:
      cursor.execute("INSERT INTO hold_stock (stock_name, stock_code, create_time, update_time) SELECT stock_name,stock_code,now(), now() FROM all_stock WHERE stock_code='%s' " %(stockInfo))
  db.commit()
  cursor.execute("update hold_stock set stock_name='未知' where stock_name is null")
  db.commit()
  
def processSinbleSyn(code,name,baseDate,closeTime): 
  #judge range  3+ or 2.5+
  cursor.execute("SELECT * FROM stock_day_base_info WHERE stock_code='%s' AND DATE(create_time)='%s'" % (code,baseDate))
  baseInfo = cursor.fetchone()
  yesterDayPrice = baseInfo[2]
  cursor.execute("SELECT min(lowest_price) FROM stock_data WHERE stock_code ='%s'  AND DATE(now_time)='%s'" % (code,baseDate))
  minPrice = cursor.fetchone()[0]
  cursor.execute("SELECT max(highest_price) FROM stock_data WHERE stock_code = '%s'  AND DATE(now_time)= '%s' " % (code,baseDate))
  maxPrice = cursor.fetchone()[0]
  cursor.execute("SELECT end_price from stock_data where stock_code='%s' AND now_time='%s' AND DATE(create_time)='%s' " % (code,closeTime,baseDate))
  endPriceFetch = cursor.fetchone()
  if endPriceFetch:
     endPrice = endPriceFetch[0]
  else:
     return
  amplitude = round(((maxPrice-minPrice)/yesterDayPrice)*100,2)
  cursor.execute("UPDATE stock_day_base_info SET low_price='%s',high_price='%s',real_amplitude='%s',close_price='%s',update_time=now() where stock_code='%s' AND DATE(create_time)='%s'" % (minPrice,maxPrice,amplitude,endPrice,code,baseDate))
  db.commit()
  # 更新持股基本信息
  cursor.execute("UPDATE hold_stock SET now_price='%s',yesterday_close_price='%s',update_time=now() where stock_code='%s' " % (endPrice,yesterDayPrice,code))
  db.commit()


  
  

if __name__ == '__main__':
  processSyn(baseDate)
