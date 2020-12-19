# coding=utf-8
import requests,json
import pymysql
import os,time
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import decimal
from decimal import *
import judgeTrend
from judgeTrend import processJudge
import correct
from correct import processCorrect
import syn
from syn import processSyn
from threading import Thread,Lock
import constant


url="https://dataapi.joinquant.com/apis"

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
#获取调用凭证
body={       
    "method": "get_token",
    "mob": "17611579536",  #mob是申请JQData时所填写的手机号
    "pwd": constant.jqDataPwd,  #Password为聚宽官网登录密码，新申请用户默认为手机号后6位
}
response = requests.post(url, data = json.dumps(body))
token=response.text

cursor = db.cursor()

baseDate = "2020-08-25"
beforeDate = "2020-08-24"

def doJob():
  scheduler = BlockingScheduler()
  #5分钟同步一次
  execute()
  #scheduler.add_job(execute, 'interval', seconds=60, id='job1')
  #scheduler.start()

def processMultyThread(holdStock):
  lock.acquire()
  code = holdStock[1]+'.'+holdStock[2]
  yesterDayPrice =  processDayCompleteInfo(holdStock[1],code,holdStock[0])
  prosessSinbleStockAllInfo(holdStock[1],code,holdStock[0],yesterDayPrice)
  lock.release()

def execute():
  cursor.execute("select * from hold_stock_imitate where stock_code not in(select stock_code from stock_day_base_Info_imitate)")
  holdStockList = cursor.fetchall()
  l = []
  for holdStock in holdStockList:
    p = Thread(target=processMultyThread(holdStock))
    l.append(p)
    p.start()
  for p in l:
    p.join()  

  ########处理预测数据 start#################
  # 如果大于十点 同时趋势为空的时候
  d1 = datetime.datetime.now()
  d2 = datetime.datetime.strptime(baseDate+' 09:40:00','%Y-%m-%d %H:%M:%S')
  if d1>d2:
    processJudge(baseDate+" ")
  
  ########处理预测数据 end##################
  #######处理纠正数据 start #################
  d3 = datetime.datetime.strptime(baseDate+' 10:30:00','%Y-%m-%d %H:%M:%S')
  if d1>d3:
    processCorrect(baseDate+' ')
  #######处理纠正数据 end #################
 
  #===============处理同步数据
  d4 = datetime.datetime.strptime(baseDate+' 15:00:00','%Y-%m-%d %H:%M:%S')  
  if d1>d4:
   processSyn(baseDate)


  ##############计算买点 start########################
  calculatePoint()
  ##############计算买点 end #########################
  #cursor.close()
  #db.close()

def prosessSinbleStockAllInfo(stockCode,code,stockName,yesterDayPrice):
  startDate = baseDate +  " 09:30:00"
  cursor = db.cursor()
  cursor.execute("SELECT date_format(DATE_ADD(max(now_time),INTERVAL 1 MINUTE), '%%Y-%%m-%%d %%H:%%i:%%s') FROM stock_data_imitate WHERE stock_code='%s' " % (stockCode))
  startDateFetch = cursor.fetchone()
  if startDateFetch[0] is None:
     print("============="+stockCode)
  else:
    startDate = startDateFetch[0]
  now = datetime.datetime.now()
  #
  #endDate=baseDate + " 09:41:00"
  endDate  = now.strftime('%Y-%m-%d %H:%M:%S')
  #endDate = baseDate + " 15:00:00"
  body={
      "method": "get_price_period",
      "token": token,
      "code": code,
      "unit": "1m",
      "date": startDate,    
      "end_date": endDate,
      "fq_ref_date": baseDate
    }
  response = requests.post(url, data = json.dumps(body))
  dataArray = response.text.split('\n')
  del dataArray[0]
  insertValues = []
  cursor = db.cursor()
  for data in dataArray:
     print(data)
     smallDataArray = data.split(',')
     nowTime = smallDataArray[0]
     startPrice = smallDataArray[1]
     endPrice = smallDataArray[2]
     currentHighestPrice = smallDataArray[3]
     currentLowestPrice = smallDataArray[4]
     currentLatitude = ((decimal.Decimal(endPrice)-decimal.Decimal(yesterDayPrice))/decimal.Decimal(yesterDayPrice))*100
     insertValues.append((stockCode,nowTime,startPrice,endPrice,currentLowestPrice,currentHighestPrice,yesterDayPrice,currentLatitude,nowTime))

  effectRow = cursor.executemany("INSERT INTO stock_data_imitate (stock_code,now_time,start_price,end_price,lowest_price,highest_price,yesterday_price,current_latitude,create_time) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", insertValues)
  db.commit()

