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
from matplotlib import pyplot as plt
from collections import defaultdict
import numpy as np

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

DO_SAVE_PER_BUG_BARPLOTS = False

# bug_designs = {
#     # 'p2': 'picorv32',
#     'v2': 'vexriscv-v1-7',
#     'k2': 'kronos-k2',
#     'c2': 'cva6',
# }

# sys.argv[1]: num of workers
# sys.argv[2]: num of repetitions
# sys.argv[3]: max num instructions. If 0, then no max num instructions.
# sys.argv[4]: 'nodeps' or 'deps'. All other values are errors

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

    # These parameters must correspond to the parameters used to generate the data.
    NUM_WORKERS = int(sys.argv[1])
    NUM_REPS = int(sys.argv[2])
    TIMEOUT_SECONDS = int(sys.argv[3])

    # Legacy
    NUM_REPS_SECONDARY = 5

    # Do not show bugs detected by all in less than this number of seconds
    FILTER_DETECTION_DURATION_SECONDS = int(sys.argv[4])

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

    # Collect the data
    all_data = defaultdict(lambda : defaultdict(dict))
    for bug_name, design_name in bug_designs.items():
        for scenario in scenarios:
            numinstrs, nodep = scenario
            filepath = gen_path_to_json(bug_name, NUM_WORKERS, NUM_REPS, numinstrs, nodep, TIMEOUT_SECONDS)
            if not os.path.exists(filepath):
                filepath = gen_path_to_json(bug_name, NUM_WORKERS, NUM_REPS_SECONDARY, numinstrs, nodep, TIMEOUT_SECONDS)
                if not os.path.exists(filepath):
                    print(f"WARNING: No data for bug {bug_name} in scenario {numinstrs} {nodep}. Skipping this scenario.")
                    continue
            all_data[bug_name][numinstrs][nodep] = json.load(open(filepath, "r"))
            
    if 'r1' in all_data.keys():
        del all_data['r1'] # r1 was already a known bug

    # all_data = json.load(open(os.path.join(PATH_TO_TMP, f"bug_timings_all.json"), "r"))

    num_bugs_detected_per_scenario = defaultdict(lambda : defaultdict(int))
    all_scenarios = set()

    all_numinstrs_set = set()
    all_nodep_set = set()

    failed_scenarios = defaultdict(lambda : defaultdict(dict))
    median_vals = defaultdict(lambda : defaultdict(dict))
    for bug_name in all_data.keys():
        Ys = []
        X_labels = []
        for numinstrs in all_data[bug_name].keys():
            for nodep in all_data[bug_name][numinstrs].keys():
                # If all the elements of all_data[bug_name][numinstrs][nodep] are None
                all_None = True
                for elem in all_data[bug_name][numinstrs][nodep]:
                    if elem is not None:
                        all_None = False
                        break
                if all_None:
                    failed_scenarios[bug_name][numinstrs][nodep] = True
                    Ys.append(0)
                    X_labels.append(f"{numinstrs} (0 %)")
                    continue
                # Say the percentage of successes in the array
                num_successes = 0
                for i, elem in enumerate(all_data[bug_name][numinstrs][nodep]):
                    if elem is None:
                        break
                    num_successes += 1

                X_labels.append(f"{numinstrs} ({100 * num_successes // len(all_data[bug_name][numinstrs][nodep])} %)")
                
                num_bugs_detected_per_scenario[numinstrs][nodep] += 1
                all_scenarios.add((numinstrs, nodep))
                print(f"Bug name: {bug_name}, numinstrs: {numinstrs}, nodep: {nodep}, time: {all_data[bug_name][numinstrs][nodep][0]}")
                failed_scenarios[bug_name][numinstrs][nodep] = False
                # Remove the None instances
                all_data[bug_name][numinstrs][nodep] = list(filter(lambda x: x is not None, all_data[bug_name][numinstrs][nodep]))
                # Compute the median
                median_vals[bug_name][numinstrs][nodep] = np.median(all_data[bug_name][numinstrs][nodep])
                Ys.append(median_vals[bug_name][numinstrs][nodep])

                all_numinstrs_set.add(numinstrs)
                all_nodep_set.add(nodep)

        # Check if all found it in less than this number of seconds
        if all([y < FILTER_DETECTION_DURATION_SECONDS for y in Ys]):
            print(f"FILTERING: All scenarios detected bug {bug_name} in less than {FILTER_DETECTION_DURATION_SECONDS} seconds. Skipping this bug.")
            continue

        if DO_SAVE_PER_BUG_BARPLOTS:
            assert len(Ys) == len(X_labels), f"len(Ys)={len(Ys)} != len(X_labels)={len(X_labels)}"
            # Put Ys in code-hours
            for i, y in enumerate(Ys):
                Ys[i] = y * NUM_WORKERS / 3600
            Xs = np.arange(len(X_labels))
            fig, ax = plt.subplots(figsize=(8, 2))
            ax.bar(Xs, Ys, color='tab:blue')
            ax.set_xticks(Xs)
            ax.set_xticklabels(X_labels)
            ax.set_ylabel('Median time (core-hours)')
            ax.set_title(f"Bug {bug_name}")
            ax.yaxis.grid(which='major')
            plt.tight_layout()
            plt.savefig(os.path.join('.', f"bug_timings_{bug_name}.png"))
            plt.close()

    # Say number of bugs detected per scenario
    print(f"Number of bugs detected per scenario:")
    for numinstrs in all_data[bug_name].keys():
        for nodep in all_data[bug_name][numinstrs].keys():
            print(f"    {numinstrs} {nodep}: {num_bugs_detected_per_scenario[numinstrs][nodep]}")

    ###########################
    # Do the plot of number of bugs found by each program length over time.
    ###########################

    Xs_curves = defaultdict(lambda: defaultdict(list))
    Ys_curves = defaultdict(lambda: defaultdict(list))


    for bug_name in all_data.keys():
        Ys = []
        X_labels = []
        for numinstrs in all_data[bug_name].keys():
            for nodep in all_data[bug_name][numinstrs].keys():
                print (f"bug_name: {bug_name}, numinstrs: {numinstrs}, nodep: {nodep}")
                if failed_scenarios[bug_name][numinstrs][nodep]:
                    continue

                Xs_curves[numinstrs][nodep].append(median_vals[bug_name][numinstrs][nodep])

    # Now compute the Ys. First sort the Xs
    for numinstrs in all_numinstrs_set:
        for nodep in all_nodep_set:
            Xs_curves[numinstrs][nodep] = list(map(int, np.sort(Xs_curves[numinstrs][nodep])))

    # Normalize the Xs to core-hours
    for numinstrs in all_numinstrs_set:
        for nodep in all_nodep_set:
            for i, x in enumerate(Xs_curves[numinstrs][nodep]):
                Xs_curves[numinstrs][nodep][i] = x * NUM_WORKERS / 3600

    for numinstrs in Xs_curves.keys():
        for nodep in Xs_curves[numinstrs].keys():
            Ys_curves[numinstrs][nodep] = list(map(int, np.arange(1, len(Xs_curves[numinstrs][nodep])+1)))

    # Plot the curves, not a bar plot
    fig, ax = plt.subplots(figsize=(6, 2.1))
    for numinstrs in Xs_curves.keys():
        for nodep in Xs_curves[numinstrs].keys():
            ax.plot(Xs_curves[numinstrs][nodep], Ys_curves[numinstrs][nodep], linestyle='--', linewidth=1, marker='d', label=f"{numinstrs} fuzz. instr.")

    ax.set_ylabel('New bugs found')
    ax.set_xlabel('Median time to discovery (core-hours)')
    # Legend with two columns
    ax.legend(ncol=2, loc='lower right')

    ax.yaxis.grid(which='major')
    plt.tight_layout()
    # plt.savefig(os.path.join('.', f"bug_timings_curves.png"))
    # plt.savefig(os.path.join('.', f"bug_timings_curves.pdf"))

    json.dump({
        'Xs_curves': Xs_curves,
        'Ys_curves': Ys_curves,
    }, open(os.path.join('.', f"bug_timings_curves.json"), "w"))

    ##################
    # Plotting
    ##################

    from matplotlib import pyplot as plt
    import json
    import os

    json_dict = json.load(open("bug_timings_curves.json", "r"))
    Xs_curves = json_dict['Xs_curves']
    Ys_curves = json_dict['Ys_curves']

    markers = [
        'd',
        'o',
        's',
        'p',
        'P',
    ]

    colors = [
        'green',
        'orange',
        'black',
        'blue',
        (240/256, 0/256, 0/256),
    ]

    # Plot the curves, not a bar plot
    fig, ax = plt.subplots(figsize=(6, 2.2))
    id_in_markers = 0
    for numinstrs in Xs_curves.keys():
        for nodep in Xs_curves[numinstrs].keys():
            ax.plot(Xs_curves[numinstrs][nodep], Ys_curves[numinstrs][nodep], linestyle='--', linewidth=1, marker=markers[id_in_markers], color=colors[id_in_markers], label=f"{float(numinstrs):,.0f} fuzz. instr.")
            id_in_markers += 1

    # Set specific yticks
    ax.set_yticks([0, 10, 20, 30, 38])

    ax.set_ylabel('New bugs found')
    ax.set_xlabel('Median time to discovery (core-hours)')
    # Legend with two columns
    fig.legend(ncol=2, loc='center right', framealpha=1)

    ax.yaxis.grid(which='major')
    plt.tight_layout()

    plt.savefig('bug_timings_curves.png', dpi=300)
    plt.savefig('bug_timings_curves.pdf')

else:
    raise Exception("This module must be at the toplevel.")
