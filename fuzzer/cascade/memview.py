# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script defines the memory allocation.

# For the moment, MemoryView is not designed to be thread-safe.
# MemoryView is a data structure that represents allocated and free memory.
# MemoryView is not yet designed to free any memory. Only more memory can be further allocated.

# A design assumption is that we will use the available memory very sparsely.

# Internally, MemoryView is implemented as a sorted iterable of pairs (free_start_addr, free_end_addr_plus_one)
# Internally, it offers the guarantee that if (a, b) and (c, d) are in the iterable in this order, then b < c (i.e., no superposition and no juxtaposition)

import random
# from params.runparams import DO_ASSERT
DO_ASSERT = True

MEMVIEW_ALLOC_MAX_ATTEMPTS = 1000

class MemoryView:
    # @param memsize should be at least 4, typically much higher. It is also typically a power of 2.
    def __init__(self, memsize: int):
        self.freepairs = [(0, memsize)]
        self.memsize = memsize
        self.occupied_addrs = 0 # Follow the number of occupied addresses.

    # In particular, returns False if it goes beyond the memory boundaries.
    def is_mem_free(self, addr: int):
        for curr_pair in self.freepairs:
            if addr < curr_pair[1]:
                return curr_pair[0] <= addr
        return False

    # @param start: first address of the range
    # @param end:   last address of the range, excluded
    # In particular, returns False if it goes beyond the memory boundaries.
    def is_mem_range_free(self, start: int, end: int):
        # Find the pair to which `start` belongs, and then check that `end` is still in the same pair.
        for curr_pair in self.freepairs:
            if start < curr_pair[1]:
                return start >= curr_pair[0] and end <= curr_pair[1]
        return False

    # @param addr: the current address
    # @return: the number of addresses, including addr, that are free until the next allocated address (or until the end of the memory).
    def get_available_contig_space(self, addr: int):
        # Find the pair to which `start` belongs, and then check that `end` is still in the same pair.
        for curr_pair in self.freepairs:
            if addr < curr_pair[1]:
                if (addr >= curr_pair[0]):
                    return curr_pair[1] - addr
                else:
                    return 0
        return 0

    # @param start:         first address of the range.
    # @param alloc_size:    size of the memory region to allocate, excluding the last adress
    def alloc_mem_range(self, start: int, alloc_size: int):
        end = start + alloc_size
        if DO_ASSERT:
            assert end > start, f"Expected start ({start}) > end ({end}) in alloc_mem_range."
        self.occupied_addrs += end-start
        for curr_pair_id, curr_pair in enumerate(self.freepairs):
            if start < curr_pair[1]:
                # Check that the range is initially free.
                if DO_ASSERT:
                    assert start >= curr_pair[0] and end <= curr_pair[1], "The memory range to allocate is not free."
                # Remove the tuple and replace it with at most two smaller tuples. This will automatically coalesce.
                if start == curr_pair[0] and end == curr_pair[1]:
                    self.freepairs = self.freepairs[:curr_pair_id] + self.freepairs[curr_pair_id+1:]
                    break
                elif start == curr_pair[0]:
                    self.freepairs = self.freepairs[:curr_pair_id] + [(end, curr_pair[1])] + self.freepairs[curr_pair_id+1:]
                    break
                elif end == curr_pair[1]:
                    self.freepairs = self.freepairs[:curr_pair_id] + [(curr_pair[0], start)] + self.freepairs[curr_pair_id+1:]
                    break
                else:
                    self.freepairs = self.freepairs[:curr_pair_id] + [(curr_pair[0], start)] + [(end, curr_pair[1])] + self.freepairs[curr_pair_id+1:]
                    break
        else:
            raise ValueError("Trying to allocate a memory range that was already not free.")
        # print(self.to_string())

    # @param store_instr_str: for example `sw`.
    # @param addr may be outside of memview
    def alloc_from_store_instruction(self, store_instr_str: str, addr: int):
        # Get the width from the opcode
        if store_instr_str == "sb":
            opwidth = 1
        elif store_instr_str == "sh":
            opwidth = 2
        elif store_instr_str in ("sw", "fsw"):
            opwidth = 4
        elif store_instr_str in ("sd", "fsd"):
            opwidth = 8
        else:
            raise ValueError(f"Unexpected store instruction string: `{store_instr_str}`")

        # Cap to the memory bounds
        left_bound = max(addr, 0) # Included
        right_bound = min(addr+opwidth, self.memsize) # Excluded

        if DO_ASSERT:
            assert left_bound <= right_bound

        if right_bound == left_bound:
            return
        self.alloc_mem_range(left_bound, right_bound)

    # @param alignment_bits: bits of alignment. For example, 0 for no specific alignment, 1 for 2-byte alignment, 2 for 4-byte, etc. 
    # @param min_space:      the minimal number of memory addresses that are free, starting from the returned address 
    # @param left_bound:     byte address. Included. May exceed memory bounds, in which case will be brought back to memory boundaries.
    # @param right_bound:    byte address. Excluded. May exceed memory bounds, in which case will be brought back to memory boundaries.
    # @param max_attempts:   max random attempts. After this number of unsuccessful attempts, the function will return None. Must be strictly positive.
    # @return None if no corresponding address was found in max_attempts. Else, return the address
    def gen_random_free_addr(self, alignment_bits: int, min_space: int, left_bound: int, right_bound: int, max_attempts: int = MEMVIEW_ALLOC_MAX_ATTEMPTS):
        left_bound  = max(left_bound, 0)
        right_bound = min(right_bound, self.memsize)
        if DO_ASSERT:
            assert max_attempts > 0
            assert min_space >= 0
            assert left_bound >= 0
            assert right_bound <= self.memsize
            assert left_bound < right_bound
            # The bounds must be sufficiently spaced. In our use case, this is not at all a problem.
            assert ((left_bound+(1 << alignment_bits)-1) >> alignment_bits) < ((right_bound-min_space) >> alignment_bits)

        for _ in range(max_attempts):
            picked_addr = random.randrange((left_bound+(1 << alignment_bits)-1) >> alignment_bits, ((right_bound-min_space) >> alignment_bits)) << alignment_bits
            if min_space == 0 or self.is_mem_range_free(picked_addr, picked_addr+min_space): # is_mem_range_free returns False if it goes beyond the memory boundaries.
                if DO_ASSERT:
                    assert picked_addr >= 0
                    assert picked_addr + min_space <= self.memsize
                    assert picked_addr % (1 << alignment_bits) == 0
                return picked_addr
        return None

    # @brief Computes the percentage of the memory that is allocated
    def get_allocated_ratio(self):
        free_sum = sum(map(lambda p: p[1] - p[0], self.freepairs))
        return (self.memsize - free_sum)/self.memsize

    def to_string(self):
        return str(self.freepairs)
