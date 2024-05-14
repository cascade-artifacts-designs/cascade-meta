# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module provides facilities for reducing test cases

from common.designcfgs import get_design_march_flags_nocompressed, get_design_boot_addr, get_design_cascade_path
from common.spike import SPIKE_STARTADDR
from cascade.basicblock import gen_basicblocks
from cascade.cfinstructionclasses import JALInstruction, RegImmInstruction
from cascade.fuzzsim import SimulatorEnum, runtest_simulator
from cascade.spikeresolution import gen_elf_from_bbs, gen_regdump_reqs_reduced, gen_ctx_regdump_reqs, run_trace_regs_at_pc_locs, spike_resolution
from cascade.contextreplay import SavedContext, gen_context_setter
from cascade.privilegestate import PrivilegeStateEnum
from params.runparams import DO_ASSERT, NO_REMOVE_TMPFILES

from copy import deepcopy
import itertools
import os
import random
import shutil
import subprocess
import time
from pathlib import Path

REDUCTION_SIMULATOR = SimulatorEnum.VERILATOR
NOPIZE_SANDWICH_INSTRUCTIONS = False # Not fully implemented & tested, hence do not yet set to True
FLATTEN_SANDWICH_INSTRUCTIONS = False # Not fully implemented & tested, hence do not yet set to True

# Used for removing the first BBs and instructions.
def _save_ctx_and_jump_to_pillar_specific_instr(fuzzerstate, index_first_bb_to_consider: int, index_first_instr_to_consider: int):
    print(f"Saving context and jumping to pillar-specific instruction {index_first_bb_to_consider}:{index_first_instr_to_consider}...")
    spikereduce_elfpath = gen_elf_from_bbs(fuzzerstate, False, "spikereduce_savectx", f"{fuzzerstate.instance_to_str()}_{index_first_bb_to_consider}_{index_first_instr_to_consider}", SPIKE_STARTADDR)

    ctx_regdump_reqs, storenumbytes = gen_ctx_regdump_reqs(fuzzerstate, index_first_bb_to_consider, index_first_instr_to_consider)
    dumpedvals = run_trace_regs_at_pc_locs(fuzzerstate.instance_to_str(), spikereduce_elfpath, get_design_march_flags_nocompressed(fuzzerstate.design_name), SPIKE_STARTADDR, ctx_regdump_reqs, False, fuzzerstate.final_bb_base_addr+SPIKE_STARTADDR, fuzzerstate.num_pickable_floating_regs if fuzzerstate.design_has_fpu else 0, fuzzerstate.design_has_fpud)

    del ctx_regdump_reqs

    # Remove the ELF
    if not NO_REMOVE_TMPFILES:
        os.remove(spikereduce_elfpath)
        del spikereduce_elfpath

    # Generate the context setter
    NUM_CSRS = 13 + int(not fuzzerstate.is_design_64bit) # includes the privilege request. +1 for minstreth if 32-bit
    if DO_ASSERT:
        assert (len(dumpedvals) - NUM_CSRS - fuzzerstate.num_pickable_floating_regs - fuzzerstate.num_pickable_regs) % 2 == 0, "The number of dumps for memory operations must be even: one address for one value."

    # Get the saved context
    curr_id_in_dumpedvals = 0
    num_stores_found = (len(dumpedvals) - NUM_CSRS - fuzzerstate.num_pickable_floating_regs - fuzzerstate.num_pickable_regs) // 2
    saved_stores = dict()

    curr_id_in_storenumbytes = 0
    for _ in range(num_stores_found):
        for byte_id in range(storenumbytes[curr_id_in_storenumbytes]):
            addr = dumpedvals[curr_id_in_dumpedvals] + byte_id - SPIKE_STARTADDR
            val = (dumpedvals[curr_id_in_dumpedvals+1] >> (8*byte_id)) & 0xFF
            saved_stores[addr] = val
        curr_id_in_storenumbytes += 1
        curr_id_in_dumpedvals += 2
    csr_count_fordebug = 0
    saved_fcsr = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_mepc = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_sepc = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_mcause = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_scause = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_mscratch = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_sscratch = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_mtvec = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_stvec = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_medeleg = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_mstatus = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    saved_minstret = dumpedvals[curr_id_in_dumpedvals]
    curr_id_in_dumpedvals += 1
    csr_count_fordebug += 1
    if not fuzzerstate.is_design_64bit:
        saved_minstreth = dumpedvals[curr_id_in_dumpedvals]
        curr_id_in_dumpedvals += 1
        csr_count_fordebug += 1
    else:
        saved_minstreth = None

    # Parse the privilege level
    saved_privilege_char = dumpedvals[curr_id_in_dumpedvals]
    if saved_privilege_char == 'M':
        saved_privilege = PrivilegeStateEnum.MACHINE
    elif saved_privilege_char == 'S':
        saved_privilege = PrivilegeStateEnum.SUPERVISOR
    elif saved_privilege_char == 'U':
        saved_privilege = PrivilegeStateEnum.USER
    else:
        raise ValueError("Unknown privilege level: " + str(saved_privilege_char))
    csr_count_fordebug += 1
    curr_id_in_dumpedvals += 1

    if DO_ASSERT:
        assert csr_count_fordebug == NUM_CSRS, "The number of CSRs found is not the expected one. Found: " + str(csr_count_fordebug) + ", expected: " + str(num_csrs)

    if fuzzerstate.design_has_fpu:
        # We only take the low part of the floats, because (currently) spike represents them on 16 bytes.
        if fuzzerstate.design_has_fpud:
            saved_fregvals = list(map(lambda x: ((1 << 64) -1) & x, dumpedvals[curr_id_in_dumpedvals:curr_id_in_dumpedvals+fuzzerstate.num_pickable_floating_regs]))
        else:
            saved_fregvals = list(map(lambda x: ((1 << 32) -1) & x, dumpedvals[curr_id_in_dumpedvals:curr_id_in_dumpedvals+fuzzerstate.num_pickable_floating_regs]))
    else:
        saved_fregvals = []

    curr_id_in_dumpedvals += fuzzerstate.num_pickable_floating_regs
    saved_regvals  = dumpedvals[curr_id_in_dumpedvals:curr_id_in_dumpedvals+fuzzerstate.num_pickable_regs]

    if DO_ASSERT:
        assert curr_id_in_dumpedvals + fuzzerstate.num_pickable_regs == len(dumpedvals)
    saved_context = SavedContext(saved_fcsr,
                                    saved_mepc,
                                    saved_sepc,
                                    saved_mcause,
                                    saved_scause,
                                    saved_mscratch,
                                    saved_sscratch,
                                    saved_mtvec,
                                    saved_stvec,
                                    saved_medeleg,
                                    saved_mstatus,
                                    saved_minstret,
                                    saved_minstreth,
                                    saved_privilege,
                                    saved_stores,
                                    saved_fregvals,
                                    saved_regvals)

    gen_context_setter(fuzzerstate, saved_context, fuzzerstate.bb_start_addr_seq[index_first_bb_to_consider] + index_first_instr_to_consider * 4) # NO_COMPRESSED

    # Jump from the intial state to the context setter
    fuzzerstate.instr_objs_seq[0][-1] = JALInstruction("jal", 0, fuzzerstate.ctxsv_bb_base_addr - 4*(len(fuzzerstate.instr_objs_seq[0])-1)) # NO_COMPRESSED

    return fuzzerstate

