# coding=utf-8
import requests,json
import pymysql
import time
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
import decimal
from decimal import *
import judgeTrend
from judgeTrend import processJudge
import correct
from correct import processCorrect
from getAllStock import synNewStock
from clean import cleanData
import syn
from smsSend import smsVerifySend
from pickingStock import pickingStocks
from syn import processSyn
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import math
import constant
import redis

#文档
#https://dataapi.joinquant.com/docs

url="https://dataapi.joinquant.com/apis"

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

r = redis.Redis(host=constant.redisHost,port=constant.redisPort,password=constant.redisPassword,db=0,decode_responses=True)
#获取调用凭证
body={       
    "method": "get_token",
    "mob": "17611579536",  
    "pwd": constant.jqDataPwd,  
}

response = requests.post(url, data = json.dumps(body))
token=response.text

cursor = db.cursor()

baseDate=''
beforeDate = ''

def doJob():
  logging.basicConfig(level=logging.INFO, filename='index.html',filemode='a',format=' %(message)s<br>')
  if constant.exeSwitch:
    scheduler = BlockingScheduler()
    scheduler.add_job(execute, 'cron',hour='0-22',minute='*/1', id='job1')
    #清理数据 九点清理数据
    #scheduler.add_job(cleanData, 'cron',hour=9,minute=1,id='job2')
    #scheduler.add_job(processCorrect, 'cron',hour=00,minute=58,id='job3')
    # 开始选股
    scheduler.add_job(pickingStocks, 'cron',hour='15-20',minute='*/30',id='job4')
    # 同步最新发布的股票同时插入到最新的股票
    scheduler.add_job(synNewStock, 'cron', hour=23,minute=1,id='job5')
    scheduler.start()
  else:
    execute()
  

def execute():  
  #自动获取时间
  cursor.execute("select deal_date from trade_days where DATE(now())>=deal_date ORDER BY deal_date desc limit 2")
  dealDataArray = cursor.fetchall()
  global baseDate
  baseDate = str(dealDataArray[0][0])
  #baseDate = '2020-12-03'
  global beforeDate
  #beforeDate = '2020-12-02'
  beforeDate = str(dealDataArray[1][0])
  
  cursor.execute("select count(*) from hold_stock  ")
  #math.ceil 向上取整 math.floor 向下取整
  threadNum = math.ceil(cursor.fetchone()[0]/50)
  with ThreadPoolExecutor(max_workers=threadNum) as t:
    obj_list = []
    begin = time.time()
    for num in range(1,threadNum+1):
      obj = t.submit(processSingleExecute, num)
      obj_list.append(obj)
      for future in as_completed(obj_list):
        data = future.result()
      times = time.time() - begin
  processBuyAndSell(baseDate)
  #db.close()

def processSingleExecute(num):
  startNum = (num-1)*50
  cursor.execute("select stock_code,stock_name,note,hold_flag  from hold_stock order by stock_code desc limit %d,50" % (startNum))
  holdStockList = cursor.fetchall()
  for holdStock in holdStockList:
    stockCode = holdStock[0]
    if stockCode[0:2] == '00':
      code = stockCode + '.XSHE'
    else:
      code = stockCode + '.XSHG'
    yesterDayPrice =  processDayCompleteInfo(stockCode,code,holdStock[1],holdStock[2],holdStock[3])
    prosessSinbleStockAllInfo(stockCode,code,holdStock[1],yesterDayPrice)

def processBuyAndSell(baseDate):
  d1 = datetime.datetime.now()
  ########处理预测数据 start#################
  # 如果大于十点 同时趋势为空的时候
  d2 = datetime.datetime.strptime(baseDate+' 09:40:00','%Y-%m-%d %H:%M:%S')
  if d1>d2:
    processJudge(baseDate+" ")
  
  ########处理预测数据 end##################
 
  #===============处理同步数据
  d4 = datetime.datetime.strptime(baseDate+' 15:00:00','%Y-%m-%d %H:%M:%S')  
  if d1>d4:
   processSyn(baseDate)

  ###########处理买入数据开盘急跌start############
  d5 = datetime.datetime.strptime(baseDate+' 10:00:00','%Y-%m-%d %H:%M:%S')
  if d5>=d1:
    #获得当前分钟
    nowTime = str(d1)[0:17]+"00"
    processDownThree(nowTime)
  ############处理开盘急跌 end #################
  ############开盘急涨 start #################
  d6 = datetime.datetime.strptime(baseDate+' 10:10:00','%Y-%m-%d %H:%M:%S')
  if d6>=d1:
    nowTime = str(d1)[0:17]+"00"
    processRiseThree(nowTime)
  d7 = datetime.datetime.strptime(baseDate+' 09:42:00','%Y-%m-%d %H:%M:%S')
  
  if d7>=d1:
    #TODO 不能每分钟都发 每两分钟发一次
    nowTime = str(d1)[0:17]+"00"
    processLowerest(nowTime)
  ############开盘急涨 end #################


