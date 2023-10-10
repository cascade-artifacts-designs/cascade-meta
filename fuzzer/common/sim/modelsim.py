import os
import filelock
from pathlib import Path

def get_next_worker_id():
    lockfile_path = os.getenv("MODELSIM_LOCKFILE")
    if not os.path.exists(lockfile_path):
        Path(os.path.dirname(lockfile_path)).mkdir(parents=True, exist_ok=True)
        Path(lockfile_path).touch()
    lock = filelock.FileLock(f"{lockfile_path}.lock")
    with lock:
        with open(lockfile_path, "r") as f:
            prev_id = f.read()
        if prev_id == "":
            prev_id = 0
        my_id = ((int(prev_id) + 1) % int(os.getenv("MODELSIM_MAX_INSTANCES")))
        with open(lockfile_path, "w") as f:
            f.write(str(my_id))
    return my_id