# @param max_bb_id_to_consider: the number of BBs to consider, hence from 0 to len(fuzzerstate.instr_objs_seq)-1.
# @param max_instr_id_except_cf: the number of instructions in the bb `max_bb_id_to_consider` to consider in total, including the cf instruction that may be added (equivalently, the max instruction index to consider in the bb `max_bb_id_to_consider` when ignoring the cf instruction). -1 means that we only want the CF instruction. None means that we do not expect to do any replacement.
# @param index_first_bb_to_consider: the index of the first BB to consider. 1 if we remove no bb on the left side.
# @return test_fuzzerstate, rtl_elfpath, (finalintregvals_spikeresol[1:], finalfloatregvals_spikeresol), numinstrs
def gen_reduced_elf(fuzzerstate, max_bb_id_to_consider: int, max_instr_id_except_cf: int = None, index_first_bb_to_consider: int = 1, index_first_instr_to_consider: int = 0):
    # print(f"gen_reduced_elf with max_bb_id_to_consider: {max_bb_id_to_consider}, max_instr_id_except_cf: {max_instr_id_except_cf}, index_first_bb_to_consider: {index_first_bb_to_consider}, index_first_instr_to_consider: {index_first_instr_to_consider}")
    if DO_ASSERT:
        assert max_bb_id_to_consider >= 0
        assert max_bb_id_to_consider < len(fuzzerstate.instr_objs_seq), f"Expected max_bb_id_to_consider `{max_bb_id_to_consider}` <= len(fuzzerstate.instr_objs_seq) `{len(fuzzerstate.instr_objs_seq)}`"
        assert index_first_bb_to_consider >= 0
        assert index_first_bb_to_consider <= max_bb_id_to_consider or max_bb_id_to_consider == 0, f"index_first_bb_to_consider: `{index_first_bb_to_consider}`, max_bb_id_to_consider: `{max_bb_id_to_consider}`"

    if max_bb_id_to_consider == 0:
        return False
    if max_instr_id_except_cf is None:
        max_instr_id_except_cf = len(fuzzerstate.instr_objs_seq[max_bb_id_to_consider])

    if DO_ASSERT:
        if max_instr_id_except_cf is not None:
            assert max_instr_id_except_cf >= -1, f"Expected max_instr_id_except_cf `{max_instr_id_except_cf}` >= -1"  # if -1, then it means that we only want the CF instruction.
            assert max_instr_id_except_cf <= len(fuzzerstate.instr_objs_seq[max_bb_id_to_consider]), f"Expected `{max_instr_id_except_cf}` <= `{len(fuzzerstate.instr_objs_seq[max_bb_id_to_consider])}-1`"
        # Check that we do not remove beyond the buggy instruction
        if index_first_bb_to_consider == max_bb_id_to_consider and max_instr_id_except_cf is not None and index_first_instr_to_consider is not None:
            assert max_instr_id_except_cf+1 >= index_first_instr_to_consider, f"Expected max_instr_id_except_cf+1 `{max_instr_id_except_cf+1}` >= index_first_instr_to_consider `{index_first_instr_to_consider}`"
            assert index_first_instr_to_consider <= len(fuzzerstate.instr_objs_seq[index_first_bb_to_consider])-1, f"Expected `{index_first_instr_to_consider}` <= `{len(fuzzerstate.instr_objs_seq[index_first_bb_to_consider])-1}`"

    ###
    # Remove the last basic blocks
    ###

    # Copy the fuzzerstate. Maybe it is an overkill.
    test_fuzzerstate = deepcopy(fuzzerstate)
    del fuzzerstate # Just for safety. We will not need fuzzerstate anymore in this function

    test_fuzzerstate.intregpickstate.restore_state(test_fuzzerstate.saved_reg_states[max_bb_id_to_consider])
    if DO_ASSERT:
        if isinstance(test_fuzzerstate.instr_objs_seq[max_bb_id_to_consider][-1], JALInstruction):
            assert test_fuzzerstate.memsize <= 1 << 20, "The whole memory cannot be addressed with JAL."

    ###
    # Remove the last instructions in the last basic block
    ###

    # Pop intermediate instructions if required
    if max_instr_id_except_cf < len(test_fuzzerstate.instr_objs_seq[max_bb_id_to_consider]):
        curr_addr = test_fuzzerstate.bb_start_addr_seq[max_bb_id_to_consider] + (max_instr_id_except_cf+1) * 4 # NO_COMPRESSED
        test_fuzzerstate.instr_objs_seq[max_bb_id_to_consider][max_instr_id_except_cf+1] = JALInstruction("jal", 0, test_fuzzerstate.final_bb_base_addr-curr_addr)
    else:
        curr_addr = test_fuzzerstate.bb_start_addr_seq[max_bb_id_to_consider] + (len(test_fuzzerstate.instr_objs_seq[max_bb_id_to_consider])-1) * 4 # NO_COMPRESSED
        test_fuzzerstate.instr_objs_seq[max_bb_id_to_consider][-1] = JALInstruction("jal", 0, test_fuzzerstate.final_bb_base_addr-curr_addr)

    ###
    # Remove the first basic blocks and instructions
    ###

    if index_first_bb_to_consider > 1 or index_first_instr_to_consider > 0:
        # First, we must record the context in the end of the last removed bb and after the correct number of instructions in that bb
        # storenumbytes is a list which, for each store operation, returns the number of bytes stored
        test_fuzzerstate = _save_ctx_and_jump_to_pillar_specific_instr(test_fuzzerstate, index_first_bb_to_consider, index_first_instr_to_consider)

        spikereduce_elfpath = gen_elf_from_bbs(test_fuzzerstate, False, "spikereduce_reducedstart", f"{test_fuzzerstate.instance_to_str()}_{max_bb_id_to_consider}_{max_instr_id_except_cf}_{index_first_bb_to_consider}_{index_first_instr_to_consider}", SPIKE_STARTADDR)
    else:
        spikereduce_elfpath = gen_elf_from_bbs(test_fuzzerstate, False, "spikereduce", f"{test_fuzzerstate.instance_to_str()}_{max_bb_id_to_consider}_{max_instr_id_except_cf}_{index_first_bb_to_consider}_{index_first_instr_to_consider}", SPIKE_STARTADDR)

    ###
    # Generate the ELF for RTL
    ###

    regdump_reqs = gen_regdump_reqs_reduced(test_fuzzerstate, max_bb_id_to_consider, max_instr_id_except_cf+1, index_first_bb_to_consider, index_first_instr_to_consider)

    # This is only needed for generating the final reg and freg values iirc.
    _, (finalintregvals_spikeresol, finalfloatregvals_spikeresol) = run_trace_regs_at_pc_locs(test_fuzzerstate.instance_to_str(), spikereduce_elfpath, get_design_march_flags_nocompressed(test_fuzzerstate.design_name), SPIKE_STARTADDR, regdump_reqs, True, test_fuzzerstate.final_bb_base_addr+SPIKE_STARTADDR, test_fuzzerstate.num_pickable_floating_regs if test_fuzzerstate.design_has_fpu else 0, test_fuzzerstate.design_has_fpud)

    rtl_elfpath = spikereduce_elfpath

    # To reduce the timeout duration, we compute the (approx) expected number of instructions
    numinstrs = len(test_fuzzerstate.final_bb)
    for bb in test_fuzzerstate.instr_objs_seq[:max_bb_id_to_consider+1]:
        numinstrs += len(bb)

    return test_fuzzerstate, rtl_elfpath, (finalintregvals_spikeresol[1:], finalfloatregvals_spikeresol), numinstrs

