import redis
import constant
r = redis.Redis(host=constant.redisHost,port=constant.redisPort,password=constant.redisPassword,db=0,decode_responses=True)
r.set('foo','for')
r.get('foo')
print(r.get('foo'))
