# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
cursor = db.cursor()

baseDate = "2020-04-17 "
#baseDate = "2020-04-24 "

closeTime = baseDate + "14:59:00"

def processJudge():
  processSinbleJudge('300598')
  cursor.close()
  db.close()

def processSinbleJudge(code):
   
  #judge range  3+ or 2.5+
  cursor.execute("SELECT * FROM stock_day_base_Info_single WHERE stock_code='%s' AND DATE(create_time)='%s'" % (code,baseDate))
  baseInfo = cursor.fetchone()
  yesterDayPrice = baseInfo[2]
  cursor.execute("SELECT min(lowest_price) FROM stock_data_single WHERE stock_code ='%s'  AND DATE(now_time)='%s'" % (code,baseDate))
  minPrice = cursor.fetchone()[0]
  cursor.execute("SELECT max(highest_price) FROM stock_data_single WHERE stock_code = '%s'  AND DATE(now_time)= '%s' " % (code,baseDate))
  maxPrice = cursor.fetchone()[0]
  print(code)
  cursor.execute("SELECT end_price from stock_data_single where stock_code='%s' AND now_time='%s' AND DATE(create_time)='%s' " % (code,closeTime,baseDate))
  endPrice = cursor.fetchone()[0]
  #TODO 是否翻转 如果翻转 如何模拟
  amplitude = round(((maxPrice-minPrice)/yesterDayPrice)*100,2)
  cursor.execute("UPDATE stock_day_base_Info_single SET low_price='%s',high_price='%s',real_amplitude='%s',close_price='%s',update_time=now() where stock_code='%s' AND DATE(create_time)='%s'" % (minPrice,maxPrice,amplitude,endPrice,code,baseDate))
  db.commit()


  
  

if __name__ == '__main__':
  processJudge()
