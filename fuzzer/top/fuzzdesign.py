# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Toplevel for a cycle of program generation and RTL simulation.

from common.spike import calibrate_spikespeed
from common.profiledesign import profile_get_medeleg_mask
from cascade.fuzzfromdescriptor import gen_new_test_instance, fuzz_single_from_descriptor

import time
import threading

callback_lock = threading.Lock()
newly_finished_tests = 0
curr_round_id = 0
all_times_to_detection = []

def test_done_callback(arg):
    global newly_finished_tests
    global callback_lock
    global curr_round_id
    global all_times_to_detection
    with callback_lock:
        newly_finished_tests += 1

def fuzzdesign(design_name: str, num_cores: int, seed_offset: int, can_authorize_privileges: bool):
    global newly_finished_tests
    global callback_lock
    global all_times_to_detection
    global curr_round_id

    newly_finished_tests = 0
    curr_round_id = 0
    all_times_to_detection = []

    import multiprocessing as mp

    num_workers = num_cores
    assert num_workers > 0

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)
    print(f"Starting parallel testing of `{design_name}` on {num_workers} processes.")

    newly_finished_tests = 0
    pool = mp.Pool(processes=num_workers)
    process_instance_id = seed_offset
    # First, apply the function to all the workers.
    for _ in range(num_workers):
        memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, process_instance_id, can_authorize_privileges)
        pool.apply_async(fuzz_single_from_descriptor, args=(memsize, design_name, process_instance_id, num_bbs, authorize_privileges, None, True), callback=test_done_callback)
        process_instance_id += 1

    while True:
        time.sleep(2)
        # Check whether we received new coverage paths
        with callback_lock:
            if newly_finished_tests > 0:
                for _ in range(newly_finished_tests):
                    memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, process_instance_id, can_authorize_privileges)
                    pool.apply_async(fuzz_single_from_descriptor, args=(memsize, design_name, process_instance_id, num_bbs, authorize_privileges, None, True), callback=test_done_callback)
                    process_instance_id += 1
                newly_finished_tests = 0

    # This code should never be reached.
    # Kill all remaining processes
    pool.close()
    pool.terminate()
