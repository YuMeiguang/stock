# coding=utf-8
import requests,json
import pymysql
import time
import datetime
import decimal
from decimal import *
import pymysql
import constant


db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

url="https://dataapi.joinquant.com/apis"
#获取调用凭证
body={
    "method": "get_token",
    "mob": "17611579536",  
    "pwd": constant.jqDataPwd,  
}
response = requests.post(url, data = json.dumps(body))
token=response.text

cursor = db.cursor()

beforeDate = "2021-05-14"

now = datetime.datetime.now()

endTime  = now.strftime('%Y-%m-%d %H:%M:%S')

def execute():
     processDayCompleteInfo()
def processDayCompleteInfo():
   body={
      "method": "get_all_trade_days",
      "token": token
    }
   response = requests.post(url, data = json.dumps(body))
   dataArray = response.text.split('\n')
   yesterDayPrice = response.text[3]
   print(dataArray)
   del dataArray[0]
   if len(dataArray)==0 :
     return



if __name__ == '__main__':
  execute()
