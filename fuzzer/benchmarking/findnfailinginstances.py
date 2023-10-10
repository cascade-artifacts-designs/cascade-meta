# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This utility finds n distinct failing program descriptors

from params.runparams import PATH_TO_TMP
from cascade.fuzzfromdescriptor import gen_new_test_instance, fuzz_single_from_descriptor
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed

import json
import os
import time
import threading
import multiprocessing as mp
from tqdm import tqdm

callback_lock = threading.Lock()
newly_finishing_instances = 0
newly_failing_instances = 0
all_failing_instances = []

def test_done_callback(ret):
    global newly_failing_instances
    global newly_finishing_instances
    global callback_lock
    global all_failing_instances
    with callback_lock:
        newly_finishing_instances += 1
        if ret is None:
            return
        else:
            newly_failing_instances += 1
            all_failing_instances.append(ret)

def _find_n_failing_descriptors_worker(memsize, design_name, process_instance_id, num_bbs, authorize_privileges):
    result = fuzz_single_from_descriptor(memsize, design_name, process_instance_id, num_bbs, authorize_privileges, None, True)
    # result is 0, 0, 0, 0 iff the program descriptor is failing
    if result == (0, 0, 0, 0):
        return (memsize, design_name, process_instance_id, num_bbs, authorize_privileges)
    else:
        return None

def find_n_failing_descriptors(design_name: str, num_testcases: int, num_workers: int, seed_offset: int = 0, can_authorize_privileges: bool = True):
    global callback_lock
    global newly_failing_instances
    global newly_finishing_instances
    global all_failing_instances

    newly_failing_instances = 0
    newly_finishing_instances = 0
    all_failing_instances.clear()

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    pool = mp.Pool(processes=num_workers)
    process_instance_id = seed_offset

    # First, apply the function to all the workers.
    for _ in range(num_workers):
        memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, process_instance_id, can_authorize_privileges)
        pool.apply_async(_find_n_failing_descriptors_worker, args=(memsize, design_name, process_instance_id, num_bbs, authorize_privileges), callback=test_done_callback)
        process_instance_id += 1

    # Respawn processes until we received the desired number of failing descriptors
    with tqdm(total=num_testcases) as pbar:
        while newly_finishing_instances < num_testcases:
            # Yield the execution
            time.sleep(1)
            # Check whether we received new coverage paths
            with callback_lock:
                if newly_failing_instances > 0:
                    pbar.update(newly_failing_instances)
                    newly_failing_instances = 0
                if newly_finishing_instances > 0:
                    if len(all_failing_instances) >= num_testcases:
                        print(f"Received enough failing instances for design `{design_name}`. Stopping.")
                        break
                    for new_process_id in range(newly_finishing_instances):
                        pool.apply_async(_find_n_failing_descriptors_worker, args=(*gen_new_test_instance(design_name, process_instance_id, True),), callback=test_done_callback)
                        process_instance_id += 1
                    newly_finishing_instances = 0

    # Kill all remaining processes
    pool.close()
    pool.terminate()

    # Ensure we do not have too many instances due to parallelism
    all_failing_instances = all_failing_instances[:num_testcases]

    # Save the requested number of failing instances
    json.dump(all_failing_instances, open(os.path.join(PATH_TO_TMP, f"failinginstances_{design_name}_{num_testcases}.json"), 'w'))
    print('Saved failing program descriptors results to', os.path.join(PATH_TO_TMP, f"failinginstances_{design_name}_{num_testcases}.json"))
