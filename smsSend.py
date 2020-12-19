# coding=utf-8
import pymysql
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
import constant

db = pymysql.connect(constant.host,constant.userName,constant.password,"market",charset="utf8")

cursor = db.cursor()

def smsVerifySend(code,nowTime,baseDate):
  if not timeBetween() and not constant.smsSwitch:
    print("时间不在范围内或者开关关闭,无需发短信")
    return 
  phoneNumbers = constant.phoneNumbers;
  client = AcsClient(constant.accessKeyId, constant.accessKeySecret, 'cn-hangzhou')
  request = CommonRequest()
  request.set_accept_format('json')
  request.set_domain('dysmsapi.aliyuncs.com')
  request.set_method('POST')
  request.set_protocol_type('https') #
  request.set_version('2017-05-25')
  request.set_action_name('SendSms')

  request.add_query_param('RegionId', "cn-hangzhou")
  request.add_query_param('SignName', constant.signName)
  request.add_query_param('TemplateCode', constant.smsTemplateCode)
  request.add_query_param('TemplateParam', "{\"code\":\""+code+"\"}")
  if len(code)>6 and len(code)<20 :
    myNumberArray = constant.myNumber;
    #没三分钟发一次短信
    if int(nowTime[14:16])%3 == 2:
      for number in myNumberArray.split(','):
        request.add_query_param('PhoneNumbers', number)
        response = client.do_action(request)
        print(response)
    return
  for number in phoneNumbers.split(','):
    request.add_query_param('PhoneNumbers', number)
    cursor.execute("SELECT * FROM sms_send_record where stock_code='%s' and phone_number='%s' and DATE(send_date)='%s'" % (code,number,baseDate))
    flag = cursor.fetchone()
    if flag:
       pass
    else:
      response = client.do_action(request)
      #cursor.execute("select stock_name from stock_day_base_info where stock_code='%s' AND DATE(create_time)='%s'" % (code,baseDate))
      #stockName = cursor.fetchone()[0]
      stockName='weizhi'
      cursor.execute("INSERT INTO sms_send_record (stock_code,stock_name, phone_number, send_date) VALUES ('%s','%s', '%s', '%s')" % (code,stockName,number,nowTime))
      db.commit()
      print(str(response, encoding = 'utf-8'))

#判断时间是否在 上午九点到下午三点之间
def timeBetween():
  timeStr = str(datetime.datetime.now())
  timeNumber = int(timeStr[11:13])
  # 时间范围结果
  return timeNumber>=1 and timeNumber<=2

def sms75Rule(stockCode,nowPrice):
    print(10)


if __name__ == '__main__':
  smsVerifySend('603986','2020-12-04 09:35:00','2020-12-04')
