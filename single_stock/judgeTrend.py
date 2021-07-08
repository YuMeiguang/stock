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


def processJudge():
  processSinbleJudge('300598')
  cursor.close()
  db.close()

def processSinbleJudge(code):
  flag = 0
  startTime = baseDate + "09:30"
  endTime = baseDate + "10:00"
  openTime = baseDate + "09:31"
   
  #judge range  3+ or 2.5+
  cursor.execute("SELECT * FROM stock_day_base_Info_single WHERE stock_code='%s' AND DATE(create_time)='%s'" % (code,baseDate))
  baseInfo = cursor.fetchone()
  print(baseInfo)
  yesterDayPrice = baseInfo[2]
  cursor.execute("SELECT start_price FROM stock_data_single WHERE stock_code ='%s'  AND now_time = '%s'" % (code,openTime))
  startPrice = cursor.fetchone()[0] 
  cursor.execute("SELECT min(lowest_price) FROM stock_data_single WHERE stock_code ='%s'  AND now_time BETWEEN '%s' AND '%s'" % (code,startTime,endTime))
  minPrice = cursor.fetchone()
  cursor.execute("SELECT max(highest_price) FROM stock_data_single WHERE stock_code = '%s'  AND now_time BETWEEN '%s' AND '%s' " % (code,startTime,endTime))
  maxPrice = cursor.fetchone()
  amplitude = round(((maxPrice[0]-minPrice[0])/yesterDayPrice)*100,2)
  # 小于2.5 不考虑 .5-3 系数为2   3-4 系数为1.8  
  cursor.execute("SELECT count(*) FROM stock_data_single WHERE stock_code = '%s'  AND now_time BETWEEN '%s' AND '%s' AND start_price<=end_price" % (code,startTime,endTime))
  riseNum = cursor.fetchone()[0]
  #偏离中心值  也就是减去15 如果得数 0-1 为3 1-3 为5  3-4 为6  4+ 为8
  riseNum = abs(riseNum - 15)
  #振幅计算
  # 1.系数获取  RANGE 振幅范围系数  
  cursor.execute("SELECT * FROM level_ratio WHERE ratio_type='%s' AND min_param<='%s' AND max_param>='%s'" % ('RANGE',amplitude,amplitude))
  rangeRatio = cursor.fetchone()
  # 1.2 RISE_NUM 数量偏差系数
  cursor.execute("SELECT * FROM level_ratio WHERE ratio_type='%s' AND min_param<='%s' AND max_param>='%s'" % ('RISE_NUM',riseNum,riseNum))
  riseNumRatio = cursor.fetchone()
  print(code)
  preMaxAmplitude = (Decimal(str(0.7))*amplitude*rangeRatio[4]) + (Decimal(str(0.3))*riseNumRatio[4])
  #趋势判断  1.最大价格时间大于最小值时间  2.10点重的5分钟均值 大于看5分钟均值
  cursor.execute("SELECT (SELECT now_time FROM stock_data_single WHERE stock_code = '%s'  AND now_time BETWEEN '%s' AND '%s' AND highest_price='%s' order by now_time limit 1) >= (SELECT now_time FROM stock_data_single WHERE stock_code = '%s'  AND now_time BETWEEN '%s' AND '%s' AND lowest_price='%s' order by now_time limit 1) " % (code,startTime,endTime,maxPrice[0],code,startTime,endTime,minPrice[0]))
  trendFlag = cursor.fetchone()
  preLowPrice = 0
  preHighPrice = 0
  preBuyPoint = 0
  preSellPoint =  0
  if trendFlag[0] == 1: 
    trendFlag = 1
    preLowPrice = minPrice[0]
    preHighPrice = yesterDayPrice*preMaxAmplitude/100 + preLowPrice
    riseStop = yesterDayPrice*decimal.Decimal('1.1')
    if (preHighPrice - riseStop)>0:
      preHighPrice = riseStop
      preMaxAmplitude =  ((preHighPrice-preLowPrice)/yesterDayPrice)*100
    preSellPoint = (minPrice[0]+(yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.9'))
    preBuyPoint = minPrice[0]+(yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.25')
  else:
   trendFlag = -1
   preHighPrice = maxPrice[0]
   preLowPrice = preHighPrice -  yesterDayPrice*preMaxAmplitude/100
   fallStop = yesterDayPrice*decimal.Decimal('0.9')
   if (fallStop-preLowPrice)>0:
     preLowPrice = fallStop
     #根据振幅确定系数
     preMaxAmplitude = ((preHighPrice-preLowPrice)/yesterDayPrice)*100
   preSellPoint = preHighPrice - ((yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.25'))
   preBuyPoint = preHighPrice - ((yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.9'))
  effectRow = cursor.execute("UPDATE stock_day_base_Info_single set start_price='%s', pre_max_amplitude='%s',pre_low_price='%s',pre_high_price='%s',pre_sell_point='%s',pre_buy_point='%s', trend='%s',amplitude='%s', update_time=now() WHERE stock_code='%s' AND DATE(create_time)='%s' " % (startPrice,preMaxAmplitude,preLowPrice,preHighPrice,preSellPoint,preBuyPoint,trendFlag,amplitude,code,baseDate))
  db.commit() 
   



  
  

if __name__ == '__main__':
  processJudge()
