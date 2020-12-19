import threading
import time

def worker():
  count = 0
  while True:
    if (count > 5):
      raise RuntimeError()
    
      time.sleep(1)
      print("working")
      count += 1

t = threading.Thread(target = worker,name='worker')

t.start()

print("====END=====")
