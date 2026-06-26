## automate_helper.py
# import

import subprocess
import time
from collections import deque

import heapq
import time


import multiprocessing
import time



'''
import os
import time

TEMP_DIR = "temp_files"

def cleanup_temp_files():

    now = time.time()

    for file in os.listdir(TEMP_DIR):

        path = os.path.join(TEMP_DIR, file)

        if os.stat(path).st_mtime < now - 86400:
            os.remove(path)
            print("Deleted:", path)

cleanup_temp_files()
'''

'''
import schedule
import time

def daily_pipeline():

    print("Running automation pipeline")

schedule.every().day.at("02:00").do(daily_pipeline)

while True:

    schedule.run_pending()

    time.sleep(1)
'''


def worker():

    while True:
        try:
            print("Worker running...")
            time.sleep(3)

            # simulate occasional crash
            if int(time.time()) % 15 == 0:
                raise Exception("Random crash")

        except Exception as e:
            print("Worker crashed:", e)
            time.sleep(2)

def start_worker():

    while True:
        process = multiprocessing.Process(target=worker)
        process.start()

        process.join()

        print("Restarting worker process...")
        time.sleep(3)

# start_worker()

#######################
'''

tasks = []

def add_task(task):
    tasks.append(task)

def view_tasks():
    for i, task in enumerate(tasks):
        print(f"{i+1}. {task}")

add_task("Send invoice")
add_task("Follow up client")

view_tasks()

'''


tasks = []

def add_task(name, deadline):
    heapq.heappush(tasks, (deadline, name))

add_task("send_report", time.time() + 60)
add_task("cleanup", time.time() + 3600)

while tasks:
    deadline, task = heapq.heappop(tasks)
    if time.time() > deadline:
        print(f"Skipping expired task: {task}")
    else:
        print(f"Running task: {task}")

########

FAIL_WINDOW = 300  # seconds
MAX_FAILS = 3

failures = deque()

def run_script():
    return subprocess.run(
        ["python", "worker.py"],
        capture_output=True
    )

while True:
    result = run_script()
    if result.returncode != 0:
        now = time.time()
        failures.append(now)
        while failures and now - failures[0] > FAIL_WINDOW:
            failures.popleft()
        if len(failures) >= MAX_FAILS:
            print("Too many failures. Escalating.")
            # trigger alert / stop system
            break
    time.sleep(5)

import subprocess
import time

while True:
    process = subprocess.Popen(
        ["python", "worker.py"]
    )

    code = process.wait()

    print(f"Exited with {code}")

    time.sleep(5)

import psutil
import time

def system_ready():
    return (
        psutil.cpu_percent() < 40 and
        psutil.virtual_memory().percent < 70
    )

while True:
    if system_ready():
        print("Running heavy task")
        # do expensive work
        break
    else:
        print("System busy. Waiting.")
        time.sleep(10)