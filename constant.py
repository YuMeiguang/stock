import configparser

cf = configparser.ConfigParser()
cf.read("config.ini")

host = cf.get("mysql", "host")
userName = cf.get("mysql","userName")
password = cf.get("mysql","password")
exeSwitch = cf.getboolean("switch","exe_switch")
jqDataPwd = cf.get('password','jqDataPwd')

accessKeyId = cf.get("sms","accessKeyId")
accessKeySecret = cf.get("sms","accessKeySecret")
smsSwitch = cf.get("sms","smsSwitch")
phoneNumbers = cf.get("sms","phoneNumbers")
signName = cf.get("sms","signName")
smsTemplateCode = cf.get("sms","smsTemplateCode")
myNumber = cf.get("sms","myNumber")
bucketName = cf.get("oss","bucketName")

redisHost = cf.get("redis", "host")
redisPassword = cf.get("redis","password")
redisPort = cf.get("redis","port")

