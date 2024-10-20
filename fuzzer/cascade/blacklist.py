# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module is responsible for blacklisting addresses, aka strong allocations.

from cascade.cfinstructionclasses import BranchInstruction, PlaceholderProducerInstr0, PlaceholderProducerInstr1, PlaceholderConsumerInstr

# Blacklisting is typically used for forbidding loads from loading instructions 
# that will change between spike resolution and RTL sim.

# All functions whose bytecode depends on the is_spike_resolution boolean
INSTRUCTION_TYPES_TO_BLACKLIST = [
    BranchInstruction,
    PlaceholderProducerInstr0,
    PlaceholderProducerInstr1,
    PlaceholderConsumerInstr
]

# Blacklist addresses where instructions change between spike resolution and RTL sim.
def blacklist_changing_instructions(fuzzerstate):
    # The first two instructions set up the relocator reg and may change betweend spike and rtl.
    fuzzerstate.memview_blacklist.alloc_mem_range(fuzzerstate.bb_start_addr_seq[0], 8) # NO_COMPRESSED

    # Find specific instruction types to blacklist
    for bb_id, bb_instrlist in enumerate(fuzzerstate.instr_objs_seq):
        for bb_instr_id, bb_instr in enumerate(bb_instrlist):
            for instr_type_to_blacklist in INSTRUCTION_TYPES_TO_BLACKLIST:
                if isinstance(bb_instr, instr_type_to_blacklist):
                    curr_addr = fuzzerstate.bb_start_addr_seq[bb_id] + bb_instr_id * 4 # NO_COMPRESSED
                    fuzzerstate.memview_blacklist.alloc_mem_range(curr_addr, 4)
                    break
    
    # Blacklist the last instruction of the initial block because we may steer it 
    # into other blocks (typically to the context setter before steering the control 
    # flow to a later bb, skipping some first ones).
    last_instr_addr = fuzzerstate.bb_start_addr_seq[0] + (len(fuzzerstate.instr_objs_seq[0]) - 1) * 4
    fuzzerstate.memview_blacklist.alloc_mem_range(last_instr_addr, 4) # NO_COMPRESSED

# Blacklist addresses where instructions change between spike resolution and RTL sim.
def blacklist_final_block(fuzzerstate):
    fuzzerstate.memview_blacklist.alloc_mem_range(fuzzerstate.final_bb_base_addr, len(fuzzerstate.final_bb) * 4) # NO_COMPRESSED

# Blacklist addresses where instructions change between spike resolution and RTL sim.
def blacklist_context_setter(fuzzerstate):
    fuzzerstate.memview_blacklist.alloc_mem_range(fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.ctxsv_size_upperbound) # NO_COMPRESSED
