# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
from apscheduler.schedulers.blocking import BlockingScheduler

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

cursor = db.cursor()

baseDate = "2020-04-22 "

def doJob():
  scheduler = BlockingScheduler()
  scheduler.add_job(processJudge, 'interval', seconds=60, id='job1')
  scheduler.start()

def processJudge():
  cursor.execute("SELECT stock_code,stock_name,pre_buy_point,trend  FROM stock_day_base_info ")
  baseInfo = cursor.fetchall()
  for stock in baseInfo:
     getPreBuyStock(stock[0],stock[1],stock[2],stock[3])
  print("======================")
  #cursor.close()
  #db.close()

def getPreBuyStock(stockCode,stockName,preBuyPoint,trend):
  startDate = baseDate+"10:00:00" 
  cursor.execute("SELECT *  FROM stock_data WHERE stock_code ='%s' AND lowest_price<='%s'  AND now_time>='%s'" % (stockCode,preBuyPoint,startDate))
  existFlag = cursor.fetchall()
  if existFlag:
    print (stockName,preBuyPoint,trend) 
  

if __name__ == '__main__':
  doJob()