# This module resolves a mismatch between design and simulation by finding the first basic block that causes a mismatch.
# @param failing_instr_id the index of the first instruction in the bb `failing_bb_id` that causes trouble, in the sense that when it is removed (and all the following instructions and bbs), the test case does not fail anymore. It is None if the failing instruction is actually the last one in the previous bb. Only used in the second step.
# @param index_first_bb_to_consider: only used in the second step
def is_mismatch(fuzzerstate, max_bb_id_to_consider: int, failing_instr_id: int = None, index_first_bb_to_consider: int = 1, index_first_instr_to_consider: int = 0, quiet: bool = False):
    # try:
    test_fuzzerstate, rtl_elfpath, expected_regvals_pair, numinstrs = gen_reduced_elf(fuzzerstate, max_bb_id_to_consider, failing_instr_id, index_first_bb_to_consider, index_first_instr_to_consider)
    # except Exception as e:
    #     print(f"Error when generating reduced elf: `{e}`, for tuple: ({fuzzerstate.memsize}, design_name, {fuzzerstate.randseed}, {fuzzerstate.nmax_bbs})")
    #     raise Exception(e)
    if NO_REMOVE_TMPFILES:
        print(f"Generated RTL elf: {rtl_elfpath}")

    del fuzzerstate
    is_success, rtl_msg = runtest_simulator(test_fuzzerstate, rtl_elfpath, expected_regvals_pair, numinstrs, REDUCTION_SIMULATOR)

    if quiet and not is_success:
        print(rtl_msg)
    return not is_success

# Flattens the control flow except for the initial block, the context setter and the final block.
def _try_flatten_cf(fuzzerstate):
    flat_fuzzerstate = deepcopy(fuzzerstate)
    orig_fuzzerstate = fuzzerstate # Renaming to prevent accidental use of fuzzerstate
    del fuzzerstate

    # At this stage, we can increase the size of the memory, in case it was quite small. Be careful because it is a bit a hack.
    flat_fuzzerstate.memsize = max(flat_fuzzerstate.memsize, 2**20)
    flat_fuzzerstate.memview.memsize = max(flat_fuzzerstate.memview.memsize, 2**20)

    # num_flat_instrs: number of instructions in blocks, minus the cf instructions between them (fuzzerstate.instr_objs_seq - 2) + 1 for the final cf to the final block
    num_flat_instrs = sum(map(len, flat_fuzzerstate.instr_objs_seq[1:])) - len(flat_fuzzerstate.instr_objs_seq) + 2
    addr_flat_instrs = flat_fuzzerstate.memview.gen_random_free_addr(2, 4*num_flat_instrs, 0, flat_fuzzerstate.memsize)

    new_flat_instrs = []
    for bb in flat_fuzzerstate.instr_objs_seq[1:]:
        new_flat_instrs += bb[:-1]
    # Jump to the final block
    new_flat_instrs.append(JALInstruction("jal", 0, flat_fuzzerstate.final_bb_base_addr - 4*(len(new_flat_instrs)) - addr_flat_instrs))

    if DO_ASSERT:
        assert num_flat_instrs == len(new_flat_instrs), f"num_flat_instrs={num_flat_instrs} != len(new_flat_instrs)={len(new_flat_instrs)}"

    flat_fuzzerstate.instr_objs_seq = [flat_fuzzerstate.instr_objs_seq[0], new_flat_instrs]
    flat_fuzzerstate.bb_start_addr_seq = [flat_fuzzerstate.bb_start_addr_seq[0], addr_flat_instrs]
    # flat_fuzzerstate.instr_objs_seq[-1][-1] = JALInstruction("jal", 0, flat_fuzzerstate.bb_start_addr_seq[1] - 4*(len(flat_fuzzerstate.instr_objs_seq[0])-1))
    # print('Base addr guessed', hex(flat_fuzzerstate.ctxsv_bb_base_addr + 4*flat_fuzzerstate.ctxsv_bb_jal_instr_id))
    # print('Tgt addr', hex(flat_fuzzerstate.bb_start_addr_seq[1]))
    flat_fuzzerstate.ctxsv_bb[flat_fuzzerstate.ctxsv_bb_jal_instr_id] = JALInstruction("jal", 0, flat_fuzzerstate.bb_start_addr_seq[1] - (flat_fuzzerstate.ctxsv_bb_base_addr + 4*flat_fuzzerstate.ctxsv_bb_jal_instr_id))

    is_flattening_success = is_mismatch(flat_fuzzerstate, 1)

    if is_flattening_success:
        fuzzerstate = flat_fuzzerstate
    else:
        fuzzerstate = orig_fuzzerstate
    return fuzzerstate, is_flattening_success


