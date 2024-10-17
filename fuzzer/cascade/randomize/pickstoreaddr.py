# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# In this module, we propose the simple solution of pre-allocating data ranges before instruction generation starts.
# `Store locations` are 8-byte aligned, 8-byte size locations in memory.

from params.runparams import DO_ASSERT
from cascade.memview import MemoryView

import numpy as np
import random

ALIGNMENT_BITS_MAX = 3 # We support alignments 0, 1, 2 and 3 bits (i.e., we don't support quad RISC-V extensions)

class MemStoreState:
    # @param memview must be a fresh MemoryView. Is modified in place by allocating the store locations.
    def __init__(self):
        # Generate the store locations at random and allocate them
        self.store_locations = []

    # Should be called once the first basic block is already allocated
    def init_store_locations(self, num_store_locations: int, memview: MemoryView):
        for store_location_id in range(num_store_locations):
            next_store_location = memview.gen_random_free_addr(ALIGNMENT_BITS_MAX, 1 << ALIGNMENT_BITS_MAX, 0, memview.memsize)
            if next_store_location is None:
                raise ValueError(f"Could not find a next store location. You may want to increase the memory size (for the moment: {memview.memsize:,} B)")
            memview.alloc_mem_range(next_store_location, (1 << ALIGNMENT_BITS_MAX))
            self.store_locations.append(next_store_location)
            if DO_ASSERT:
                assert next_store_location >= 0
                assert next_store_location + (1 << ALIGNMENT_BITS_MAX) <= memview.memsize, ""
                assert next_store_location % (1 << ALIGNMENT_BITS_MAX) == 0
        self.location_weights = np.ones(num_store_locations)
        # Remember the last store operation address
        self.last_store_addr = self.store_locations[0]

    # Modifies the weights in place.
    # @param alignment_bits is equal to the requested size. This means we do not support misaligned mem reqs.
    # @return the picked location, in addition to updating the state.
    def pick_store_location(self, alignment_bits: int):
        if DO_ASSERT:
            assert alignment_bits >= 0
            assert alignment_bits <= ALIGNMENT_BITS_MAX

        # We first pick a store location. If the alignment is smaller than this size, then we choose uniformly inside the selected store location.
        picked_location_id = random.choices(range(len(self.store_locations)), self.location_weights)[0]
        picked_location = self.store_locations[picked_location_id]
        # Update the weights using a heuristic algorithm
        self.location_weights /= np.sum(self.location_weights)
        self.location_weights[picked_location_id] = 1

        if alignment_bits == ALIGNMENT_BITS_MAX:
            return picked_location
        else:
            # Choose uniformly a sub-location
            factor = 1 << (ALIGNMENT_BITS_MAX - alignment_bits)
            offset_in_location = random.randrange(factor) * (1 << alignment_bits)
            return picked_location + offset_in_location
