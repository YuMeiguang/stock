# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
import constant


db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

cursor = db.cursor()

def downThree(baseDate,beforeDate):
  closeTime = baseDate + " 14:59:00"
  cursor.execute("SELECT stock_code,stock_name FROM stock_day_base_info where close_price is null")
  stockList = cursor.fetchall()
  # 如果没有数据则无需同步
  if not stockList:
    return;
  print("###############同步当天数据开始##############")
  for stock in stockList:
     processSinbleSyn(stock[0],stock[1],baseDate,closeTime)
  print("###############同步当天数据结束##############")
  #cursor.close()
  #db.close()

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