# Returns the index of the first bb that fails.
# hint_left_bound_bb: when the bb with id `hint_left_bound_bb` is removed and all the subsequent bbs are removed, the bug should disappear.
# hint_right_bound_bb: when the bb with id `hint_right_bound_bb` is removed and all the subsequent bbs are removed, the bug should still be here.
# @return failing_bb_id is the index of the first bb that, when removed as well as the subsequent ones, makes the bug disappear.
def _find_failing_bb(fuzzerstate, hint_left_bound_bb: int = None, hint_right_bound_bb: int = None):
    # Take the hints
    if hint_left_bound_bb is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert not is_mismatch(fuzzerstate, hint_left_bound_bb), f"Wrong left bound hint `{hint_left_bound_bb}`."
            assert not is_mismatch(fuzzerstate, hint_left_bound_bb), f"Wrong left bound hint `{hint_left_bound_bb}`."
        left_bound = hint_left_bound_bb
    else:
        left_bound = 0
    if hint_right_bound_bb is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert is_mismatch(fuzzerstate, hint_right_bound_bb), f"Wrong right bound hint `{hint_right_bound_bb}`."
            assert is_mismatch(fuzzerstate, hint_right_bound_bb), f"Wrong right bound hint `{hint_right_bound_bb}`."
        right_bound = hint_right_bound_bb
    else:
        right_bound = len(fuzzerstate.instr_objs_seq)

    # Binary search
    # Invariant:
    #   is_mismatch(fuzzerstate, left_bound)  always False
    #   is_mismatch(fuzzerstate, right_bound) always True
    while right_bound - left_bound > 1:
        if DO_ASSERT:
            assert right_bound > left_bound
        candidate_bound = (right_bound + left_bound) // 2
        if is_mismatch(fuzzerstate, candidate_bound):
            print(candidate_bound, 'bb mismatch')
            right_bound = candidate_bound
        else:
            print(candidate_bound, 'bb match')
            left_bound = candidate_bound

    if DO_ASSERT:
        assert left_bound + 1 == right_bound

    # Now,
    #   left_bound  contains the max bb chain size that is still ok.
    #   right_bound contains the min bb chain size that is wrong.

    return right_bound

# @param failing_bb_id is the index of the first bb that, when removed as well as the subsequent ones, makes the bug disappear.
# @param failing_instr_id is the index of the first instruction in the bb `failing_bb_id` that causes trouble, in the sense that when it is removed (and all the following instructions and bbs), the test case does not fail anymore. It is None if the failing instruction is actually the last one in the previous bb.
# @param pillar_bb_id is the index of the last bb such as the test case still succeeds when the bb `pillar_bb_id` is removed (and all the preceding instructions and bbs).
def _find_pillar_bb(fuzzerstate, failing_bb_id: int, failing_instr_id: int, fault_from_prev_bb: bool, hint_left_bound_pillar_bb: int = None, hint_right_bound_pillar_bb: int = None):
    if DO_ASSERT:
        assert failing_bb_id > 0, f"In _find_pillar_bb, we assume that the initial block does not fail."
        assert failing_bb_id < len(fuzzerstate.instr_objs_seq)

    # Take the hints. Invariants: left bound always ok, right bound always wrong.
    if hint_left_bound_pillar_bb is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert not is_mismatch(fuzzerstate, failing_bb_id, hint_left_bound_pillar_bb), f"Wrong left bound hint `{hint_left_bound_pillar_bb}`."
            assert is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, hint_left_bound_pillar_bb), f"Wrong left bound hint `{hint_left_bound_pillar_bb}`."
        left_bound = hint_left_bound_pillar_bb
    else:
        left_bound = 0
    if hint_right_bound_pillar_bb is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert is_mismatch(fuzzerstate, failing_bb_id, hint_right_bound_pillar_bb), f"Wrong right bound hint `{hint_right_bound_pillar_bb}`."
            assert not is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, hint_right_bound_pillar_bb), f"Wrong right bound hint `{hint_right_bound_pillar_bb}`."
        right_bound = hint_right_bound_pillar_bb
    else:
        right_bound = failing_bb_id + 1

    if DO_ASSERT:
        assert right_bound <= failing_bb_id + 1, f"right_bound: `{right_bound}`, failing_bb_id: `{failing_bb_id}`"

    # Binary search
    # Invariant:
    #   is_mismatch(fuzzerstate, left_bound)  always False
    #   is_mismatch(fuzzerstate, right_bound) always True
    while right_bound - left_bound > 1:
        if DO_ASSERT:
            assert right_bound > left_bound
        candidate_bound = (right_bound + left_bound) // 2
        if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, candidate_bound):
            print(candidate_bound, 'pillar bb mismatch')
            left_bound = candidate_bound
        else:
            print(candidate_bound, 'pillar bb match')
            right_bound = candidate_bound

    if DO_ASSERT:
        assert left_bound + 1 == right_bound

    # Now,
    #   left_bound  contains the max bb chain size that is still ok.
    #   right_bound contains the min bb chain size that is wrong.

    return right_bound-1


# @param failing_bb_id is the index of the first bb that, when removed as well as the subsequent ones, makes the bug disappear.
# @return failing_instr_id is the index of the first instruction in the bb `failing_bb_id` that causes trouble, in the sense that when it is removed (and all the following instructions and bbs), the test case does not fail anymore. It is None if the failing instruction is actually the last one in the previous bb.
def _find_failing_instr_in_bb(fuzzerstate, failing_bb_id: int, hint_left_bound_instr: int = None, hint_right_bound_instr: int = None):
    if DO_ASSERT:
        assert failing_bb_id > 0
        assert failing_bb_id < len(fuzzerstate.instr_objs_seq)
        assert hint_left_bound_instr is None or hint_left_bound_instr >= 0, f"Got left bound hint `{hint_left_bound_instr}`."
        assert hint_right_bound_instr is None or hint_right_bound_instr <= len(fuzzerstate.instr_objs_seq[failing_bb_id]), f"Got right bound hint `{hint_right_bound_instr}, expected no more than {len(fuzzerstate.instr_objs_seq[failing_bb_id])}`."

    if len(fuzzerstate.instr_objs_seq[failing_bb_id]) == 1:
        return None

    # Take the hints
    if hint_left_bound_instr is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert not is_mismatch(fuzzerstate, failing_bb_id, hint_left_bound_instr), f"Wrong left bound hint `{hint_left_bound_instr}`."
            assert not is_mismatch(fuzzerstate, failing_bb_id, hint_left_bound_instr), f"Wrong left bound hint `{hint_left_bound_instr}`."
        left_bound = hint_left_bound_instr
    else:
        left_bound = 0
    if hint_right_bound_instr is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert is_mismatch(fuzzerstate, failing_bb_id, hint_right_bound_instr), f"Wrong right bound hint `{hint_right_bound_instr}`."
            assert is_mismatch(fuzzerstate, failing_bb_id, hint_right_bound_instr), f"Wrong right bound hint `{hint_right_bound_instr}`."
        right_bound = hint_right_bound_instr
    else:
        right_bound = len(fuzzerstate.instr_objs_seq[failing_bb_id])-1 # -1 because cannot be the last instruction of the bb (falls into the case where we look back for the previous bb)

    # Check whether the issue actually comes from the cf instruction from the previous bb.
    if right_bound == 0 or is_mismatch(fuzzerstate, failing_bb_id, 0):
        print('Issue comes from the previous bb')
        return None

    # Binary search
    # Invariant:
    #   is_mismatch(fuzzerstate, failing_bb_id, left_bound)  always False
    #   is_mismatch(fuzzerstate, failing_bb_id, right_bound) always True
    while right_bound - left_bound > 1:
        if DO_ASSERT:
            assert right_bound > left_bound
        candidate_bound = (right_bound + left_bound) // 2
        if is_mismatch(fuzzerstate, failing_bb_id, candidate_bound):
            print(candidate_bound, 'instr mismatch')
            right_bound = candidate_bound
        else:
            print(candidate_bound, 'instr match')
            left_bound = candidate_bound

    if DO_ASSERT:
        assert left_bound + 1 == right_bound, f"{left_bound}, {right_bound}"

    # print('is_mismatch(fuzzerstate, failing_bb_id, left_bound)', is_mismatch(fuzzerstate, failing_bb_id, right_bound-1))
    # print('is_mismatch(fuzzerstate, failing_bb_id, right_bound)', is_mismatch(fuzzerstate, failing_bb_id, right_bound))

    return right_bound

