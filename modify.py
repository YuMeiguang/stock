# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

cursor = db.cursor()

baseDate = "2020-04-24 "

# 趋势翻转以及买点卖点调整  翻转后幅度是否要调整

def processJudge():
  cursor.execute("SELECT * FROM hold_stock ")
  holdStockList = cursor.fetchall()
  for holdStock in holdStockList:
     processSinbleJudge(holdStock[1])
  cursor.close()
  db.close()

def processSinbleJudge(code):
  flag = 0
  startTime = baseDate + "09:30"
  endTime = baseDate + "10:30"
  openTime = baseDate + "09:31"
   
  #judge range  3+ or 2.5+
  cursor.execute("SELECT * FROM stock_day_base_info WHERE stock_code='%s' AND DATE(create_time)='%s'" % (code,baseDate))
  baseInfo = cursor.fetchone()
  yesterDayPrice = baseInfo[2]
  cursor.execute("SELECT start_price FROM stock_data WHERE stock_code ='%s'  AND now_time = '%s'" % (code,openTime))
  startPrice = cursor.fetchone()[0] 
  cursor.execute("SELECT min(lowest_price) FROM stock_data WHERE stock_code ='%s'  AND now_time BETWEEN '%s' AND '%s'" % (code,startTime,endTime))
  minPrice = cursor.fetchone()
  cursor.execute("SELECT max(highest_price) FROM stock_data WHERE stock_code = '%s'  AND now_time BETWEEN '%s' AND '%s' " % (code,startTime,endTime))
  maxPrice = cursor.fetchone()
  #TODO 是否翻转 如果翻转 如何模拟
  amplitude = round(((maxPrice[0]-minPrice[0])/yesterDayPrice)*100,2)
  preMaxAmplitude = baseInfo[4]
  cursor.execute("SELECT * FROM stock_day_base_info WHERE stock_code='%s' AND pre_max_amplitude <= 7 AND abs(pre_max_amplitude-'%s')> 1.5" % (code,amplitude))
  existFlag = cursor.fetchone()
  if existFlag:
     preMaxAmplitude = amplitude
  else:
    return
  preLowPrice = minPrice[0]
  preHighPrice = maxPrice[0]
  modifyFlag = 1
  #TODO 振幅为 3 4 5 6 7  根据系数来决定
  preSellPoint = 0
  #纠正涨停的bug
  dailyLimit = False
  if minPrice[0] == maxPrice[0] and ((minPrice[0]-yesterDayPrice)/yesterDayPrice)*100>9:
    dailyLimit = True
    preMaxAmplitude = 0
  preBuyPoint = 0
  if dailyLimit:
    preSellPoint = preHighPrice
    preBuyPoint = preHighPrice
  elif baseInfo[3] == 1 :
     preSellPoint = preLowPrice + (preMaxAmplitude*yesterDayPrice/100)*decimal.Decimal('0.9')
     preBuyPoint = preLowPrice + (preMaxAmplitude*yesterDayPrice/100)*decimal.Decimal('0.3')
  else:
    preSellPoint = preHighPrice - (preMaxAmplitude*yesterDayPrice/100)*decimal.Decimal('0.2')
    preBuyPoint = preHighPrice - (preMaxAmplitude*yesterDayPrice/100)*decimal.Decimal('0.8')
  cursor.execute("UPDATE stock_day_base_info SET pre_high_price='%s',pre_low_price='%s',pre_buy_point='%s',pre_sell_point='%s',modify_flag='%s',modify_time='%s',update_time=now() where stock_code='%s' AND DATE(create_time)='%s'" % (preHighPrice,preLowPrice,preBuyPoint,preSellPoint,modifyFlag,endTime,code,baseDate))
  db.commit()
  

if __name__ == '__main__':
  processJudge()
