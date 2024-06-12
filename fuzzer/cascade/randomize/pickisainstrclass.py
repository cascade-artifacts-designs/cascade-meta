# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import DO_ASSERT
from cascade.toleratebugs import is_tolerate_kronos_fence, is_tolerate_picorv32_fence, is_forbid_vexriscv_csrs, is_tolerate_picorv32_missingmandatorycsrs, is_tolerate_picorv32_readnonimplcsr, is_tolerate_picorv32_writehpm, is_tolerate_picorv32_readhpm_nocsrrs
from cascade.util import ISAInstrClass, IntRegIndivState
from params.fuzzparams import NUM_MIN_FREE_INTREGS, MAX_NUM_FENCES_PER_EXECUTION
from cascade.privilegestate import PrivilegeStateEnum, is_ready_to_descend_privileges
import random
from copy import copy

# This module helps picking an ISAInstrClass.
# This is the first step of generating a random instruction without a specific structure.

# Must not all be 0. Must be filtered according to the capabilities of the different CPUs.
ISAINSTRCLASS_INITIAL_BOOSTERS = {
    ISAInstrClass.REGFSM:      1,
    ISAInstrClass.FPUFSM:      0.1,
    ISAInstrClass.ALU:         0.1,
    ISAInstrClass.ALU64:       0.1,
    ISAInstrClass.MULDIV:      0.1,
    ISAInstrClass.MULDIV64:    0.1,
    ISAInstrClass.AMO:         0,
    ISAInstrClass.AMO64:       0,
    ISAInstrClass.JAL :        0.1,
    ISAInstrClass.JALR:        0.4,
    ISAInstrClass.BRANCH:      0.2,
    ISAInstrClass.MEM:         0.5,
    ISAInstrClass.MEM64:       0.5,
    ISAInstrClass.MEMFPU:      0.2,
    ISAInstrClass.FPU:         0.1,
    ISAInstrClass.FPU64:       0.1,
    ISAInstrClass.MEMFPUD:     0.2,
    ISAInstrClass.FPUD:        0.1,
    ISAInstrClass.FPUD64:      0.1,
    ISAInstrClass.TVECFSM:     0.05,
    ISAInstrClass.PPFSM:       0.01,
    ISAInstrClass.EPCFSM:      0.1,
    ISAInstrClass.MEDELEG:     0.1,
    ISAInstrClass.EXCEPTION:   0.1,
    ISAInstrClass.RANDOM_CSR:  0.01,
    ISAInstrClass.DESCEND_PRV: .01,
    ISAInstrClass.SPECIAL:     0.0001
}

###
# Helper functions
###

# @param weights a list either None (equal weights) or as long as ISAInstrClass
# return a ISAInstrClass
# Do NOT @cache this function, as it is a random function.
def _gen_next_isainstrclass_from_weights(weights: list = None) -> ISAInstrClass:
    ret = random.choices(list(weights.keys()), weights=weights.values())[0]
    assert weights[ret] != 0
    return ret

