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

# 趋势翻转以及买点卖点调整  翻转后幅度是否要调整

def processJudge():
  cursor.execute("SELECT stock_code,stock_name,yesterday_price FROM stock_day_base_Info_single ")
  baseInfoList = cursor.fetchall()
  for baseInfo in baseInfoList:
     correntProcess(baseInfo[0],baseInfo[1],baseInfo[2])
  cursor.close()
  db.close()

def correntProcess(code,stockName,yesterDayPrice):
  ############ 计算开始
  startTime1 = baseDate + "09:30";
  startTime2 = baseDate + "10:00";
  endTime1 = baseDate + "10:01";
  endTime2 = baseDate + "10:30";
  #十点前最高
  cursor.execute("SELECT max(highest_price) FROM stock_data_single WHERE stock_code='%s' AND now_time between '%s' and '%s' " % (code,startTime1,endTime1))
  highestPrice1 = cursor.fetchone()[0]
  #十点前最低
  cursor.execute("SELECT min(lowest_price) FROM stock_data_single WHERE stock_code='%s' AND now_time between '%s' and '%s' " % (code,startTime1,endTime1))
  lowestPrice1 = cursor.fetchone()[0]
  #十点到十点半前最高
  cursor.execute("SELECT max(highest_price) FROM stock_data_single WHERE stock_code='%s' AND now_time between '%s' and '%s' " % (code,startTime2,endTime2))
  highestPrice2 = cursor.fetchone()[0]
  #十点到十点半前最低
  cursor.execute("SELECT min(lowest_price) FROM stock_data_single WHERE stock_code='%s' AND now_time between '%s' and '%s' " % (code,startTime2,endTime2))
  lowestPrice2 = cursor.fetchone()[0]
  ############  计算结束
  

  #############趋势修正 开始######################  
  cursor.execute("SELECT yesterday_price,trend FROM stock_day_base_Info_single WHERE stock_code='%s' AND DATE(create_time)='%s'" % (code,baseDate))
  baseInfo = cursor.fetchone()
  yesterDayPrice = baseInfo[0]
  trend = baseInfo[1]
  pointNum = 0
  #趋势上涨逆转为向下趋势
  cursor.execute("SELECT count(*) FROM stock_data_single WHERE stock_code='%s' AND (end_price<=start_price)=1 AND now_time BETWEEN '%s' AND '%s'" % (code,startTime2,endTime2))
  fallNum = cursor.fetchone()[0]
  #这里处理极限值 避免失误
  downTrendModifyFlag = (trend==1 and (highestPrice2<=highestPrice1) and (lowestPrice2<=lowestPrice1 or fallNum>=15 ))
  if downTrendModifyFlag:
    pointNum = fallNum
  #趋势下跌逆转为向上趋势
  cursor.execute("SELECT count(*) FROM stock_data_single WHERE stock_code='%s' AND (end_price>=start_price)=1 AND now_time BETWEEN '%s' AND '%s'" % (code,startTime2,endTime2))
  #结束价格大于开始价格的点数要大于15
  riseNum = cursor.fetchone()[0]
  riseTrendModifyFlag = (trend==-1 and  (lowestPrice2>=lowestPrice1) and (highestPrice2>=highestPrice1 or riseNum>=15))
  print(stockName)
  print(yesterDayPrice)
  print(riseNum)
  if riseTrendModifyFlag:
    pointNum = riseNum
  ##逆转后买点和卖点计算
  if downTrendModifyFlag or riseTrendModifyFlag:
    newTrend = -(trend)
    processReverseBuyAndSell(code,newTrend,min(lowestPrice1,lowestPrice2),max(highestPrice1,highestPrice2),pointNum,yesterDayPrice)
  
  #############趋势修正 结束######################

#TODO 散点数不同对应的下跌买卖点系数不一样
def processReverseBuyAndSell(code,newTrend,lowestPrice,highestPrice,pointNum,yesterDayPrice):
  print(code)
  amplitude = round(((highestPrice - lowestPrice)/yesterDayPrice)*100,2)
  cursor.execute("SELECT * FROM level_ratio WHERE ratio_type='%s' AND min_param<='%s' AND max_param>='%s'" % ('RANGE',amplitude,amplitude))
  rangeRatio = cursor.fetchone()
  # 1.2 RISE_NUM 数量偏差系数
  cursor.execute("SELECT * FROM level_ratio WHERE ratio_type='%s' AND min_param<='%s' AND max_param>='%s'" % ('RISE_NUM',pointNum,pointNum)) 
  riseNumRatio = cursor.fetchone()
  preMaxAmplitude = (Decimal(str(0.7))*amplitude*rangeRatio[4]) + (Decimal(str(0.3))*riseNumRatio[4])
  preLowPrice = 0
  preHighPrice = 0
  preBuyPoint = 0
  preSellPoint =  0
  print(yesterDayPrice)
  print(newTrend) 
  if newTrend == 1:
    preLowPrice = lowestPrice
    preHighPrice = yesterDayPrice*preMaxAmplitude/100 + preLowPrice
    riseStop = yesterDayPrice*decimal.Decimal('1.1')
    if (preHighPrice - riseStop)>0:
      preHighPrice = riseStop
      preMaxAmplitude =  ((preHighPrice-preLowPrice)/yesterDayPrice)*100
    preSellPoint = (lowestPrice+(yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.9'))
    preBuyPoint = lowestPrice+(yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.25')
  else:
   preHighPrice = highestPrice
   preLowPrice = preHighPrice -  yesterDayPrice*preMaxAmplitude/100
   fallStop = yesterDayPrice*decimal.Decimal('0.9')
   #TODO这里要四舍五入 比如 9.13*0.9=8.219 实际是8.22
   if (fallStop-preLowPrice)>0:
     preLowPrice = fallStop
     #根据振幅确定系数
     preMaxAmplitude = ((preHighPrice-preLowPrice)/yesterDayPrice)*100
   preSellPoint = preHighPrice - ((yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.25'))
   preBuyPoint = preHighPrice - ((yesterDayPrice*preMaxAmplitude/100)*decimal.Decimal('0.9'))
  effectRow = cursor.execute("UPDATE stock_day_base_Info_single set  pre_max_amplitude='%s',pre_low_price='%s',pre_high_price='%s',pre_sell_point='%s',pre_buy_point='%s', trend='%s',amplitude='%s', update_time=now(),modify_flag=1,modify_time=now() WHERE stock_code='%s' AND DATE(create_time)='%s'" % (preMaxAmplitude,preLowPrice,preHighPrice,preSellPoint,preBuyPoint,newTrend,amplitude,code,baseDate))
  db.commit()


if __name__ == '__main__':
  processJudge()
