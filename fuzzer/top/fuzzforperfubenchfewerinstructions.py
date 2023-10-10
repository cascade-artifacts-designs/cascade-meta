# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Toplevel for a cycle of program generation and RTL simulation.

from common.spike import calibrate_spikespeed
from common.profiledesign import profile_get_medeleg_mask
from cascade.fuzzfromdescriptor import gen_new_test_instance, fuzz_single_from_descriptor
from cascade.fuzzsim import SimulatorEnum, runtest_simulator
from cascade.fuzzfromdescriptor import gen_fuzzerstate_elf_expectedvals

from time import time

def fuzz_for_perf_ubench_fewerinstructions(design_name: str, seed_offset: int, can_authorize_privileges: bool, time_limit_seconds: int, max_num_instructions: int):
    instance_gen_durations = []
    run_durations = []
    effective_num_instrs = []

    memsize = 1 << 20 # Dont want to be limited by the mem size
    # Does not matter as long as big enough since the cap will be the num of instructions
    nmax_bbs = 10000

    cumulated_time = 0
    while cumulated_time < time_limit_seconds:
        seed_offset += 1

        # try:
        # Gen the test case
        instance_gen_start_time = time()
        memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, seed_offset, can_authorize_privileges, memsize, nmax_bbs)
        fuzzerstate, rtl_elfpath, finalregvals_spikeresol, time_seconds_spent_in_gen_bbs, time_seconds_spent_in_spike_resol, time_seconds_spent_in_gen_elf = gen_fuzzerstate_elf_expectedvals(memsize, design_name, seed_offset, nmax_bbs, authorize_privileges, False, max_num_instructions)
        gen_duration = time() - instance_gen_start_time

        # Run the test case
        run_start_time = time()
        is_success, rtl_msg = runtest_simulator(fuzzerstate, rtl_elfpath, finalregvals_spikeresol, simulator=SimulatorEnum.VERILATOR)
        run_duration = time() - run_start_time
        # except:
        #     print(f"Got an exception, typically a Spike timeout. May happen in rare OS scheduling cases. Rerunning this specific test. This is witout consequences.")
        #     continue

        instance_gen_durations.append(gen_duration)
        run_durations.append(run_duration)
        cumulated_time += gen_duration + run_duration
        effective_num_instrs.append(fuzzerstate.get_num_fuzzing_instructions_sofar()-1) #-1 because it counts the last jump

    return instance_gen_durations, run_durations, effective_num_instrs
