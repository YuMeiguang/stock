import os
import time
import datetime
import pymysql
import configparser
from apscheduler.schedulers.blocking import BlockingScheduler
import constant

# 1.九点清理
# 2.如果发现服务启动着先停止服务，在清理，之后启动
# 3.四点之后关闭服务 
# 4.三点20执行当天全量同步任务
# 5.四点执行选股逻辑

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

def doJob():
  scheduler = BlockingScheduler()
  scheduler.add_job(startJob, 'cron', hour=9,minute=1,id='job1')
  scheduler.add_job(killJob, 'cron', hour=15,minute=3,id='job2')
  scheduler.add_job(processDayInfo, 'cron', hour=15,minute=5,id='job3')
  scheduler.start()
  #exeFlag()


def exeFlag():
  cursor = db.cursor()
  todayStr = time.strftime("%Y-%m-%d", time.localtime())
  print(todayStr)
  cursor.execute("select * from trade_days where deal_date='%s' " % (todayStr))
  dbFlag = cursor.fetchone()
  if not dbFlag:
     print("今天不在执行时间范围内")
     return 1
  else:
     print("在执行时间范围内")
     return 0

def startJob():
  #if exeFlag() == 1:
  #  return
  os.system("kill -9 `ps -ef|grep python3|grep stock.py|awk '{print $2}'`")
  os.system("python3 /root/stock/clean.py")
  os.system("nohup python3 -u /root/stock/stock.py >> /root/stock/index.html 2>&1 &")

def killJob():
  #if exeFlag() == 1:
  #  return
  os.system("kill -9 `ps -ef|grep python3|grep stock.py|awk '{print $2}'`")

def processDayInfo():
  #if exeFlag() == 1:
  #  return
  os.system("python3 /root/stock/dayInfo.py")
  os.system("python3 /root/stock/pickingStock.py")

if __name__ == '__main__':
  doJob()