def processDayCompleteInfo(stockCode,code,stockName):
   beforeStartDate = beforeDate + " 09:30:00"
   beforeEndDate = beforeDate + " 15:00:00"
   openStockTime = beforeDate + " 09:31:00"
   body={
      "method": "get_price_period",
      "token": token,
      "code": code,
      "unit": "1d",
      "date": beforeStartDate,
      "end_date": beforeEndDate,
      "fq_ref_date": beforeDate
    }
   cursor.execute("SELECT yesterday_price,start_price  FROM stock_day_base_Info_imitate WHERE stock_code='%s' AND DATE(create_time)='%s'" % (stockCode,baseDate))
   existFlag = cursor.fetchone()
   if existFlag:
      if existFlag[1]:
        return existFlag[0]
      else:
        cursor.execute("update stock_day_base_Info_imitate A ,stock_data B SET A.start_price = B.start_price where A.stock_code='%s' AND  A.stock_code=B.stock_code AND B.now_time='%s' " % (stockCode,openStockTime))
        db.commit()
      return existFlag[0]
   else:
    response = requests.post(url, data = json.dumps(body))
    dataArray = response.text.split('\n')
    yesterDayPrice = response.text[3]
    del dataArray[0]
    if len(dataArray)==0 :
      return
    yesterDayPriceArray = dataArray[0].split(',')
    yesterDayPrice = yesterDayPriceArray[2]
    cursor.execute("INSERT INTO stock_day_base_Info_imitate(stock_code,stock_name,yesterday_price,create_time,update_time) VALUES (%s,%s,%s,%s,now())",(stockCode,stockName,yesterDayPrice,baseDate)) 
    db.commit()
    return yesterDayPrice

def calculatePoint():
  #计算合适买点
  now = datetime.datetime.now()
  nowTime  = now.strftime('%Y-%m-%d %H:%M:%S')
  tenTime = baseDate + " 09:41:00"
  print("计算买点开始**********************"+nowTime+"********************")
  print("#############################合适买点###############################")
  # 计算一分钟前出现的
  beforeOneMinutesTime = (now + datetime.timedelta(minutes=-1)).strftime("%Y-%m-%d %H:%M:%S")
  cursor.execute("SELECT A.stock_code,DATE_FORMAT(B.now_time,'%%h:%%i'),B.current_latitude,trend,A.pre_max_amplitude,A.pre_low_price,B.lowest_price,A.stock_name  FROM stock_day_base_Info_imitate A,stock_data b where A.stock_code=B.stock_code AND B.lowest_price<=A.pre_buy_point AND B.lowest_price>A.pre_low_price AND B.now_time>'%s' AND B.now_time BETWEEN '%s' AND  '%s' ORDER BY A.pre_max_amplitude DESC " % (tenTime,beforeOneMinutesTime,nowTime))
  buyPointDataArray = cursor.fetchall()
  print("code	时间	涨幅	趋势	预振	预低	 最低	名称")
  for buyPoint in buyPointDataArray:
      print("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (buyPoint[0],buyPoint[1],buyPoint[2],buyPoint[3],buyPoint[4],buyPoint[5],buyPoint[6],buyPoint[7]))
  #计算最佳买点
  print("###############################最佳买点#############################")
  cursor.execute("SELECT A.stock_code,DATE_FORMAT(B.now_time,'%%h:%%i'),B.current_latitude,trend,A.pre_max_amplitude,A.pre_low_price,B.lowest_price,A.stock_name FROM stock_day_base_Info_imitate A,stock_data_imitate b where A.stock_code=B.stock_code AND B.lowest_price<=A.pre_low_price AND B.now_time>'%s' AND B.now_time BETWEEN '%s' AND  '%s' ORDER BY A.pre_max_amplitude DESC " % (tenTime,beforeOneMinutesTime,nowTime))
  bestBuyPointArray = cursor.fetchall()
  for buyPoint in bestBuyPointArray:
    print("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (buyPoint[0],buyPoint[1],buyPoint[2],buyPoint[3],buyPoint[4],buyPoint[5],buyPoint[6],buyPoint[7]))
  print("计算买点结束*******************"+nowTime+"***********************")

if __name__ == '__main__':
  lock = Lock()
  doJob()
