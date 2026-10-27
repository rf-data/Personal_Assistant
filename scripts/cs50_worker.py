"""C26 capacity guard over the unchanged C22/C16 executor and lifecycle."""

import argparse
import os
import sqlite3
import time
from pathlib import Path

from src.job_control.catalog import verified_files
from src.job_control.executor import Executor
from src.job_control.operations import fence, preflight
from src.tools_materials.capacity import check_capacity, free_space, load_limits


class CapacityExecutor(Executor):
    def __init__(self, settings, limits):
        if settings.max_parallel != 1:
            raise ValueError("C26 requires a single active processing job")
        self.limits, self.next_budget_check = limits, 0.0
        check_capacity(settings.root, limits.job_bytes, limits.reserve_bytes)
        catalog_bytes = 0
        for entry in settings.catalog.values():
            catalog_bytes += sum(len(data) for data in verified_files(entry).values())
            if catalog_bytes > limits.catalog_bytes:
                raise ValueError("Capacity catalog byte budget exceeded")
        super().__init__(settings)

    def step(self):
        free_space(self.settings.root, self.limits.reserve_bytes)
        if time.monotonic() >= self.next_budget_check:
            check_capacity(
                self.settings.root, self.limits.job_bytes, self.limits.reserve_bytes
            )
            self.next_budget_check = time.monotonic() + 1
        super().step()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--limits", type=Path, required=True)
    args = p.parse_args(argv)
    os.umask(0o077)
    try:
        limits = load_limits(args.limits)
        settings = preflight(args.config, min_free_bytes=limits.reserve_bytes)
        with fence(settings.root):
            CapacityExecutor(settings, limits).serve()
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as error:
        print("C26 worker stopped: " + type(error).__name__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