# @param failing_bb_id is the index of the first bb that, when removed as well as the subsequent ones, makes the bug disappear.
# @param failing_instr_id is the index of the first instruction in the bb `failing_bb_id` that causes trouble, in the sense that when it is removed (and all the following instructions and bbs), the test case does not fail anymore. It is None if the failing instruction is actually the last one in the previous bb.
# @return similarly to find_pillar_bb: returns the index of the first instruction in first_pillar_bb that, when removed, makes the bug disappear.
def _find_pillar_instr(fuzzerstate, failing_bb_id: int, failing_instr_id: int, pillar_bb_id: int, fault_from_prev_bb: bool, hint_left_pillar_instr: int = None, hint_right_pillar_instr: int = None):
    if DO_ASSERT:
        assert pillar_bb_id <= failing_bb_id + 1

    # Take the hints
    if hint_left_pillar_instr is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert not is_mismatch(fuzzerstate, failing_bb_id, hint_left_pillar_instr), f"Wrong left bound hint `{hint_left_pillar_instr}`."
            assert is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, hint_left_pillar_instr), f"Wrong left bound hint `{hint_left_pillar_instr}`."
        left_bound = hint_left_pillar_instr
    else:
        left_bound = 0
    if hint_right_pillar_instr is not None:
        if DO_ASSERT:
            # assert True # For safety, we uncomment sanity check for user input: assert is_mismatch(fuzzerstate, failing_bb_id, hint_right_pillar_instr), f"Wrong right bound hint `{hint_right_pillar_instr}`."
            assert not is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, hint_right_pillar_instr), f"Wrong right bound hint `{hint_right_pillar_instr}`."
        right_bound = hint_right_pillar_instr
    else:
        if pillar_bb_id == failing_bb_id:
            print('pillar_bb_id == failing_bb_id', pillar_bb_id, failing_bb_id)
            right_bound = failing_instr_id+1
        else:
            print('pillar_bb_id != failing_bb_id', pillar_bb_id, failing_bb_id)
            right_bound = len(fuzzerstate.instr_objs_seq[pillar_bb_id])

    if right_bound == left_bound:
        return right_bound

    if DO_ASSERT:
        assert right_bound > left_bound

    # Binary search
    # Invariant:
    #   is_mismatch(fuzzerstate, failing_bb_id, left_bound)  always False
    #   is_mismatch(fuzzerstate, failing_bb_id, right_bound) always True

    while right_bound - left_bound > 1:
        if DO_ASSERT:
            assert right_bound > left_bound
        candidate_bound = (right_bound + left_bound) // 2
        if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, candidate_bound):
            print(candidate_bound, 'pillar instr mismatch')
            left_bound = candidate_bound
        else:
            print(candidate_bound, 'pillar instr match')
            right_bound = candidate_bound

    if DO_ASSERT:
        assert left_bound + 1 == right_bound, f"{left_bound}, {right_bound}"

    return right_bound-1

