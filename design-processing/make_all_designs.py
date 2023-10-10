# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script makes all designs for verilator.

import json
import multiprocessing as mp
import os
import subprocess
import sys

def make_design_worker(design_path, instrumentation):
    print("Making design", design_path, "with instrumentation", instrumentation)
    subprocess.run(["rm", "-rf", os.path.join(design_path, f"run_{instrumentation}_notrace.core")], check=True)
    subprocess.run(["make", "-C", design_path, f"run_{instrumentation}_notrace"], check=False)
    return True

if __name__ == "__main__":
    instrumentation = 'vanilla'
    if len(sys.argv) > 1:
        instrumentation = sys.argv[1]
        assert instrumentation in ['vanilla', 'rfuzz', 'drfuzz'], f"Unknown instrumentation `{instrumentation}`"

    with open("design_repos.json", "r") as f:
        design_repos = json.load(f)

    # For rfuzz and drfuzz, we only want the non-buggy designs, i.e., when '-' is not in the name. Also ignore cva6 because of y1
    if instrumentation != 'vanilla':
        design_repos = {k: v for k, v in design_repos.items() if '-' not in k and 'cva6' not in k}

    all_design_names, all_design_paths = design_repos.keys(), design_repos.values()
    design_names_novex, design_paths_novex  = list(filter(lambda s: 'vex' not in s, all_design_names)), list(filter(lambda s: 'vex' not in s, all_design_paths))
    design_names_vex, design_paths_vex      = list(filter(lambda s: 'vex' in s, all_design_names)), list(filter(lambda s: 'vex' in s, all_design_paths))

    worker_cnt = int(os.environ['CASCADE_JOBS'])

    rets = []
    with mp.Pool(processes=worker_cnt) as pool:
        for design_path in design_paths_novex:
            print('Path:', design_path, len(design_path))
            rets.append(pool.apply_async(make_design_worker, (design_path, instrumentation)))
        pool.close()

        # Do the vexriscv designs separately, since apparently it clashes a bit with the other versions
        for design_path in all_design_paths:
            if 'vexriscv' in design_path:
                print('Vexpath:', design_path)
                make_design_worker(design_path, instrumentation)
        pool.join()
    for ret in rets:
        ret.get()