# @brief For now, the weights used for choosing instructions are fixed over time.
# This function filters the isainstrclass weights according to the capabilities of a given CPU
# FUTURE: Use coverage metrics or other kinds of scheduling.
# FUTURE: Use a Markov chain for executing floating point instructions in a row.
# @return a normalized dict of instruction classes supported by the CPU
# DO NOT @cache
def _get_isainstrclass_filtered_weights(fuzzerstate):
    if DO_ASSERT:
        assert fuzzerstate.design_has_fpu or not fuzzerstate.design_has_fpud, "Cannot have double but not simple precision"
    ret_dict = copy(fuzzerstate.isapickweights)
    if not fuzzerstate.is_design_64bit:
        ret_dict[ISAInstrClass.ALU64]    = 0
        ret_dict[ISAInstrClass.MULDIV64] = 0
        ret_dict[ISAInstrClass.AMO64]    = 0
        ret_dict[ISAInstrClass.MEM64]    = 0
        ret_dict[ISAInstrClass.FPU64]    = 0
        ret_dict[ISAInstrClass.FPUD64]   = 0
    if not fuzzerstate.design_has_fpu:
        ret_dict[ISAInstrClass.MEMFPU]   = 0
        ret_dict[ISAInstrClass.FPU]      = 0
        ret_dict[ISAInstrClass.FPU64]    = 0
        ret_dict[ISAInstrClass.MEMFPUD]  = 0
        ret_dict[ISAInstrClass.FPUD]     = 0
        ret_dict[ISAInstrClass.FPUD64]   = 0
        ret_dict[ISAInstrClass.FPUFSM]   = 0
    elif not fuzzerstate.is_fpu_activated:
        ret_dict[ISAInstrClass.MEMFPU]   = 0
        ret_dict[ISAInstrClass.FPU]      = 0
        ret_dict[ISAInstrClass.FPU64]    = 0
        ret_dict[ISAInstrClass.MEMFPUD]  = 0
        ret_dict[ISAInstrClass.FPUD]     = 0
        ret_dict[ISAInstrClass.FPUD64]   = 0
    if not fuzzerstate.design_has_fpud:
        ret_dict[ISAInstrClass.MEMFPUD] = 0
        ret_dict[ISAInstrClass.FPUD]    = 0
        ret_dict[ISAInstrClass.FPUD64]  = 0
    if not fuzzerstate.design_has_muldiv:
        ret_dict[ISAInstrClass.MULDIV]   = 0
        ret_dict[ISAInstrClass.MULDIV64] = 0
    if not fuzzerstate.design_has_amo:
        ret_dict[ISAInstrClass.AMO]   = 0
        ret_dict[ISAInstrClass.AMO64] = 0
    if not fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE:
        ret_dict[ISAInstrClass.FPUFSM] = 0
    if (not fuzzerstate.authorize_privileges) or not (fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE and fuzzerstate.design_has_supervisor_mode) \
        or "vexriscv" in fuzzerstate.design_name and is_forbid_vexriscv_csrs():
        # There is no notion of delegation if supervisor mode is not supported
        ret_dict[ISAInstrClass.MEDELEG] = 0
    # For now, do not populate the mtvec/stvec more than necessary
    if (not fuzzerstate.authorize_privileges) or not (fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE and not fuzzerstate.privilegestate.is_mtvec_populated) and not ((fuzzerstate.privilegestate.privstate in (PrivilegeStateEnum.MACHINE, PrivilegeStateEnum.SUPERVISOR)) and not fuzzerstate.privilegestate.is_stvec_populated and fuzzerstate.design_has_supervisor_mode) or \
        "picorv32" in fuzzerstate.design_name \
        or "vexriscv" in fuzzerstate.design_name and is_forbid_vexriscv_csrs():
        ret_dict[ISAInstrClass.TVECFSM] = 0
    # For now, do not populate the mepc/sepc more than necessary
    if (not fuzzerstate.authorize_privileges) or not ((fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE and not (fuzzerstate.privilegestate.is_mepc_populated or fuzzerstate.privilegestate.is_sepc_populated)) or \
        fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.SUPERVISOR and not fuzzerstate.privilegestate.is_sepc_populated) or \
        "picorv32" in fuzzerstate.design_name \
        or "vexriscv" in fuzzerstate.design_name and is_forbid_vexriscv_csrs():
        ret_dict[ISAInstrClass.EPCFSM] = 0
    # Do not descend privileges as long as medeleg is undefined because we have no way of certainly coming back up
    # However, this ISA class still encompasses setting mpp and spp bits, to we tolerate this ISA class at all times when executing as a non-user.
    if not is_ready_to_descend_privileges(fuzzerstate):
        ret_dict[ISAInstrClass.DESCEND_PRV] = 0
    # Decrease the proba if we know it will be a mpp/spp
    if (not fuzzerstate.authorize_privileges) or fuzzerstate.privilegestate.privstate != PrivilegeStateEnum.MACHINE or "picorv32" in fuzzerstate.design_name: # To support sret from machine mode: `not in (PrivilegeStateEnum.MACHINE, PrivilegeStateEnum.SUPERVISOR):`
        ret_dict[ISAInstrClass.PPFSM] = 0
    # No exception if no exception is possible
    if (not fuzzerstate.authorize_privileges) or not fuzzerstate.privilegestate.is_ready_to_take_exception(fuzzerstate) or "picorv32" in fuzzerstate.design_name:
        ret_dict[ISAInstrClass.EXCEPTION] = 0
    if not fuzzerstate.privilegestate.privstate in (PrivilegeStateEnum.MACHINE, PrivilegeStateEnum.SUPERVISOR) \
        or "vexriscv" in fuzzerstate.design_name and is_forbid_vexriscv_csrs() \
        or "picorv32" in fuzzerstate.design_name and not is_tolerate_picorv32_missingmandatorycsrs() and not is_tolerate_picorv32_readnonimplcsr() and not is_tolerate_picorv32_writehpm() and not is_tolerate_picorv32_readhpm_nocsrrs():
        ret_dict[ISAInstrClass.RANDOM_CSR] = 0
    if "kronos" in fuzzerstate.design_name and not is_tolerate_kronos_fence() \
        or "picorv32" in fuzzerstate.design_name and not is_tolerate_picorv32_fence() \
            or (MAX_NUM_FENCES_PER_EXECUTION is not None and fuzzerstate.special_instrs_count > MAX_NUM_FENCES_PER_EXECUTION):
        ret_dict[ISAInstrClass.SPECIAL] = 0

    # Normalize the weights
    if DO_ASSERT:
        assert sum(ret_dict.values()) > 0, "The sum of filtered isa pick weights must be strictly positive!"
    norm_factor = 1/sum(ret_dict.values())
    for curr_key in ret_dict:
        ret_dict[curr_key] = ret_dict[curr_key] * norm_factor

    return ret_dict