# @param failing_bb_id is the index of the first bb that, when removed as well as the subsequent ones, makes the bug disappear.
# @param failing_instr_id is the index of the first instruction in the bb `failing_bb_id` that causes trouble, in the sense that when it is removed (and all the following instructions and bbs), the test case does not fail anymore. It is None if the failing instruction is actually the last one in the previous bb.
# Transforms unused instructions between the first pillar and the faulty instruction into nops.
def _turn_sandwich_instructions_into_nops(fuzzerstate, failing_bb_id: int, failing_instr_id: int, pillar_bb_id: int, pillar_instr: int, fault_from_prev_bb: bool):
    if DO_ASSERT:
        assert pillar_bb_id <= failing_bb_id+1
    
    if pillar_bb_id == failing_bb_id and failing_instr_id == pillar_instr:
        return fuzzerstate

    if DO_ASSERT:
        assert is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr)
        assert not is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr+1)

    if pillar_bb_id == failing_bb_id:
        raise NotImplementedError('Check the case where pillar_bb_id == failing_bb_id')
        for instr_id in range(pillar_instr, failing_instr_id+1):
            # Save the instruction before trying to turn it into a nop
            saved_instr = fuzzerstate.instr_objs_seq[failing_bb_id][instr_id]
            fuzzerstate.instr_objs_seq[failing_bb_id][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit)
            # For debug printing
            curr_addr = fuzzerstate.bb_start_addr_seq[failing_bb_id] + 4*instr_id # NO_COMPRESSED
            try:
                if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr):
                    print(f"(D) Addr {hex(curr_addr)}: Substituted with a nop.")
                else:
                    # If this nop substitution killed the mismatch, then we must keep this instruction as normal.
                    fuzzerstate.instr_objs_seq[failing_bb_id][instr_id] = saved_instr
                    print(f"(D) Addr {hex(curr_addr)}: Not substituted instruction with a nop.")
            except:
                # Possibly, the substitution killed the spike emulation, for example by changing a non-taken branch into a taken branch.
                fuzzerstate.instr_objs_seq[failing_bb_id][instr_id] = saved_instr
                print(f"(D) Addr {hex(curr_addr)}: Not substituted instruction with a nop (spike simulation died).")


    else:
        for instr_id in range(pillar_instr, len(fuzzerstate.instr_objs_seq[pillar_bb_id])-1):
            saved_instr = fuzzerstate.instr_objs_seq[pillar_bb_id][instr_id]
            # If this is already a nop, then pass
            fuzzerstate.instr_objs_seq[pillar_bb_id][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit)
            # For debug printing
            curr_addr = fuzzerstate.bb_start_addr_seq[pillar_bb_id] + 4*instr_id # NO_COMPRESSED
            try:
                if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr):
                    print(f"(A) Addr {hex(curr_addr)}: Substituted with a nop.")
                else:
                    # If this nop substitution killed the mismatch, then we must keep this instruction as normal.
                    fuzzerstate.instr_objs_seq[pillar_bb_id][instr_id] = saved_instr
                    print(f"(A) Addr {hex(curr_addr)}: Not substituted instruction with a nop.")
            except:
                # Possibly, the substitution killed the spike emulation, for example by changing a non-taken branch into a taken branch.
                fuzzerstate.instr_objs_seq[pillar_bb_id][instr_id] = saved_instr
                print(f"(A) Addr {hex(curr_addr)}: Not substituted instruction with a nop (spike simulation died).")
                exit(0)


        for bb_id in range(pillar_bb_id, failing_bb_id):
            # For each intermediate bb, first start by turning all instructions into nops (except the last one)
            coarse_saved_instrs = [copy(fuzzerstate.instr_objs_seq[bb_id][instr_id]) for instr_id in range(len(fuzzerstate.instr_objs_seq[bb_id])-1)]
            for instr_id in range(len(fuzzerstate.instr_objs_seq[bb_id])-1):
                fuzzerstate.instr_objs_seq[bb_id][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit)

                try:
                    if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr):
                        print(f"(B) BB {hex(fuzzerstate.bb_start_addr_seq[bb_id])}: Coarse grain nop substitution success.")
                        continue
                    print(f"(B) BB {hex(fuzzerstate.bb_start_addr_seq[bb_id])}: Coarse grain failure, falling back to fine grain nop substitution.")
                except:
                    print(f"(B) BB {hex(fuzzerstate.bb_start_addr_seq[bb_id])}: Coarse grain failure, falling back to fine grain nop substitution (spike simulation died).")

                # In case the coarse grain substitution did not work, try fine grain substitution on each instruction
                # If this nop substitution killed the mismatch, then we must keep this instruction as normal.
                fuzzerstate.instr_objs_seq[bb_id][instr_id] = saved_instr

                for instr_id in range(len(fuzzerstate.instr_objs_seq[bb_id])-1):
                    fuzzerstate.instr_objs_seq[bb_id][instr_id] = coarse_saved_instrs[instr_id]
                del coarse_saved_instrs

                for instr_id in range(len(fuzzerstate.instr_objs_seq[bb_id])-1):
                    saved_instr = copy(fuzzerstate.instr_objs_seq[bb_id][instr_id])
                    fuzzerstate.instr_objs_seq[bb_id][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit)
                    # For debug printing
                    curr_addr = fuzzerstate.bb_start_addr_seq[bb_id] + 4*instr_id # NO_COMPRESSED
                    try:
                        if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr):
                            print(f"(B) Addr {hex(curr_addr)}: Substituted with a nop.")
                        else:
                            # If this nop substitution killed the mismatch, then we must keep this instruction as normal.
                            fuzzerstate.instr_objs_seq[bb_id][instr_id] = saved_instr
                            print(f"(B) Addr {hex(curr_addr)}: Not substituted instruction with a nop.")
                    except:
                        # Possibly, the substitution killed the spike emulation, for example by changing a non-taken branch into a taken branch.
                        fuzzerstate.instr_objs_seq[bb_id][instr_id] = saved_instr
                        print(f"(B) Addr {hex(curr_addr)}: Not substituted instruction with a nop (spike simulation died).")

        for instr_id in range(failing_instr_id+1):
            saved_instr = fuzzerstate.instr_objs_seq[failing_bb_id][instr_id]
            fuzzerstate.instr_objs_seq[failing_bb_id][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit)
            # For debug printing
            curr_addr = fuzzerstate.bb_start_addr_seq[failing_bb_id] + 4*instr_id # NO_COMPRESSED
            try:
                if is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr):
                    print(f"(C) Addr {hex(curr_addr)}: Substituted with a nop.")
                else:
                    # If this nop substitution killed the mismatch, then we must keep this instruction as normal.
                    fuzzerstate.instr_objs_seq[failing_bb_id][instr_id] = saved_instr
                    print(f"(C) Addr {hex(curr_addr)}: Not substituted instruction with a nop.")
            except:
                # Possibly, the substitution killed the spike emulation, for example by changing a non-taken branch into a taken branch.
                fuzzerstate.instr_objs_seq[failing_bb_id][instr_id] = saved_instr
                print(f"(C) Addr {hex(curr_addr)}: Not substituted instruction with a nop (spike simulation died).")


    return fuzzerstate

