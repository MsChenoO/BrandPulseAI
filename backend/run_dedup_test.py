#!/usr/bin/env python3
# Run deduplication worker for testing

import subprocess
import time
import signal
import sys

print("Starting deduplication worker...")
print("Will process messages for 8 seconds then stop\n")

# Start worker
proc = subprocess.Popen(
    ["python", "workers/deduplication_worker.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

try:
    # Read output for 8 seconds
    start_time = time.time()
    while time.time() - start_time < 8:
        line = proc.stdout.readline()
        if line:
            print(line, end='')
        if proc.poll() is not None:
            break
        time.sleep(0.1)

    # Kill process
    proc.send_signal(signal.SIGINT)
    time.sleep(1)

    # Read remaining output
    remaining = proc.stdout.read()
    if remaining:
        print(remaining, end='')

except KeyboardInterrupt:
    proc.send_signal(signal.SIGINT)

finally:
    proc.wait()
    print("\n\nWorker stopped.")
