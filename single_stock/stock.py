# coding=utf-8
import requests,json
import pymysql
import time
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
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

baseDate = "2020-04-07"
beforeDate = "2020-04-03"
#beforeDate=str((datetime.datetime.strptime(baseDate,'%Y-%m-%d')+datetime.timedelta(days=-1)).strftime("%Y-%m-%d"))


def execute():
  
  prosessSinbleStockAllInfo('300598','300598.XSHG','诚迈科技')
  #processDayCompleteInfo('300598','300598.XSHG','诚迈科技')
  #cursor.close()
  #db.close()

def prosessSinbleStockAllInfo(stockCode,code,stockName):
  startDate = baseDate +  " 09:30:00"
  cursor = db.cursor()
  cursor.execute("SELECT date_format(max(now_time), '%%Y-%%m-%%d %%H:%%i:%%s') FROM stock_data_single WHERE stock_code='%s' " % (stockCode))
  startDateFetch = cursor.fetchone()
  if startDateFetch[0] is None:
     print("============="+code)
  else:
    startDate = startDateFetch[0]
  now = datetime.datetime.now()
  endDate  = now.strftime('%Y-%m-%d %H:%M:%S')
  #处理日交易完结的数据
  processDayCompleteInfo(stockCode,code,stockName)
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
  #print(response)
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
     effectRow = cursor.execute("INSERT INTO stock_data_single (stock_code,now_time,start_price,end_price,lowest_price,highest_price,create_time) VALUES (%s,%s,%s,%s,%s,%s,%s)", (stockCode,nowTime,startPrice,endPrice,currentLowestPrice,currentHighestPrice,time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())))
     db.commit()

def processDayCompleteInfo(stockCode,code,stockName):
   beforeStartDate = beforeDate + " 09:30:00"
   beforeEndDate = beforeDate + " 15:00:00"
   body={
      "method": "get_price_period",
      "token": token,
      "code": code,
      "unit": "1d",
      "date": beforeStartDate,
      "end_date": beforeEndDate,
      "fq_ref_date": beforeDate
    }
   cursor.execute("SELECT * FROM stock_day_base_Info_single WHERE stock_code='%s' AND DATE(create_time)='%s'" % (stockCode,baseDate))
   existFlag = cursor.fetchone()
   if existFlag:
      return
   else:
    response = requests.post(url, data = json.dumps(body))
    dataArray = response.text.split('\n')
    yesterDayPrice = response.text[3]
    del dataArray[0]
    if len(dataArray)==0 :
      print(code)
      return
    yesterDayPriceArray = dataArray[0].split(',')
    yesterDayPrice = yesterDayPriceArray[2]
    cursor.execute("INSERT INTO stock_day_base_Info_single(stock_code,stock_name,yesterday_price,create_time,update_time) VALUES (%s,%s,%s,%s,now())",(stockCode,stockName,yesterDayPrice,baseDate)) 
    db.commit()


if __name__ == '__main__':
  execute()
