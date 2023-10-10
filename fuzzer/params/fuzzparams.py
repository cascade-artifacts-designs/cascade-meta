# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from enum import IntEnum, auto
import numpy as np

###
# Basic blocks
###

BLOCK_HEADER_RANDOM_DATA_BYTES = 12
RANDOM_DATA_BLOCK_MIN_SIZE_BYTES = 12
RANDOM_DATA_BLOCK_MAX_SIZE_BYTES = 64

###
# Branches
###

BRANCH_TAKEN_PROBA = 0.2 # Proba of a branch to be taken
NONTAKEN_BRANCH_INTO_RANDOM_DATA_PROBA = 0.9 # Proba of a branch to target the random data block if it is in range

###
# Memory operations
###

# Picking memory addresses

class MemaddrPickPolicy(IntEnum):
    MEM_ANY_STORELOC = auto() # proba weight to take any store location.
    MEM_ANY          = auto() # proba weight to take any register and any authorized address.

# Weights to choose the address of the next
MEMADDR_PICK_POLICY_WEIGTHS = {
    True: { # If it is a load
        MemaddrPickPolicy.MEM_ANY_STORELOC: 1,
        MemaddrPickPolicy.MEM_ANY:          1,
    },
    False: { # If it is a store
        MemaddrPickPolicy.MEM_ANY_STORELOC: 1,
        MemaddrPickPolicy.MEM_ANY:          0, # This must always be 0 for stores, because they can only be performed to specific locations.
    }
}

# Store locations
MAX_NUM_STORE_LOCATIONS = 30 # Max number of locations where doublewords can be stored.
MAX_NUM_FENCES_PER_EXECUTION = 10


###
# End condition
###

# Stop generating instructions when the memory saturation reaches this level.
# In other words, if the memory is occupied by more than this amount, then do not start generating new basic blocks.
LIMIT_MEM_SATURATION_RATIO = 0.8


###
# Register picking
###

# When a register is produced, it gets this probability to be picked next. What is nice is that it immediately saturates: producing it twice does not increase picking proba.
REGPICK_PROTUBERANCE_RATIO = 0.2 

# There should always be at least this number of free registers
NUM_MIN_FREE_INTREGS = 2

# Reduce the registers that we allow ourselves to pick randomly
MIN_NUM_PICKABLE_REGS = 4
MAX_NUM_PICKABLE_REGS = 25

MIN_NUM_PICKABLE_FLOATING_REGS = 1
MAX_NUM_PICKABLE_FLOATING_REGS = 14

RELOCATOR_REGISTER_ID = 31
RDEP_MASK_REGISTER_ID = 30 # The mask to limit the value of the dependent register at the consumer level
FPU_ENDIS_REGISTER_ID = 29 # The mask to enable or disable the FPU
MPP_BOTH_ENDIS_REGISTER_ID = 28 # The mask to switch both MPP bits
MPP_TOP_ENDIS_REGISTER_ID = 27 # The mask to switch only the top MPP bit. We cannot do it for the bottom, because we could not go to supervisor mode reliably on a design that does not have user mode.
SPP_ENDIS_REGISTER_ID = 26 # The mask to switch the (unique) SPP Bit

assert RELOCATOR_REGISTER_ID < 32
assert RDEP_MASK_REGISTER_ID < 32
assert FPU_ENDIS_REGISTER_ID < 32
assert MPP_BOTH_ENDIS_REGISTER_ID < 32
assert MPP_TOP_ENDIS_REGISTER_ID < 32
assert SPP_ENDIS_REGISTER_ID < 32

assert RELOCATOR_REGISTER_ID >= MAX_NUM_PICKABLE_REGS
assert RDEP_MASK_REGISTER_ID >= MAX_NUM_PICKABLE_REGS
assert FPU_ENDIS_REGISTER_ID >= MAX_NUM_PICKABLE_REGS
assert MPP_BOTH_ENDIS_REGISTER_ID >= MAX_NUM_PICKABLE_REGS
assert MPP_TOP_ENDIS_REGISTER_ID >= MAX_NUM_PICKABLE_REGS
assert SPP_ENDIS_REGISTER_ID >= MAX_NUM_PICKABLE_REGS


assert RDEP_MASK_REGISTER_ID != RELOCATOR_REGISTER_ID
# Check that they are all distinct
assert len({RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID}) == len([RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID])

###
# Register FSM
###

REG_FSM_WEIGHTS = np.array([
    1,  # FREE           -> PRODUCED0
    10, # PRODUCED0      -> PRODUCED1
    10, # PRODUCED1      -> FREE/CONSUMED
])

PROBA_CONSUME_PRODUCED1_SAME = 0.05 # The proba to output the same register as PRODUCED1 at the output of a CONSUME op

###
# Exceptions
###

SIMPLE_ILLEGAL_INSTRUCTION_PROBA = 0.01
PROBA_PICK_WRONG_FPU = 0.0 # Having this being zero eases the analysis of the program since we can try to simply remove all the FPU activations/deactivations to ensure that dumping is possible. More sophisticated methods could be implemented.
PROBA_AUTHORIZE_PRIVILEGES = 0.05

###
# Getters from the environment
###

def get_max_num_instructions_upperbound():
    # Return the MAX_NUM_INSTRUCTIONS_UPPERBOUND environment variable if it is defined, otherwise return None
    import os
    if 'MAX_NUM_INSTRUCTIONS_UPPERBOUND' in os.environ:
        return int(os.environ['MAX_NUM_INSTRUCTIONS_UPPERBOUND'])
    else:
        return None

def is_no_dependency_bias():
    # Return the MAX_NUM_INSTRUCTIONS_UPPERBOUND environment variable if it is defined, otherwise return None
    import os
    if 'CASCADE_NO_DEPENDENCY_BIAS' in os.environ:
        return bool(os.environ['CASCADE_NO_DEPENDENCY_BIAS'])
    else:
        return False
