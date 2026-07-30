## watchdog.py
# import


# core watcher skeleton I still use today
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Handler(FileSystemEventHandler):
    def on_created(self, event):
        print("Created:", event.src_path)

observer = Observer()
observer.schedule(Handler(), path="/data/inbound", recursive=True)
observer.start()

## design 'directory -> action' pipeline
# directory → handler routing map
ROUTES = {
    "/data/invoices": "process_invoice",
    "/data/images": "thumbnail_image",
    "/data/logs": "parse_log",
}
############################
# HELPER
############################
## event deduplication + micro-delays.
import time

class StableEventHandler(FileSystemEventHandler):
    pending = {}

    def on_modified(self, event):
        self.pending[event.src_path] = time.time()

def flush_stable(handler, delay=0.3):
    now = time.time()
    stable = [p for p,t in handler.pending.items() if now - t > delay]
    for path in stable:
        print("Stable:", path)
        del handler.pending[path]

## turn handler into workflows
import logging

logging.basicConfig(
    filename="automation.log",
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

def workflow(func):
    def wrapper(path):
        logging.info(f"RUN {func.__name__} -> {path}")
      
        try:
            print("Start:", path)
            func(path)
            print("Done:", path)
        except Exception as e:
            print("Error:", e)
    return wrapper

@workflow
def process_invoice(path):
    # parse, validate, push to API
    pass

from queue import Queue
from threading import Thread

q = Queue()

def worker():
    while True:
        fn, path = q.get()
        fn(path)
        q.task_done()

Thread(target=worker, daemon=True).start()

def on_created(self, event):
    task = resolve(event.src_path)  # converts path → function
    q.put((task, event.src_path))

## Preventing Duplicate Runs and Race Conditions
import hashlib

processed = set()

def file_id(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def safe_run(func, path):
    fid = file_id(path)
    if fid in processed:
        return
    processed.add(fid)
    func(path)

## upgrades 
- Async I/O with asyncio for non-blocking tasks
- A pluggable rule engine for mappings
- Better metrics (Prometheus)
- A disk-based checkpoint system for persistence
- Optional cloud emitters
