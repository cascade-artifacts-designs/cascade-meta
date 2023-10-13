# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script evaluates the duration to detect each bug.

from top.fuzzdesigntiming import measure_time_to_bug, plot_bug_timings
from cascade.toleratebugs import tolerate_bug_for_bug_timing

from params.runparams import PATH_TO_TMP
import json
import os
import sys

bug_designs = {
    'p1': 'picorv32',
    'p2': 'picorv32',
    'p3': 'picorv32',
    'p4': 'picorv32',
    'p5': 'picorv32-p5',
    'p6': 'picorv32',
    'v1': 'vexriscv-v1-7',
    'v2': 'vexriscv-v1-7',
    'v3': 'vexriscv-v1-7',
    'v4': 'vexriscv-v1-7',
    'v5': 'vexriscv-v1-7',
    'v6': 'vexriscv-v1-7',
    'v7': 'vexriscv-v1-7',
    'v8': 'vexriscv-v8-9-v15',
    'v9': 'vexriscv-v8-9-v15',
    'v10': 'vexriscv-v10-11',
    'v11': 'vexriscv-v10-11',
    # 'v12': 'vexriscv-v12',
    'v12': 'vexriscv-v13',
    'v13': 'vexriscv',
    'v14': 'vexriscv-v8-9-v15',
    'k1': 'kronos-k1',
    'k2': 'kronos-k2',
    'k3': 'kronos',
    'k4': 'kronos',
    'k5': 'kronos',
    'c1': 'cva6-c1',
    'c2': 'cva6',
    'c3': 'cva6',
    'c4': 'cva6',
    'c5': 'cva6',
    'c6': 'cva6',
    'c7': 'cva6',
    'c8': 'cva6',
    'c9': 'cva6',
    'c10': 'cva6',
    'b1': 'boom-b1',
    'b2': 'boom',
    'r1': 'rocket',
    'y1': 'cva6-y1',
}

def gen_path_to_json(bug_name, num_workers, num_reps, max_num_instructions, nodependencybias, timeout_seconds):
    filebasename = f"bug_timings_{bug_name}_{num_workers}_{num_reps}"
    if max_num_instructions is not None:
        filebasename += f"_maxinstr{max_num_instructions}"
    else:
        filebasename += f"_nomaxinstr"

    if nodependencybias:
        filebasename += f"_nodepbias"
    else:
        filebasename += f"_depbias"
    filebasename += f"_timeout{timeout_seconds}"
    return os.path.join(PATH_TO_TMP, f"{filebasename}.json")

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    num_workers = int(sys.argv[1])
    num_reps = int(sys.argv[2])
    timeout_seconds = int(sys.argv[3])

    # Pairs (maxnuminstrs, nodependencybias)
    scenarios = [
        (1, False),
        (10, False),
        # (10, True),
        (100, False),
        # (100, True),
        (1000, False),
        # (1000, True),
        (10000, False),
        # (10000, True),
        # (100000, False),
        # (100000, True),
    ]

    # Measure the time to detect each bug.
    for bug_name, design_name in bug_designs.items():
        tolerate_bug_for_bug_timing(design_name, bug_name, True)
        for scenario in scenarios:
            max_num_instructions, nodependencybias = scenario
            ret = measure_time_to_bug(design_name, num_workers, num_reps, max_num_instructions, nodependencybias, timeout_seconds)
            retpath = gen_path_to_json(bug_name, num_workers, num_reps, max_num_instructions, nodependencybias, timeout_seconds)
            json.dump(ret, open(retpath, "w"))
            print('Saved bug timing results to', retpath)
        tolerate_bug_for_bug_timing(design_name, bug_name, False)

    # Regroup the JSONs for convenience
    from collections import defaultdict
    all_rets = {}
    for bug_name, _ in bug_designs.items():
        all_rets[bug_name] = defaultdict(dict)
        for scenario in scenarios:
            max_num_instructions, nodependencybias = scenario
            retpath = gen_path_to_json(bug_name, num_workers, num_reps, max_num_instructions, nodependencybias, timeout_seconds)
            all_rets[bug_name][max_num_instructions][nodependencybias] = json.load(open(retpath, "r"))
    # Write a single json out of them
    aggregated_json_path = os.path.join(PATH_TO_TMP, f"bug_timings_all.json")
    json.dump(all_rets, open(aggregated_json_path, "w"))
    print('Saved aggregated timing results to', aggregated_json_path)

    # Plot these measurements.
    # plot_bug_timings(num_workers, num_reps)
    # plot_bug_timings_scenarios(num_workers, num_reps)

else:
    raise Exception("This module must be at the toplevel.")
