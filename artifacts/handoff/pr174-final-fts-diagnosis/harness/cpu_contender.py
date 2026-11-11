"""One time-bounded, inherited-affinity CPU contender; no I/O after READY."""
import time

until = time.monotonic() + 45
print('READY', flush=True)
value = 1
while time.monotonic() < until:
    for _ in range(10000):
        value = (value * 17 + 13) % 1000003
