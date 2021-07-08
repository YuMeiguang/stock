# coding=utf-8
import requests,json
import pymysql
import time
import decimal
from decimal import *
import os
import sys
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")
cursor = db.cursor()


def cleanData():
  print('清理前一日数据 开始')
  #clean stock_data数据
  cursor.execute("TRUNCATE TABLE stock_data")
  cleaStockData = cursor.fetchall()
  #clean stock_base_info
  cursor.execute("TRUNCATE TABLE stock_day_base_info")
  cleanBaseInfo = cursor.fetchall()

  #clean stock_data_imitate
  cursor.execute("TRUNCATE TABLE stock_data_imitate")
  cleanStockDataImitate = cursor.fetchall()
  #clean stock_day_base_info_imitate
  cursor.execute("TRUNCATE TABLE stock_day_base_info_imitate")
  cleanBaseInfoDataImitate = cursor.fetchall()
  try:
    os.remove("index.html")
  except:
    print("文件不存在")
  print('清理前一日数据 结束')
if __name__ == '__main__':
  cleanData()
