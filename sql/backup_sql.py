import os
import time
import datetime
import configparser
from apscheduler.schedulers.blocking import BlockingScheduler


def doJob():
  scheduler = BlockingScheduler()
  scheduler.add_job(execute, 'interval', days=1, id='job1')
  scheduler.start()
  #execute()

def execute():
  cf = configparser.ConfigParser()
  cf.read("../config.ini")
  host = cf.get("mysql", "host")
  userName = cf.get("mysql","userName")
  password = cf.get("mysql","password")

  DATETIME = time.strftime('%Y%m%d')
  BASE_PATH = '/root/stock_sql/'
  os.system('mysqldump -h'+host+' -u'+userName+' -p'+password+' market >'+BASE_PATH+DATETIME+'.sql')


if __name__ == '__main__':
  doJob()
