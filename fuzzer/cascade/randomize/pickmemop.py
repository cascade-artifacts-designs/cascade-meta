# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module is responsible for choosing the memory operation addresses and address registers.

from params.runparams import DO_ASSERT
import random

from params.fuzzparams import MemaddrPickPolicy, MEMADDR_PICK_POLICY_WEIGTHS

# Helper function for the basic blocks
def is_instrstr_load(instr_str: str):
    return instr_str in ("lb", "lh", "lhu", "lw", "lwu", "flw", "ld", "fld", "lbu")

# Helper function for the basic blocks
def get_alignment_bits(instr_str: str):
    if instr_str in ("sb", "lb", "lbu"):
        return 0
    elif instr_str in ("sh", "lh", "lhu"):
        return 1
    elif instr_str in ("sw", "lw", "lwu", "flw", "fsw"):
        return 2
    elif instr_str in ("sd", "ld", "fld", "fsd"):
        return 3
    else:
        raise ValueError(f"Unexpected memory instruction string: `{instr_str}`")

# Does not update the memview of the fuzzerstate.
# @param is_curr_load: True if load, False if store
# @param alignment_bits: 0, 1, 2 or 3
# @return the address
def pick_memop_addr(fuzzerstate, is_curr_load: bool, alignment_bits: int):
    if DO_ASSERT:
        assert alignment_bits >= 0
        assert alignment_bits <= 3

    # Ensure we don't make a wrong choice
    curr_pick_type = None
    while curr_pick_type is None or MEMADDR_PICK_POLICY_WEIGTHS[is_curr_load][curr_pick_type] == 0:
        curr_pick_type = random.choices(list(MEMADDR_PICK_POLICY_WEIGTHS[is_curr_load].keys()), weights=MEMADDR_PICK_POLICY_WEIGTHS[is_curr_load].values())[0]

    if curr_pick_type == MemaddrPickPolicy.MEM_ANY_STORELOC:
        # Pick a store location
        ret_addr = fuzzerstate.memstorestate.pick_store_location(alignment_bits)
        if not is_curr_load:
            fuzzerstate.memstorestate.last_store_addr = ret_addr
        return ret_addr
    elif curr_pick_type == MemaddrPickPolicy.MEM_ANY:
        if DO_ASSERT:
            assert is_curr_load
        # Pick any location
        ret_addr = fuzzerstate.memview_blacklist.gen_random_free_addr(alignment_bits, 1 << alignment_bits, 0, fuzzerstate.memview_blacklist.memsize)
        if DO_ASSERT:
            assert ret_addr >= 0
            assert ret_addr + (1 << alignment_bits) < fuzzerstate.memsize
        return ret_addr
    else:
        raise NotImplementedError(f"Unimplemented MemaddrPickPolicy: `{curr_pick_type}`.")
