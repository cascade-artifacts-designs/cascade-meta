# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module runs Cascade and collects multiplexer toggle coverage.

from common.timeout import timeout
from params.runparams import PATH_TO_TMP
from common.spike import calibrate_spikespeed
from common.profiledesign import profile_get_medeleg_mask
from cascade.fuzzfromdescriptor import NUM_MAX_BBS_UPPERBOUND, gen_fuzzerstate_elf_expectedvals, gen_new_test_instance
from cascade.fuzzsim import runtest_verilator_forrfuzz

import json
import multiprocessing as mp
import os
import random
import threading
import time
from tqdm import tqdm


# This helps tracking how many new processes to spawn
rfuzz_coverage_lock = threading.Lock()
newly_collected_coverages_size = 0
collected_coverages = []
collected_durations = []

def callback_collectrfuzz(collected_coverage_time_tuple: str):
    global collected_coverages
    global newly_collected_coverages_size
    global rfuzz_coverage_lock
    with rfuzz_coverage_lock:
        if collected_coverage_time_tuple is None:
            return
        collected_coverage, collected_duration = collected_coverage_time_tuple
        if collected_coverage is not None:
            collected_coverages.append(collected_coverage)
            collected_durations.append(collected_duration)
            newly_collected_coverages_size += 1

# @return a pair (rfuzz_coverage_mask, duration in seconds)
@timeout(seconds=60*60)
def _measure_coverage_rfuzz_worker(memsize: int, design_name: str, randseed: int, nmax_bbs: int, authorize_privileges: bool):
    try:
        start_time = time.time()
        fuzzerstate, elfpath, _, _, _, _ = gen_fuzzerstate_elf_expectedvals(memsize, design_name, randseed, nmax_bbs, authorize_privileges, True)
        rfuzz_coverage_mask = runtest_verilator_forrfuzz(fuzzerstate, elfpath)
        return rfuzz_coverage_mask, time.time() - start_time
    except:
        print(f"Ignored failed instance with tuple: ({memsize}, design_name, {randseed}, {nmax_bbs})")
        return 0, -1

# Get the rfuzz coverage of Cascade
def collect_coverage_rfuzz(design_name: str, num_cores: int, num_testcases: int):
    # assert not DO_ASSERT, "Please disable DO_ASSERT for performance measurements"
    global collected_coverages
    global newly_collected_coverages_size
    global collected_durations

    collected_coverages.clear()
    collected_durations.clear()
    newly_collected_coverages_size = 0

    num_workers = min(num_cores, num_testcases)
    assert num_workers > 0

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    print(f"Starting mux select coverage testing of `{design_name}` on {num_workers} processes.")

    pool = mp.Pool(processes=num_workers)
    process_instance_id = 0
    # First, apply the function to all the workers.
    for process_id in range(num_workers):
        pool.apply_async(_measure_coverage_rfuzz_worker, args=(*gen_new_test_instance(design_name, process_instance_id, True),), callback=callback_collectrfuzz)
        process_instance_id += 1    

    # Respawn processes until we received the desired number of coverage paths
    with tqdm(total=num_testcases) as pbar:
        while newly_collected_coverages_size < num_testcases:
            # Yield the execution
            time.sleep(1)
            # Check whether we received new coverage paths
            with rfuzz_coverage_lock:
                if newly_collected_coverages_size > 0:
                    pbar.update(newly_collected_coverages_size)
                    if len(collected_coverages) >= num_testcases:
                        print(f"Received enough coverages. Stopping.")
                        break
                    for new_process_id in range(newly_collected_coverages_size):
                        pool.apply_async(_measure_coverage_rfuzz_worker, args=(*gen_new_test_instance(design_name, process_instance_id, True),), callback=callback_collectrfuzz)
                        process_instance_id += 1
                    newly_collected_coverages_size = 0

    # Kill all remaining processes
    pool.close()
    pool.terminate()

    print(f"Parallel section complete, proceeding to merging.")

    all_coverage_masks = collected_coverages
    durations = collected_durations

    coverage_sequence = []
    last_merged_coverage_mask = None
    for coverage_mask_id, coverage_mask in enumerate(tqdm(all_coverage_masks)):
        # Check whether this was a failed instance
        if durations[coverage_mask_id] == -1:
            continue

        # Add the coverage of the last step
        if last_merged_coverage_mask is not None:
            last_merged_coverage_mask |= coverage_mask
        else:
            last_merged_coverage_mask = coverage_mask
        coverage_sequence.append(bin(last_merged_coverage_mask).count('1'))

    # Export a json with coverage_sequence and durations
    json_filepath = os.path.join(PATH_TO_TMP, f"rfuzz_coverages_{design_name}_{num_testcases}_{NUM_MAX_BBS_UPPERBOUND}.json")
    with open(json_filepath, 'w') as f: 
        json.dump({'coverage_sequence': coverage_sequence, 'durations': durations}, f)
    return json_filepath

