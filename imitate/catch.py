# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
cursor = db.cursor()

baseDate = "2020-05-08"

def processCatch(baseDate):
  closeTime = baseDate + " 14:59:00"
  startTIme1 = baseDate + "09:35:00"
  startTime2 = baseDate + "09:43:00"

  

if __name__ == '__main__':
  processSyn(baseDate)
