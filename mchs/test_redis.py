import redis

from main import PHONE

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

r.set('MYPHONE', PHONE)
phone = r.get('MYPHONE')
print(phone)