# This is the main function in this file.
# First finds the problematic basic block.
# Second, finds the problematic instruction.
# Third, reduce some first basic blocks that are not involved in the problem.
# Fourth, reduce some initial instructions in the first problematic bb.
# @param target_dir: If not None, the directory where to save the generated files. Else, will be saved in the design's directory
# @param find_pillars: If false, the front of the test case will not be reduced.
# @return a boolean indicating whether the reduction was successful, a float measuring the elapesd time (in seconds), and the number of instructions in the test case.
def reduce_program(memsize: int, design_name: str, randseed: int, nmax_bbs: int, authorize_privileges: bool, find_pillars: bool, quiet: bool = False, target_dir: str = None, hint_left_bound_bb: int = None, hint_right_bound_bb: int = None, hint_left_bound_instr: int = None, hint_right_bound_instr: int = None, hint_left_bound_pillar_bb: int = None, hint_right_bound_pillar_bb: int = None, hint_left_bound_pillar_instr: int = None, hint_right_bound_pillar_instr: int = None, check_pc_spike_again: bool = False):
    from cascade.fuzzerstate import FuzzerState

    ###
    # Prepare the basic blocks
    ###

    if DO_ASSERT:
        assert nmax_bbs is None or nmax_bbs > 0

    start_time = time.time()

    random.seed(randseed)
    fuzzerstate = FuzzerState(get_design_boot_addr(design_name), design_name, memsize, randseed, nmax_bbs, authorize_privileges)

    gen_basicblocks(fuzzerstate)
    numinstrs = sum([len(bb) for bb in fuzzerstate.instr_objs_seq])

    # spike resolution
    expected_regvals = spike_resolution(fuzzerstate, check_pc_spike_again)

    if len(fuzzerstate.instr_objs_seq) == 1:
        print('Only one basic block. Trivial case.')
        print('Is mismatch', is_mismatch(fuzzerstate, 1, len(fuzzerstate.instr_objs_seq[0])-1))
        return True, time.time() - start_time, numinstrs

    # Try to replace all FPU enable/disable instructions with nops, to make the FPU dumping possible.
    for block_id, instr_id in fuzzerstate.fpuendis_coords:
        if block_id >= len(fuzzerstate.instr_objs_seq):
            continue
        if DO_ASSERT:
            assert 'csr' in fuzzerstate.instr_objs_seq[block_id][instr_id].instr_str, f"Block id {block_id}, instr id {instr_id} was not a csr instruction but was {fuzzerstate.instr_objs_seq[block_id][instr_id].instr_str}"
        fuzzerstate.instr_objs_seq[block_id][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit)

    ###
    # Find the first bb that causes trouble.
    ###

    # failing_bb_id is the index of the first basic block that causes trouble, in the sense that when it is removed (and all the following ones), the test case does not fail anymore.
    failing_bb_id = _find_failing_bb(fuzzerstate, hint_left_bound_bb, hint_right_bound_bb)

    # If fail even just with the initial block
    if failing_bb_id == 0:
        if is_mismatch(fuzzerstate, 1, len(fuzzerstate.instr_objs_seq[0])-1):
            if not quiet:
                print('Failure takes already place in the initial basic block. Copying the initial basic block.')
            test_fuzzerstate_larger, rtl_elfpath_larger, expected_regvals_pairs_larger, numinstrs = gen_reduced_elf(fuzzerstate, failing_bb_id, len(fuzzerstate.instr_objs_seq[0])-1)
            if target_dir is None:
                target_dir = os.path.join(get_design_cascade_path(design_name), 'sw', 'fuzzsample')
            if not quiet:
                Path(target_dir).mkdir(parents=True, exist_ok=True)
                shutil.copyfile(rtl_elfpath_larger, os.path.join(target_dir, 'app_buggy.elf'))
                subprocess.run(' '.join([f"riscv{os.environ['CASCADE_RISCV_BITWIDTH']}-unknown-elf-objdump", '-D', '--disassembler-options=numeric,no-aliases', os.path.join(target_dir, 'app_buggy.elf'), '>', os.path.join(target_dir, 'app_buggy.elf.dump')]), shell=True)
            return True, time.time() - start_time, numinstrs

    # If no fail at all
    if failing_bb_id == len(fuzzerstate.instr_objs_seq) and not is_mismatch(fuzzerstate, failing_bb_id-1):
        if not quiet:
            print(f"Success (no failure at all with tuple: ({memsize}, {design_name}, {randseed}, {nmax_bbs}, {authorize_privileges}))")
        return True, time.time() - start_time, numinstrs

    ###
    # Find the specific problematic instruction in the bb.
    ###

    # failing_instr_id is the index of the first instruction in the bb `failing_bb_id` that causes trouble, in the sense that when it is removed (and all the following instructions and bbs), the test case does not fail anymore.
    # It is None if the failing instruction is actually the last one in the previous bb.
    failing_instr_id = _find_failing_instr_in_bb(fuzzerstate, failing_bb_id, hint_left_bound_instr, hint_right_bound_instr)

    # Regularize the case where the faulty instruction was a cf instruction at the end of a bb.
    # If the fault comes from the prev bb, by definition we keep failing_bb_id untouched, and we set failing_instr_id to -1.
    fault_from_prev_bb = False
    if failing_instr_id is None:
        fault_from_prev_bb = True

        # If this is due to an interaction between the last CF instruction and the first instruction of the failing_bb_id, we may want to have failing_instr_id=0
        failing_instr_id = -1
        if not is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id):
            print('Detected interaction between CF instruction and the next block instruction')
            failing_instr_id = 0
            assert is_mismatch(fuzzerstate, failing_bb_id, failing_instr_id)
        # failing_bb_id = failing_bb_id-1
        # failing_instr_id = len(fuzzerstate.instr_objs_seq[failing_bb_id])

    ###
    # Cut the first bbs until the problem disappears.
    ###

    # pillar_bb_id: the index of the last bb such as the test case still succeeds when the bb `pillar_bb_id` is removed (and all the preceding instructions and bbs).
    # We have as an invariane: pillar_bb_id <= failing_bb_id
    if find_pillars:
        pillar_bb_id = _find_pillar_bb(fuzzerstate, failing_bb_id, failing_instr_id, fault_from_prev_bb, hint_left_bound_pillar_bb, hint_right_bound_pillar_bb)
    else:
        pillar_bb_id = 1

    ###
    # Cut the first instructions of the first pillar bb.
    ###

    if find_pillars:
        pillar_instr = _find_pillar_instr(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, fault_from_prev_bb, hint_left_bound_pillar_instr, hint_right_bound_pillar_instr)
    else:
        pillar_instr = 0

    ###
    # Some debug printing.
    ###

    if not quiet:
        print(f"Failing bb id                    : {failing_bb_id}")
        print(f"Failing instrs in bb excluding cf: {failing_instr_id}/{len(fuzzerstate.instr_objs_seq[failing_bb_id])}")
        if find_pillars:
            print(f"Pillar bb                        : {pillar_bb_id}")
            print(f"Pillar instr                     : {pillar_instr}/{len(fuzzerstate.instr_objs_seq[pillar_bb_id])}")

    ###
    # Transform some instructions into nops.
    ###

    if find_pillars and NOPIZE_SANDWICH_INSTRUCTIONS:
        # The advantage of doing this before the reduction of the ELF size is that we may successfully remove some load instructions targeting the instructions we will remove. The downside is that it is slower than cleaning up after the reduction.
        fuzzerstate = _turn_sandwich_instructions_into_nops(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr, fault_from_prev_bb)

    # Not mature code.
    # if find_pillars:
    #     if not quiet:
    #         # Instructions in the pillar bb
    #         if pillar_bb_id == failing_bb_id:
    #             for instr_id in range(pillar_instr, failing_instr_id+1):
    #                 curr_addr = fuzzerstate.bb_start_addr_seq[pillar_bb_id] + 4*instr_id # NO_COMPRESSED
    #                 if not quiet:
    #                     print('Problematic PC:', hex(curr_addr+SPIKE_STARTADDR))
    #         # If there are multiple bbs involved
    #         else:
    #             for instr_id in range(pillar_instr, len(fuzzerstate.instr_objs_seq[pillar_bb_id])):
    #                 curr_addr = fuzzerstate.bb_start_addr_seq[pillar_bb_id] + 4*instr_id # NO_COMPRESSED
    #                 if not quiet:
    #                     print('(A) Problematic PC:', hex(curr_addr+SPIKE_STARTADDR))
    #             for bb_id in range(pillar_bb_id, failing_bb_id):
    #                 for instr_id in range(len(fuzzerstate.instr_objs_seq[bb_id])):
    #                     curr_addr = fuzzerstate.bb_start_addr_seq[bb_id] + 4*instr_id # NO_COMPRESSED
    #                     if not quiet:
    #                         print('(B) Problematic PC:', hex(curr_addr+SPIKE_STARTADDR))
    #             for instr_id in range(failing_instr_id+1):
    #                 curr_addr = fuzzerstate.bb_start_addr_seq[failing_bb_id] + 4*instr_id # NO_COMPRESSED
    #                 if not quiet:
    #                     print('(C) Problematic PC:', hex(curr_addr+SPIKE_STARTADDR))

    # Not mature code.
    if FLATTEN_SANDWICH_INSTRUCTIONS and not pillar_bb_id == failing_bb_id:
        if not quiet:
            print('Flattening the control flow.')
        try:
            fuzzerstate, is_success_flattening = _try_flatten_cf(fuzzerstate)
        except Exception as e:
            print(f"Exception while flattening the control flow: {e}")
            is_success_flattening = False
        # Warning: Flattening cf outdates the indices of problematic and pillar instructions.
        if not quiet:
            print('is_success_flattening', is_success_flattening)

        if is_success_flattening:
            failing_bb_id = 1
            pillar_bb_id = 2
            fault_from_prev_bb = False

            failing_instr_id = _find_failing_instr_in_bb(fuzzerstate, failing_bb_id)
            pillar_instr = _find_pillar_instr(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, fault_from_prev_bb)
            # Remove the instructions after and before
            fuzzerstate.instr_objs_seq[-1] = fuzzerstate.instr_objs_seq[-1][:failing_instr_id+2]
            fuzzerstate.ctxsv_bb[fuzzerstate.ctxsv_bb_jal_instr_id] = JALInstruction("jal", 0, fuzzerstate.bb_start_addr_seq[1] + 4*(pillar_instr) - (fuzzerstate.ctxsv_bb_base_addr + 4*fuzzerstate.ctxsv_bb_jal_instr_id))
            for instr_id in range(pillar_instr):
                fuzzerstate.instr_objs_seq[1][instr_id] = RegImmInstruction("addi", 0, 0, 0, is_design_64bit=fuzzerstate.is_design_64bit) # RawDataWord(0)

            # We can do this one more time
            fuzzerstate = _turn_sandwich_instructions_into_nops(fuzzerstate, failing_bb_id, failing_instr_id, pillar_bb_id, pillar_instr, fault_from_prev_bb)

    if fault_from_prev_bb:
        # If the fault came from the previous bb, there are 2 possibilities:
        # 1. The fault came from the last instruction of the previous bb alone.
        # 2. The fault came from the last instruction of the previous bb and the first instruction of the failing bb.
        # In the first case, failing_instr_id = -1. In the second, failing_instr_id = 0.
        # Actually, all becomes perfectly regular in the 'larger' case, if I'm not mistaken.
        test_fuzzerstate_larger, rtl_elfpath_larger, expected_regvals_pairs_larger, numinstrs_larger = gen_reduced_elf(fuzzerstate, failing_bb_id, failing_instr_id)
    else:
        test_fuzzerstate_larger, rtl_elfpath_larger, expected_regvals_pairs_larger, numinstrs_larger = gen_reduced_elf(fuzzerstate, failing_bb_id, failing_instr_id)
        print(f"Larger: failing_bb_id: {failing_bb_id}, failing_instr_id: {failing_instr_id}, numinstrs_larger: {numinstrs_larger}")
        print(f"Larger ELF: {rtl_elfpath_larger}")

    if failing_instr_id == -1 and fault_from_prev_bb:
        ret = gen_reduced_elf(fuzzerstate, failing_bb_id-1)
        if ret is False:
            test_fuzzerstate_smaller, rtl_elfpath_smaller, expected_regvals_pairs_smaller, numinstrs_smaller = itertools.repeat(None, 4)
            print('Warning: smaller is trivial. Error may come from initial block.')
            return True, time.time() - start_time, numinstrs
        else:
            test_fuzzerstate_smaller, rtl_elfpath_smaller, expected_regvals_pairs_smaller, numinstrs_smaller = ret
    else:
        test_fuzzerstate_smaller, rtl_elfpath_smaller, expected_regvals_pairs_smaller, numinstrs_smaller = gen_reduced_elf(fuzzerstate, failing_bb_id, failing_instr_id-1)
        print(f"Smaller: failing_bb_id: {failing_bb_id}, failing_instr_id: {failing_instr_id-1}, numinstrs_smaller: {numinstrs_smaller}")
        print(f"Smaller ELF: {rtl_elfpath_smaller}")


    is_success_larger, rtl_msg_larger = runtest_simulator(test_fuzzerstate_larger, rtl_elfpath_larger, expected_regvals_pairs_larger, numinstrs_smaller)
    if not quiet:
        print('Success larger:', 0, is_success_larger)
        print('larger msg:', rtl_msg_larger)
    is_success_smaller, rtl_msg_smaller = runtest_simulator(test_fuzzerstate_smaller, rtl_elfpath_smaller, expected_regvals_pairs_smaller, numinstrs_larger)
    if not quiet:
        print('Success smaller:', 0, is_success_smaller)
        print('smaller msg:', rtl_msg_smaller)

    if not (is_success_smaller and not is_success_larger):
        print('Reduction did not totally succeed.')

    if target_dir is None:
        target_dir = os.path.join(get_design_cascade_path(design_name), 'sw', 'fuzzsample')
    if not quiet:
        print('Copying both ELFs')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(rtl_elfpath_larger, os.path.join(target_dir, 'app_buggy.elf'))
        subprocess.run(' '.join([f"riscv{os.environ['CASCADE_RISCV_BITWIDTH']}-unknown-elf-objdump", '-D', '--disassembler-options=numeric,no-aliases', os.path.join(target_dir, 'app_buggy.elf'), '>', os.path.join(target_dir, 'app_buggy.elf.dump')]), shell=True)
        shutil.copyfile(rtl_elfpath_smaller, os.path.join(target_dir, 'app_ok.elf'))
        subprocess.run(' '.join([f"riscv{os.environ['CASCADE_RISCV_BITWIDTH']}-unknown-elf-objdump", '-D', '--disassembler-options=numeric,no-aliases', os.path.join(target_dir, 'app_ok.elf'), '>', os.path.join(target_dir, 'app_ok.elf.dump')]), shell=True)
    # Write the error message
    with open(os.path.join(target_dir, 'err.log'), 'w') as f:
        f.write(rtl_msg_larger)

    return is_success_smaller and not is_success_larger, time.time() - start_time, numinstrs
