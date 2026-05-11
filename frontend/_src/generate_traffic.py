# import json
import time
import sys

import requests
import numpy as np


# import utils


# configurations
API_URL = "https://localhost:8001/french"
N_RUNS = 100 

def generate_traffic(url, count: int):
    """
    Generates simulated traffic to an API endpoint.
    """
    print(f"\n--- Generating {count} requests to {url} ---")

    n_errors = 0
    n_requests = 0

    for i in range(count):

        if n_errors > 10:
            print("\n[ERROR --> EXIT] More than 10 errors occured. Thus, script is stopped now.\n")
            # break 
            sys.exit(2)

        SLEEP_SECONDS = 10*float(np.random.random(
                            size=1, 
                            # random_state=42
                            ))
        if i % 10 == 0:
            print(f"  - Sending request {i+1}/{count}...")
        
        response = requests.get(url)  
                                # json=sample_features_copy, 
                                # timeout=10)

        n_requests += 1

        if response.status_code != 200:
            n_errors += 1
            continue

        print(f"[response.status_code]\t{response.text}")

        

        # response.raise_for_status()
        time.sleep(SLEEP_SECONDS)

        
    print(f"{n_requests} API requests sent.")

if __name__ == "__main__":
    generate_traffic(url=API_URL, count=N_RUNS)
