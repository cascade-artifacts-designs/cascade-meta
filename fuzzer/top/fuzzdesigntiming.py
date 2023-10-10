# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module is responsible to measure the time required to find a bug, given some behavior tolerances and a specific design name

from params.runparams import PATH_TO_TMP, PATH_TO_FIGURES
from common.timeout import timeout
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed
from cascade.fuzzfromdescriptor import gen_new_test_instance, run_rtl

import threading
import time

callback_lock = threading.Lock()
newly_finished_tests = 0
curr_round_id = 0
all_times_to_detection = []

def bug_detection_callback(ret):
    global newly_finished_tests
    global callback_lock
    global curr_round_id
    global all_times_to_detection
    with callback_lock:
        newly_finished_tests += 1
        if ret is not None:
            if len(all_times_to_detection) <= curr_round_id:
                all_times_to_detection.append(ret)

@timeout(seconds=60*60*2)
def run_rtl_single_for_timebugdetection(memsize: int, design_name: str, randseed: int, nmax_bbs: int, start_time: float, authorize_privileges: bool, nmax_instructions: int, nodependencybias: bool):
    assert type(nmax_instructions) == int or nmax_instructions is None, f"nmax_instructions must be an integer or None, but its type is {type(nmax_instructions)}"
    assert type(nodependencybias) == bool, f"nodependencybias must be a boolean, but its type is {type(nodependencybias)}"
    try:
        run_rtl(memsize, design_name, randseed, nmax_bbs, authorize_privileges, False, nmax_instructions, nodependencybias)
        return None
    except Exception as e:
        # print(f"Failed run_rtl_single_for_timebugdetection for params memsize: `{memsize}`, design_name: `{design_name}`, check_pc_spike_again: `{False}`, randseed: `{randseed}`, nmax_bbs: `{nmax_bbs}`, authorize_privileges: `{authorize_privileges}`, nmax_instructions: `{nmax_instructions}`, nodependencybias: `{nodependencybias}` -- ({memsize}, design_name, {randseed}, {nmax_bbs})")
        # print(e)
        if start_time is None:
            start_time = 0
        time_to_detection = time.time() - start_time
        # print(f"  Time to detection (seconds): {time.time() - start_time}")
        if start_time:
            return time_to_detection

def measure_time_to_bug(design_name: str, num_cores: int, num_reps: int, nmax_instructions: int = None, nodependencybias: bool = False, time_limit_seconds: int = None):
    assert type(nmax_instructions) == int or nmax_instructions is None, f"nmax_instructions must be an integer or None, but its type is {type(nmax_instructions)}"
    assert type(nodependencybias) == bool, f"nodependencybias must be a boolean, but its type is {type(nodependencybias)}"

    global newly_finished_tests
    global callback_lock
    global all_times_to_detection
    global curr_round_id

    newly_finished_tests = 0
    all_times_to_detection = []
    curr_round_id = 0

    import multiprocessing as mp

    num_workers = num_cores
    assert num_workers > 0

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    print(f"Starting timing of bug detection on `{design_name}` on {num_workers} processes.")

    assert num_reps > 0, "num_reps must be > 0, may it be for bug detection timing or just normal fuzzing"

    for global_iter_id in range(num_reps):
        exit_global_loop = False
        # print(f"Starting global iteration {global_iter_id}.")

        newly_finished_tests = 0
        exit_curr_global_rep = False

        start_time = time.time()

        pool = mp.Pool(processes=num_workers)
        process_instance_id = 0
        # First, apply the function to all the workers. We do not use map because some instances, rarely, seem to be stuck if there are bugs in some of the EDA tools.
        for process_id in range(num_workers):
            memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, process_instance_id, True)
            if nmax_instructions is not None:
                num_bbs = 10000
            pool.apply_async(run_rtl_single_for_timebugdetection, args=(memsize, design_name, process_instance_id+50000*global_iter_id, num_bbs, start_time, authorize_privileges, nmax_instructions, nodependencybias), callback=bug_detection_callback)
            process_instance_id += 1

        while not exit_curr_global_rep:
            time.sleep(2)
            # Check whether we received new coverage paths
            with callback_lock:
                if newly_finished_tests > 0:
                    assert len(all_times_to_detection) <= curr_round_id + 1
                    if len(all_times_to_detection) == curr_round_id + 1 or (time_limit_seconds is not None and time.time() - start_time > time_limit_seconds):
                        # # If the detection failed, do not try again
                        # if len(all_times_to_detection) <= curr_round_id:
                        #     exit_global_loop = True
                        #     print("Did not find. Abandoning this scenario.")
                        exit_curr_global_rep = True
                        curr_round_id += 1
                        print(f"Curr all times to detection: [{' '.join(map(lambda x: f'{x:2f}', all_times_to_detection))}]")
                        break

                    for new_process_id in range(newly_finished_tests):
                        memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, process_instance_id, True)
                        if nmax_instructions is not None:
                            num_bbs = 10000
                        pool.apply_async(run_rtl_single_for_timebugdetection, args=(memsize, design_name, process_instance_id+50000*global_iter_id, num_bbs, start_time, authorize_privileges, nmax_instructions, nodependencybias), callback=bug_detection_callback)
                        process_instance_id += 1
                    newly_finished_tests = 0

        if exit_global_loop:
            break

        # This code is only reached if we are measuring the time to bug detection
        pool.close()
        pool.terminate()

    # This code is only reached if we are measuring the time to bug detection
    print(f"Times to bug detection (seconds): {all_times_to_detection}")
    if len(all_times_to_detection) < curr_round_id:
        print(f"WARNING: The time to bug detection was not measured for all the rounds. This is likely due to a timeout that we set to cap the duration dedicated to bug detection.")
        # Fill the rest of times to detection with None
        for _ in range(curr_round_id - len(all_times_to_detection)):
            all_times_to_detection.append(None)

    return all_times_to_detection

def plot_bug_timings(num_workers: int, num_reps: int):
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    import json
    import os

    # bug_names = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'v15', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'k1', 'k2', 'k3', 'k4', 'k5', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'b1', 'b2', 'y1', 'r1']
    # Remove the v12 and shift the remainings down
    bug_names = ['v1', 'v2', 'v3', 'v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', 'v13', 'v14', 'p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'k1', 'k2', 'k3', 'k4', 'k5', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 'c8', 'c9', 'c10', 'b1', 'b2', 'y1', 'r1']
    all_series = []
    for bug_name in bug_names:
        jsonpath = os.path.join(PATH_TO_TMP, f"bug_timings_{bug_name}_{num_workers}_{num_reps}.json")
        new_series = json.load(open(jsonpath, 'r'))
        all_series.append(new_series)

    fig, ax = plt.subplots(figsize=(15, 2))
    boxplot = ax.boxplot(all_series, vert=True, showfliers=False)

    # Customize the colors
    for median_line in boxplot['medians']:
        median_line.set(color='red', linewidth=1.2, zorder=0)

    ax.set_xticklabels(list(map(lambda s: s.upper(), bug_names)))
    ax.set_ylabel('Time to discovery (s)')

    # Make the y axis logarithmic
    ax.set_yscale('log')

    # Add y ticks at 10, 100 and 1000
    ax.set_yticks([1, 10, 100, 1000])
    ax.yaxis.set_major_formatter(mticker.ScalarFormatter())

    # Straddle the x ticks
    for i, tick in enumerate(ax.xaxis.get_ticklabels()):
        if i % 2 == 0:
            tick.set_y(0)
        else:
            tick.set_y(0-0.05)

    ax.yaxis.grid(which='major')

    plt.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'bug_detection_timings.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)