def prosessSinbleStockAllInfo(stockCode,code,stockName,yesterDayPrice):
  startDate = baseDate +  " 09:30:00"
  cursor = db.cursor()
  cursor.execute("SELECT date_format(DATE_ADD(max(now_time),INTERVAL 1 MINUTE), '%%Y-%%m-%%d %%H:%%i:%%s') FROM stock_data WHERE stock_code='%s' " % (stockCode))
  startDateFetch = cursor.fetchone()
  if startDateFetch[0] is not None:
     startDate = startDateFetch[0]
  now = datetime.datetime.now()
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
  for data in dataArray:
     smallDataArray = data.split(',')
     nowTime = smallDataArray[0]
     startPrice = smallDataArray[1]
     endPrice = smallDataArray[2]
     currentHighestPrice = smallDataArray[3]
     currentLowestPrice = smallDataArray[4]
     cursor = db.cursor()
     cursor.execute("SELECT (start_price+end_price+lowest_price+highest_price)/4 as price,rise_point,down_point FROM stock_data WHERE stock_code ='%s' order by now_time desc limit 1" % (stockCode))
     preMinuteAveregePriceFetchOne = cursor.fetchone()
     if preMinuteAveregePriceFetchOne:
       preMinuteAveregePrice = preMinuteAveregePriceFetchOne[0]
       nowAveregePrice = (float(startPrice)+float(endPrice)+float(currentHighestPrice)+float(currentLowestPrice))/4
       currentAmplitude = ((nowAveregePrice-float(preMinuteAveregePrice))/float(yesterDayPrice))*100
       risePoint = preMinuteAveregePriceFetchOne[1]
       downPoint = preMinuteAveregePriceFetchOne[2]
     else:
       currentAmplitude = ((float(endPrice) - float(startPrice))/float(yesterDayPrice))*100
       risePoint = 0
       downPoint = 0
     currentLatitude = ((decimal.Decimal(endPrice)-decimal.Decimal(yesterDayPrice))/decimal.Decimal(yesterDayPrice))*100
     cursor.execute("SELECT ((max(highest_price)-%s)/yesterday_price)*100>13 as flag FROM stock_data where stock_code='%s'" % (currentLowestPrice,stockCode))
     flag = cursor.fetchone() 
     #达到位置0.75短信通知
     sevenFiveProcess(stockCode,currentLowestPrice,nowTime)
     if flag:
        if flag[0] == 1:
           smsVerifySend(stockCode,nowTime,baseDate)
           logging.info("买入 stockName="+stockName+" code="+stockCode+" 时间="+nowTime+" 当前低位"+str(round(currentLatitude,2))+"两点半后慎重考虑")
     if currentLatitude <= -6:
       logging.info("买入参考 name="+stockName+" code="+stockCode+" 时间="+nowTime+" 当前低位"+str(round(currentLatitude,2))) 
     if currentAmplitude >= 1:
       risePoint = risePoint+1
       logging.info("name="+stockName+" code="+stockCode+" 时间="+nowTime+" 涨跌幅:"+str(round(currentLatitude,2))+" 上扬次数:"+str(risePoint)+" 分钟级别上扬:"+str(round(currentAmplitude,2)))
       cursor.execute("INSERT INTO minute_level (stock_code, stock_name, rise_point, down_point, current_amplitude_rise, current_latitude, now_time,deal_date) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)",(stockCode,stockName,str(risePoint),str(downPoint),str(round(currentAmplitude,2)),str(round(currentLatitude,2)),nowTime,baseDate))
       db.commit()
     if currentAmplitude <= -1:
       downPoint = downPoint+1
       cursor.execute("INSERT INTO minute_level (stock_code, stock_name, rise_point, down_point, current_amplitude_down,current_latitude, now_time,deal_date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",(stockCode,stockName,str(risePoint),str(downPoint),str(round(currentAmplitude,2)),str(round(currentLatitude,2)),nowTime,baseDate))
       db.commit()
       logging.info("name="+stockName+" code="+stockCode+" 时间="+nowTime+" 涨跌幅:"+str(round(currentLatitude,2))+" 下挫次数:"+str(downPoint)+ " 分钟级别下挫:"+str(round(currentAmplitude,2)))
     effectRow = cursor.execute("INSERT INTO stock_data (stock_code,now_time,start_price,end_price,lowest_price,highest_price,yesterday_price,current_amplitude,current_latitude,create_time,rise_point,down_point) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (stockCode,nowTime,startPrice,endPrice,currentLowestPrice,currentHighestPrice,yesterDayPrice,currentAmplitude,currentLatitude,nowTime,risePoint,downPoint))
     db.commit()

def processDayCompleteInfo(stockCode,code,stockName,note,holdFlag):
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
   cursor.execute("SELECT yesterday_price,start_price  FROM stock_day_base_info WHERE stock_code='%s' AND DATE(create_time)='%s'" % (stockCode,baseDate))
   existFlag = cursor.fetchone()
   if existFlag:
      if existFlag[1]:
        return existFlag[0]
      else:
        cursor.execute("update stock_day_base_info A ,stock_data B SET A.start_price = B.start_price where A.stock_code='%s' AND  A.stock_code=B.stock_code AND B.now_time='%s' " % (stockCode,openStockTime))
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
    cursor.execute("SELECT A.maxPrice FROM (select max(high_price) as maxPrice,stock_code,stock_name from hold_stock_day_info where deal_date>=(SELECT * FROM (select deal_date from trade_days where deal_date<=DATE(now()) ORDER BY deal_date DESC limit 12) A ORDER BY A.deal_date limit 1) GROUP BY  stock_code) A where A.stock_code = '%s'" % (stockCode))
    max12Price =  cursor.fetchone()
    cursor.execute("INSERT INTO stock_day_base_info(stock_code,stock_name,yesterday_price,note,create_time,update_time,hold_flag,max_12_price) VALUES (%s,%s,%s,%s,%s,now(),%s,%s)",(stockCode,stockName,yesterDayPrice,note,baseDate,holdFlag,str(max12Price[0]))) 
    db.commit()
    return yesterDayPrice


def processDownThree(nowTime):
  cursor.execute("SELECT A.stock_code,C.now_time,C.current_latitude,C.lowest_price,A.start_price,D.rize_amplitude,ROUND(((C.lowest_price-A.start_price)/C.yesterday_price)*100,2) AS downPoint,D.stock_name,A.current_latitude FROM (SELECT * FROM stock_data where now_time='%s') A,stock_day_base_info B, (SELECT * FROM stock_data where now_time ='%s') C, (SELECT * from hold_stock_day_info where deal_date='%s' AND rize_amplitude>0) D where  A.stock_code = B.stock_code AND A.stock_code = C.stock_code   AND A.stock_code=D.stock_code AND ((C.lowest_price-A.start_price)/C.yesterday_price)*100<-3 AND ((C.lowest_price-C.yesterday_price)/C.yesterday_price)*100>-8 AND A.lowest_price>=1.5  ORDER BY downPoint " %(baseDate+" 09:31:00",nowTime,beforeDate))
  downThreeFetch = cursor.fetchall()
  if downThreeFetch:
    logging.info("###############################强势股下移#############################")
    logging.info("code   时间    涨幅   低位    开价     昨涨    下点    名称")
    for downThree in downThreeFetch:
      #涨停股下杀近5个点才可介入
      if downThree[8]>9.5 and downThree[6]<-4.8:
        logging.info("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (downThree[0],nowTime[11:17],downThree[2],downThree[3],downThree[4],downThree[5],downThree[6],downThree[7]))
      elif downThree[8]<=9.5:
        logging.info("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (downThree[0],nowTime[11:17],downThree[2],downThree[3],downThree[4],downThree[5],downThree[6],downThree[7]))

def processRiseThree(nowTime):
  cursor.execute("SELECT A.stock_code,C.now_time,C.current_latitude,C.lowest_price,A.start_price,D.rize_amplitude,ROUND(((C.highest_price - A.start_price) / C.yesterday_price) * 100, 2) AS riseThree,D.stock_name,A.current_latitude FROM (SELECT * FROM stock_data WHERE now_time = '%s') A, stock_day_base_info B, (SELECT * FROM stock_data WHERE now_time = '%s') C, (SELECT * FROM hold_stock_day_info WHERE deal_date = '%s' AND rize_amplitude > 0) D WHERE A.stock_code = B.stock_code AND A.stock_code = C.stock_code AND A.stock_code = D.stock_code AND ((C.lowest_price - A.start_price) / C.yesterday_price) * 100 > 3  AND ROUND(((A.start_price-C.yesterday_price) / C.yesterday_price) * 100, 2)<3 AND ((C.lowest_price - C.yesterday_price) / C.yesterday_price) * 100 > -8 AND A.lowest_price >= 1.5 ORDER BY riseThree " %(baseDate+" 09:31:00",nowTime,beforeDate))
  riseThreeFetch = cursor.fetchall()
  if riseThreeFetch:
    logging.info("###############################上涨趋势上涨动能#############################")
    logging.info("code   时间    涨幅   低位    开价     昨涨    上点    名称")
    for riseThree in riseThreeFetch:
       logging.info("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s" % (riseThree[0],nowTime[11:17],riseThree[2],riseThree[3],riseThree[4],riseThree[5],riseThree[6],riseThree[7]))
   
def processLowerest(nowTime):
  cursor.execute("SELECT ((A.lowest_price-A.yesterday_price)/A.yesterday_price)*100 as riseAm,A.stock_code,B.stock_name,A.rise_point,A.down_point FROM stock_data A,hold_stock B where A.stock_code = B.stock_code AND A.now_time='%s' ORDER BY riseAm limit 6" % (nowTime))
  lowerestFetch = cursor.fetchall()
  if lowerestFetch:
    codeList=''
    for lowerest in lowerestFetch:
      logging.info("倒数三位最低股票 当前低位=%s  stockCode=%s stockName=%s" %(str(lowerest[0]),str(lowerest[1]),str(lowerest[2])))
      if len(codeList)<=12:
        if int(lowerest[3])>0 or int(lowerest[4])>0:
          codeList = codeList+str(lowerest[1])
      
    #smsVerifySend(codeList,nowTime,baseDate)


def sevenFiveProcess(stockCode,nowPrice,nowTime):
    MAX_PRICE_KEY = "MAX_PRICE_"+baseDate+"_"+stockCode
    START_PRICE_KEY = "START_PRICE_"+baseDate+"_"+stockCode
    maxPrice = r.get(MAX_PRICE_KEY)
    startPrice = r.get(START_PRICE_KEY)
    if not maxPrice:
      cursor.execute("select max_12_price from stock_day_base_info where stock_code='%s' and create_time='%s'" %(stockCode,baseDate))
      maxPriceFetch = cursor.fetchone()
      if maxPriceFetch:
        maxPrice = maxPriceFetch[0]
        #设置过期时间 24*60*60
        r.setex(MAX_PRICE_KEY,24*60*60,str(maxPrice))
    if not startPrice:
      cursor.execute("select start_price  from stock_data where stock_code='%s' and now_time='%s'" %(stockCode,baseDate+" 09:31:00"))
      startPriceFetch = cursor.fetchone()
      if startPriceFetch:
        startPrice = startPriceFetch[0]
        r.setex(START_PRICE_KEY,24*60*60,str(startPrice))
    if startPrice and  maxPrice and nowPrice:
      maxPrice = decimal.Decimal(maxPrice)
      startPrice = decimal.Decimal(startPrice)
      nowPrice = decimal.Decimal(nowPrice)
      startPercent = startPrice/maxPrice
      nowPercent = nowPrice/maxPrice
      if startPercent>0.76 and nowPercent<0.752:
        smsVerifySend(stockCode,nowTime,baseDate) 
        print("发送第1梯度",stockCode,nowTime,nowPrice)
      if startPercent<0.75 and  nowPercent<0.708:
        smsVerifySend(stockCode,nowTime,baseDate)
        print("发送第2梯度",stockCode,nowTime,nowPrice)
      if nowPercent<0.62:
        smsVerifySend(stockCode,nowTime,baseDate)


if __name__ == '__main__':
  doJob()
