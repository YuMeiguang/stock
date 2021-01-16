# coding=utf-8
import requests,json
import pymysql
import time
import datetime
import decimal
from decimal import *
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

cursor.execute("select deal_date from trade_days where deal_date<=DATE(now()) ORDER BY deal_date desc limit 1")

#获取当前时间
#baseDate='2021-01-06'
baseDate = str(cursor.fetchone()[0])

now = datetime.datetime.now()

endTime  = now.strftime('%Y-%m-%d %H:%M:%S')

#baseDate='2021-01-13'
#endTime  = '2021-01-24 15:00:00'

def execute(baseDate):
  #插入当前没有的股票
  cursor.execute("insert into hold_stock_imitate(stock_code,stock_name,interface_code,create_time,update_time) select stock_code,stock_name,simple_head,now(),now() from all_stock where stock_code not in(select stock_code from hold_stock_imitate)")
  db.commit()
  cursor.execute("SELECT * FROM hold_stock_imitate where stock_code NOT IN(SELECT stock_code FROM hold_stock_day_info where deal_date='%s') " % (baseDate))
  holdStockList = cursor.fetchall()
  for holdStock in holdStockList:
     code = holdStock[1]+'.'+holdStock[2]
     processDayCompleteInfo(holdStock[1],code,holdStock[0],baseDate)
  cursor.execute("UPDATE hold_stock_day_info set amplitude = ((high_price-low_price)/yesterday_price)*100,rize_amplitude=((end_price-yesterday_price)/yesterday_price)*100 where yesterday_price!=0")
  db.commit()
def processDayCompleteInfo(stockCode,code,stockName,baseDate):
   startTime = baseDate + " 09:30:00"
   body={
      "method": "get_price_period",
      "token": token,
      "code": code,
      "unit": "1d",
      "date": startTime,
      "end_date": endTime,
      "fq_ref_date": baseDate
    }
   response = requests.post(url, data = json.dumps(body))
   dataArray = response.text.split('\n')
   yesterDayPrice = response.text[3]
   del dataArray[0]
   if len(dataArray)==0 :
     return
   insertValues = []
   for data in dataArray:
     smallDataArray = data.split(',')
     dealDate = smallDataArray[0]
     if dealDate!=baseDate:
       continue
     openPrice = smallDataArray[1]
     endPrice = smallDataArray[2]
     highPrice = smallDataArray[3]
     lowPrice = smallDataArray[4]
     highLimit = smallDataArray[8]
     if len(smallDataArray)<=11:
       yesterdayPrice = '0'
     else:
       yesterdayPrice = smallDataArray[11]
     insertValues.append((stockCode,stockName,openPrice,endPrice,highPrice,lowPrice,yesterdayPrice,dealDate)) 
   cursor.executemany("INSERT INTO hold_stock_day_info(stock_code,stock_name,open_price,end_price,high_price,low_price,yesterday_price,deal_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",insertValues)
   db.commit()



if __name__ == '__main__':
  execute(baseDate)
