# coding=utf-8
import requests,json
import pymysql
import time
import datetime
import decimal
from decimal import *
import constant

url="https://dataapi.joinquant.com/apis"

url="https://dataapi.joinquant.com/apis"
db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
#获取调用凭证
body={
    "method": "get_token",
    "mob": "17611579536", 
    "pwd": constant.jqDataPwd,  
}
response = requests.post(url, data = json.dumps(body))
token=response.text

cursor = db.cursor()

beforeDate = "2020-05-14"

now = datetime.datetime.now()

endTime  = now.strftime('%Y-%m-%d %H:%M:%S')

def execute():
     processDayCompleteInfo()
def processDayCompleteInfo():
   body={
      "method": "get_billboard_list",
      "token": token,
      "code":"000002.XSHE",
      "date":"2019-09-20",
      "end_date":"2019-09-23"
    }
   response = requests.post(url, data = json.dumps(body))
   dataArray = response.text.split('\n')
   print(dataArray)
   del dataArray[0]
   if len(dataArray)==0 :
     return



if __name__ == '__main__':
  execute()
