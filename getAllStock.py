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

beforeDate = "2020-11-20"

def doJob():
  #5分钟同步一次
  synNewStock()


def synNewStock():
  print("=========执行同步已发行最新股票 开始============")
  dict={'00':'XSHE','300':'XSHG','60':'XSHG','688':'XSHG'}
  rangeNum={'00':'3000|6000','300':'300|999','60':'1000|6000','688':'000|999'}
  for key in dict:
    baseCode = str(key)
    simpleHead = str(dict[key])
    rangeNumStr = rangeNum[key]
    rangeNumStart = int(rangeNumStr.split('|')[0])
    rangeNumEnd = int(rangeNumStr.split('|')[1])
    for num in range(rangeNumStart,rangeNumEnd):
      #补全位数
      buquanNum = 6-len(baseCode)
      code = baseCode+str(num).rjust(buquanNum,'0')
      codeReq = code +'.'+simpleHead
      processDayCompleteInfo(code,codeReq,simpleHead)
  print("=========执行同步已发行最新股票 结束============")

def processDayCompleteInfo(stockCode,code,simpleHead):
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
   response = requests.post(url, data = json.dumps(body))
   dataArray = response.text.split('\n')  
   del dataArray[0]
   if dataArray:
     cursor.execute("SELECT * FROM all_stock where stock_code='%s'"%(stockCode))
     one = cursor.fetchone()
     if one:
        print(code+"已存在")
     else:
       cursor.execute("INSERT INTO all_stock(stock_code,stock_name,simple_head) VALUES('%s','未知','%s')" % (str(stockCode),simpleHead))
       db.commit()
       print("插入股票"+code)
   #else:
   #   print(stockCode) 

if __name__ == '__main__':
  doJob()
