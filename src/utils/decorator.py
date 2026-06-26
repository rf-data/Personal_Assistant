## decorator.py
# import
import time

def timer(func):
    
   def wrapper(*args, **kwargs):
        
        start = time.perf_counter()
        
        result = func(*args, **kwargs)
        
        end = time.perf_counter()
        
        print(
            f"{func.__name__}: "
            f"{end-start:.4f}s"
        )
        
        return result
   
   return wrapper

"""
@timer
def expensive_task():
    total = 0
    for i in range(10_000_000):
        total += i
    return total

expensive_task()
"""


import os
from datetime import datetime

def record_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        snapshot = {
            "function": func.__name__,
            "args": args,
            "kwargs": kwargs,
            "env": dict(os.environ)
        }
        with open("execution_log.json", "a") as f:
            f.write(json.dumps(snapshot) + "\n")
        return func(*args, **kwargs)
    return wrapper
@record_execution
def process_order(order_id, amount):
    return amount * 1.18
process_order(42, 99.99)