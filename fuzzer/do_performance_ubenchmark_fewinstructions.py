# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script executes the fuzzer on Rocket and measures the performance when we limit ourselves to a certain number of instructions.

# sys.argv[1]: offset for seed (to avoid running the fuzzing on the same instances over again)
# sys.argv[2]: duration of the experiment in core-seconds

from top.fuzzforperfubenchfewerinstructions import fuzz_for_perf_ubench_fewerinstructions
from cascade.toleratebugs import tolerate_bug_for_eval_reduction
from params.fuzzparams import get_max_num_instructions_upperbound
from common.spike import calibrate_spikespeed
from common.profiledesign import profile_get_medeleg_mask

import json
import os
import sys

def single_measurement(design: str, num_instructions: int, time_limit_seconds: int, seed_offset: int):
    authorize_privileges = True
    instance_gen_durations, run_durations, effective_num_instructions = fuzz_for_perf_ubench_fewerinstructions(design, num_instructions*1234567 + seed_offset, authorize_privileges, time_limit_seconds, num_instructions)
    return instance_gen_durations, run_durations, effective_num_instructions
    # print(f"Instance generation durations: {instance_gen_durations}")
    # print(f"Run durations: {run_durations}")
    # print(f"Effective_num_instructions: {effective_num_instructions}")

    # instructions_per_millisecond_nogen = effective_num_instructions / (sum(run_durations) * 1000)
    # instructions_per_millisecond_livegen = effective_num_instructions / ((sum(run_durations) + sum(instance_gen_durations)) * 1000)
    # print(f"Instructions per millisecond (nogen): {instructions_per_millisecond_nogen}")
    # print(f"Instructions per millisecond (livegen): {instructions_per_millisecond_livegen}")


if __name__ == '__main__':
    import multiprocessing as mp

    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    if len(sys.argv) != 4:
        raise Exception("Usage: python3 do_performance_ubenchmark_fewinstructions.py <seed_offset> <time_limit_seconds_per_core> <num_workers>")

    seed_offset = int(sys.argv[1])
    time_limit_seconds_per_core = int(sys.argv[2])
    num_workers = int(sys.argv[3])

    design_names = [
        'picorv32',
        'kronos',
        'vexriscv',
        'rocket',
        'cva6',
        'boom',
    ]

    nums_instructions = [1, 10, 100, 1000, 10000, 100000]

    calibrate_spikespeed()

    from collections import defaultdict
    instance_gen_durations = defaultdict(lambda: defaultdict(list))
    run_durations = defaultdict(lambda: defaultdict(list))
    effective_num_instructions = defaultdict(lambda: defaultdict(list))

    for design_name in design_names:
        profile_get_medeleg_mask(design_name)
        for num_instructions in nums_instructions:
            print(f"Starting fuzzing for micro-benchmark of programs with {num_instructions} instructions on `{design_name}`.")

            input_pool = [(design_name, num_instructions, time_limit_seconds_per_core, seed_offset+1000*i) for i in range(num_workers)]
            seed_offset += 1000000 * num_workers
            with mp.Pool(processes=num_workers) as pool:
                results = pool.starmap(single_measurement, input_pool)
            # results is a list of triples (instance_gen_durations, run_durations, effective_num_instructions)

            for worker_result in results:
                new_instance_gen_durations, new_run_durations, new_effective_num_instructions = worker_result
                instance_gen_durations[design_name][num_instructions] += new_instance_gen_durations
                run_durations[design_name][num_instructions] += new_run_durations
                effective_num_instructions[design_name][num_instructions] += new_effective_num_instructions

    with open('perf_ubenchmark_fewinstructions.json', 'w') as f:
        json.dump({
            'nums_instructions': nums_instructions,
            'instance_gen_durations': instance_gen_durations,
            'run_durations': run_durations,
            'effective_num_instructions': effective_num_instructions,
        }, f)
    print("Saved results to perf_ubenchmark_fewinstructions.json")



else:
    raise Exception("This module must be at the toplevel.")
