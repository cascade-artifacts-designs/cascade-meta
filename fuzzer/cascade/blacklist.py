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
    # Collect every 4-byte slot to blacklist into a set first so we can do
    # one alloc per unique address. memview_blacklist.alloc_mem_range asserts
    # that the range is free, so we cannot blanket-allocate a slot twice
    # when, e.g., a compressed slot is also the last instruction of the
    # initial block (handled below).
    addrs_to_blacklist = set()

    # The first two instructions set up the relocator reg and may change between spike and rtl.
    addrs_to_blacklist.add(fuzzerstate.bb_start_addr_seq[0])
    addrs_to_blacklist.add(fuzzerstate.bb_start_addr_seq[0] + 4)

    # Find specific instruction types to blacklist. Also blacklist any slot
    # marked iscompressed: in the RTL ELF such a slot is emitted as a packed
    # (compressed_instr | c.nop) pair, while in the spike-resolution ELF the
    # same slot is emitted as the full uncompressed 32-bit form
    # (see _emit_slot_bytecode in genelf.py). The two byte sequences differ,
    # so loads landing on these slots return divergent values between the two
    # runs — which in turn corrupts placeholder-consumer rdep values and can
    # produce, e.g., misaligned load addresses at runtime.
    for bb_id, bb_instrlist in enumerate(fuzzerstate.instr_objs_seq):
        for bb_instr_id, bb_instr in enumerate(bb_instrlist):
            should_blacklist = getattr(bb_instr, 'iscompressed', False) or any(
                isinstance(bb_instr, t) for t in INSTRUCTION_TYPES_TO_BLACKLIST
            )
            if should_blacklist:
                addrs_to_blacklist.add(fuzzerstate.bb_start_addr_seq[bb_id] + bb_instr_id * 4) # NO_COMPRESSED

    # Blacklist the last instruction of the initial block because we may steer it
    # into other blocks (typically to the context setter before steering the control
    # flow to a later bb, skipping some first ones).
    addrs_to_blacklist.add(fuzzerstate.bb_start_addr_seq[0] + (len(fuzzerstate.instr_objs_seq[0]) - 1) * 4) # NO_COMPRESSED

    for addr in addrs_to_blacklist:
        fuzzerstate.memview_blacklist.alloc_mem_range(addr, 4)

# Blacklist addresses where instructions change between spike resolution and RTL sim.
def blacklist_final_block(fuzzerstate):
    fuzzerstate.memview_blacklist.alloc_mem_range(fuzzerstate.final_bb_base_addr, len(fuzzerstate.final_bb) * 4) # NO_COMPRESSED

# Blacklist addresses where instructions change between spike resolution and RTL sim.
def blacklist_context_setter(fuzzerstate):
    fuzzerstate.memview_blacklist.alloc_mem_range(fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.ctxsv_size_upperbound) # NO_COMPRESSED
