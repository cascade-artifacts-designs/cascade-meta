# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This utility finds n distinct failing program descriptors. It is supposed to be preceded by find_n_failing_descriptors.

from params.runparams import PATH_TO_TMP, PATH_TO_FIGURES
from cascade.reduce import reduce_program
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed

import json
import os
import time
import threading
import multiprocessing as mp
from tqdm import tqdm
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42

callback_lock = threading.Lock()
newly_completed_reductions_nb = 0
all_reduction_results = [] # Tuples (success, duration (seconds))
num_failures = 0

def reduction_done_callback(ret):
    global newly_completed_reductions_nb
    global callback_lock
    global all_reduction_results
    global num_failures
    with callback_lock:
        newly_completed_reductions_nb += 1
        if ret is None:
            num_failures += 1
        else:
            all_reduction_results.append(ret)

def reduce_program_worker(size: int, design_name: str, randseed: int, nmax_bbs: int, authorize_privileges: bool, find_pillars: bool, quiet: bool = False, target_dir: str = None, hint_left_bound_bb: int = None, hint_right_bound_bb: int = None, hint_left_bound_instr: int = None, hint_right_bound_instr: int = None, hint_left_bound_pillar_bb: int = None, hint_right_bound_pillar_bb: int = None, hint_left_bound_pillar_instr: int = None, hint_right_bound_pillar_instr: int = None, check_pc_spike_again: bool = False):
    try:
        return reduce_program(size, design_name, randseed, nmax_bbs, authorize_privileges, find_pillars, quiet, target_dir, hint_left_bound_bb, hint_right_bound_bb, hint_left_bound_instr, hint_right_bound_instr, hint_left_bound_pillar_bb, hint_right_bound_pillar_bb, hint_left_bound_pillar_instr, hint_right_bound_pillar_instr, check_pc_spike_again)
    except Exception as e:
        print(f"Exception in reduce_program_worker for tuple: ({size}, '{design_name}', {randseed}, {nmax_bbs})")
        return None

def eval_reduction(design_name: str, num_testcases: int, num_workers: int):
    global callback_lock
    global newly_completed_reductions_nb
    global all_reduction_results
    global num_failures

    newly_completed_reductions_nb = 0
    all_reduction_results.clear()
    num_failures = 0

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    # Read the failing program descriptors
    json_path = os.path.join(PATH_TO_TMP, f"failinginstances_{design_name}_{2*num_testcases}.json")
    workloads = json.load(open(json_path, 'r'))

    # Also find the pillars (aka. head)
    workloads = [(memsize, design_name, process_instance_id, num_bbs, authorize_privileges, True) for memsize, design_name, process_instance_id, num_bbs, authorize_privileges in workloads]

    # Because of concurrency, we may have slightly more than 2*num_testcases instances. We just take the first 2*num_testcases.
    assert len(workloads) >= 2*num_testcases, f"Expected {2*num_testcases} failing instances, but found {len(workloads)} in {json_path}"
    workloads = workloads[:2*num_testcases]

    pool = mp.Pool(processes=num_workers)
    workload_id = 0

    # First, apply the function to all the workers.
    for _ in range(min(num_testcases, num_workers)):
        pool.apply_async(reduce_program_worker, args=workloads[workload_id], callback=reduction_done_callback)
        workload_id += 1

    # Respawn processes until we received the desired number of reductions
    with tqdm(total=num_testcases) as pbar:
        while len(all_reduction_results) < num_testcases:
            # Yield the execution
            time.sleep(1)
            # Check whether we received new coverage paths
            with callback_lock:
                if newly_completed_reductions_nb > 0:
                    pbar.update(newly_completed_reductions_nb)
                    if len(all_reduction_results) >= num_testcases:
                        print(f"Received enough failing instances for design `{design_name}`. Stopping.")
                        break
                    for new_process_id in range(newly_completed_reductions_nb):
                        if workload_id >= len(workloads):
                            break
                        pool.apply_async(reduce_program_worker, args=workloads[workload_id], callback=reduction_done_callback)
                        workload_id += 1
                    newly_completed_reductions_nb = 0

    # Kill all remaining processes
    pool.close()
    pool.terminate()

    # Save the requested number of failing instances
    json_path = os.path.join(PATH_TO_TMP, f"evalreduction_{design_name}_{num_testcases}.json")
    print('Saving figure to', json_path)
    os.makedirs(PATH_TO_TMP, exist_ok=True)
    json.dump({'all_reduction_results': all_reduction_results, 'num_failures': num_failures}, open(json_path, 'w'))

DESIGN_PRETTY_NAMES = {
    'picorv32': 'PicoRV32',
    'kronos': 'Kronos',
    'vexriscv': 'VexRiscv',
    'rocket': 'Rocket',
    'cva6': 'CVA6',
    'boom': 'BOOM',
}

def plot_eval_reduction(design_names: str, num_testcases: int):
    all_successes_per_design = dict()
    all_timings_per_design = dict()
    all_numinstrs_per_design = dict()
    for design_name in design_names:
        # Load json paths
        json_path = os.path.join(PATH_TO_TMP, f"evalreduction_{design_name}_{num_testcases}.json")
        print('Loading', json_path)

        json_content = json.load(open(json_path, 'r'))
        all_data_per_design, num_failures = json_content['all_reduction_results'], json_content['num_failures']
        all_successes_per_design[design_name] = list(map(lambda x: x[0], all_data_per_design))
        all_timings_per_design[design_name] = list(map(lambda x: x[1], all_data_per_design))
        all_numinstrs_per_design[design_name] = list(map(lambda x: x[2], all_data_per_design))

    # Print the number of successes per design
    for design_name in design_names:
        print(f"Design {design_name} has success: {num_testcases-num_failures}/{num_testcases}.")

    # Find the absolute min and max numbers of test cases
    min_numinstrs = min([min(all_numinstrs_per_design[design_name]) for design_name in design_names])
    max_numinstrs = max([max(all_numinstrs_per_design[design_name]) for design_name in design_names])

    print('Absolute min and max numbers of instructions in a test case:', min_numinstrs, max_numinstrs)

    all_series = [[1000*all_timings_per_design[design_name][i]/(all_numinstrs_per_design[design_name][i]) for i in range(len(all_timings_per_design[design_name]))] for design_name in design_names]

    fig, ax = plt.subplots(figsize=(5, 1.25))
    boxplot = ax.boxplot(all_series, vert=True, showfliers=False)

    # Customize the colors
    for median_line in boxplot['medians']:
        median_line.set(color='blue', linewidth=1.2, zorder=0)

    ax.set_xticklabels(list(map(lambda design_name: DESIGN_PRETTY_NAMES[design_name], design_names)))
    ax.set_ylabel('Seconds / k instr')
    ax.yaxis.grid(which='major')

    plt.tight_layout()

    # Export the figure
    # Make the dir and its parents
    outfile_path_png = os.path.join(PATH_TO_FIGURES, 'reduction_perf.png')
    outfile_path_pdf = os.path.join(PATH_TO_FIGURES, 'reduction_perf.pdf')
    print('Saving figure to', outfile_path_png)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(outfile_path_png, dpi=300)
    plt.savefig(outfile_path_pdf)