# Sets the REGFSM weight to 0 if no register can be produced, consumed or relocated
def _filter_regfsm_weight(fuzzerstate, filtered_weights: list):
    if fuzzerstate.intregpickstate.get_num_regs_in_state(IntRegIndivState.FREE) > NUM_MIN_FREE_INTREGS or \
            fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.PRODUCED0) or \
            fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.PRODUCED1):
            return

    filtered_weights[ISAInstrClass.REGFSM] = 0

# Filters out the sensitive instructions considering whether there are available registers in the suitable state
def _filter_sensitive_instr_weights(fuzzerstate, filtered_weights: list):
    if not fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.CONSUMED):
        filtered_weights[ISAInstrClass.JAL]     = 0
        # We use branches with two dependent registers, so we don't need CONSUMED registers.
        # filtered_weights[ISAInstrClass.BRANCH]  = 0
        filtered_weights[ISAInstrClass.MEDELEG] = 0
        filtered_weights[ISAInstrClass.TVECFSM] = 0
        filtered_weights[ISAInstrClass.EPCFSM]  = 0
        filtered_weights[ISAInstrClass.JALR]    = 0
        filtered_weights[ISAInstrClass.MEM]     = 0
        filtered_weights[ISAInstrClass.MEM64]   = 0
        filtered_weights[ISAInstrClass.MEMFPU]  = 0
        filtered_weights[ISAInstrClass.MEMFPUD] = 0

###
# Exposed function
###

# Do NOT @cache this function, as it is a random function.
def gen_next_isainstrclass(fuzzerstate) -> ISAInstrClass:
    filtered_weights = _get_isainstrclass_filtered_weights(fuzzerstate)
    _filter_regfsm_weight(fuzzerstate, filtered_weights)
    _filter_sensitive_instr_weights(fuzzerstate, filtered_weights)

    return _gen_next_isainstrclass_from_weights(filtered_weights)
