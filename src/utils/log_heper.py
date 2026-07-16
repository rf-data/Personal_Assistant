

import os
import psutil


def log_memory(label: str):
    process = psutil.Process(os.getpid())

    rss_mb = process.memory_info().rss / 1024**2

    print(
        f"[MEM] {label}: "
        f"{rss_mb:.1f} MB RSS"
    )