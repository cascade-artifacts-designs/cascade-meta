# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import DO_ASSERT
from cascade.util import ExceptionCauseVal, IntRegIndivState
from functools import reduce
from enum import IntEnum

class PrivilegeStateEnum(IntEnum):
    USER       = 0
    SUPERVISOR = 1
    HYPERVISOR = 2 # We do not support it atm, as no open source design implements it afawk to date.
    MACHINE    = 3

# Represents the privilege and MMU state, evolving during the fuzzing process
class PrivilegeState:
    def __init__(self):
        self.privstate = PrivilegeStateEnum.MACHINE

        # These values must be initialized because the corresponding [m/s]ret is executed.
        # The values are PrivilegeStateEnum values. We initialize them in the initial block.
        self.curr_mstatus_mpp = PrivilegeStateEnum.MACHINE
        self.curr_mstatus_spp = PrivilegeStateEnum.SUPERVISOR
        # self.curr_sstatus_spp = PrivilegeStateEnum.SUPERVISOR # Only used to support sret from machine mode

        # Says whether the trap vectors are populated with valid next blocks.
        self.is_mtvec_populated = False
        self.is_stvec_populated = False
        self.is_mepc_populated = False
        self.is_sepc_populated = False
        # We must ignore the reset value of some CSRs because it may be unspecified
        self.is_mtvec_still_reset_val = True
        self.is_stvec_still_reset_val = True
        self.is_mepc_still_reset_val = True
        self.is_sepc_still_reset_val = True

        # In the initial block, we populate medeleg with 0, so we don't have the problem described below, and never use the None value.
        # None means not yet populated. The initial value is then unpredictable.
        # Example: rocket 0xd08518, boom 0xf0b55d, while their max is 0xf0b55d. The other designs (cva6 and vexriscv) start with 0.
        self.medeleg_val = 0

    def gen_takable_exception_dict(self, fuzzerstate):
        supported_exceptions_dict = {
            ExceptionCauseVal.ID_INSTR_ADDR_MISALIGNED: True,
            ExceptionCauseVal.ID_ILLEGAL_INSTRUCTION: True,
            ExceptionCauseVal.ID_BREAKPOINT: True,
            ExceptionCauseVal.ID_LOAD_ADDR_MISALIGNED: True,
            ExceptionCauseVal.ID_STORE_AMO_ADDR_MISALIGNED: True,
            ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_U_MODE: True,
            ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_S_MODE: True,
            ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_M_MODE: True,
            ExceptionCauseVal.ID_INSTR_ACCESS_FAULT: False,
            ExceptionCauseVal.ID_LOAD_ACCESS_FAULT: False,
            ExceptionCauseVal.ID_INSTRUCTION_PAGE_FAULT: False,
            ExceptionCauseVal.ID_STORE_AMO_ACCESS_FAULT: False,
            ExceptionCauseVal.ID_LOAD_PAGE_FAULT: False,
            ExceptionCauseVal.ID_STORE_AMO_PAGE_FAULT: False
        }

        # Remove all entries with weight zero
        for exception_cause_val in list(supported_exceptions_dict.keys()):
            if fuzzerstate.exceptionoppickweights[exception_cause_val] == 0:
                supported_exceptions_dict[exception_cause_val] = False

        if fuzzerstate.design_has_misaligned_data_support:
            # If such data accesses are supported, then it will not result in an exception.
            # Additionally, we require some consumed register.
            supported_exceptions_dict[ExceptionCauseVal.ID_LOAD_ADDR_MISALIGNED] = False
            supported_exceptions_dict[ExceptionCauseVal.ID_STORE_AMO_ADDR_MISALIGNED] = False
        if fuzzerstate.design_has_compressed_support:
            supported_exceptions_dict[ExceptionCauseVal.ID_INSTR_ADDR_MISALIGNED] = False
        # Not yet supported
        supported_exceptions_dict[ExceptionCauseVal.ID_INSTRUCTION_PAGE_FAULT] = False
        supported_exceptions_dict[ExceptionCauseVal.ID_LOAD_PAGE_FAULT] = False
        supported_exceptions_dict[ExceptionCauseVal.ID_STORE_AMO_PAGE_FAULT] = False

        # Make sure there are consumed registers for some of the misaligned accesses
        has_consumed_reg = fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.CONSUMED)
        if not has_consumed_reg:
            supported_exceptions_dict[ExceptionCauseVal.ID_LOAD_ACCESS_FAULT] = False      # Not yet sure whether we will need a consumed reg, but let's do it like this for now
            supported_exceptions_dict[ExceptionCauseVal.ID_STORE_AMO_ACCESS_FAULT] = False # Not yet sure whether we will need a consumed reg, but let's do it like this for now
            supported_exceptions_dict[ExceptionCauseVal.ID_INSTRUCTION_PAGE_FAULT] = False # Not yet sure whether we will need a consumed reg, but let's do it like this for now
            supported_exceptions_dict[ExceptionCauseVal.ID_LOAD_PAGE_FAULT] = False        # Not yet sure whether we will need a consumed reg, but let's do it like this for now
            supported_exceptions_dict[ExceptionCauseVal.ID_STORE_AMO_PAGE_FAULT] = False   # Not yet sure whether we will need a consumed reg, but let's do it like this for now
            supported_exceptions_dict[ExceptionCauseVal.ID_LOAD_ADDR_MISALIGNED] = False
            supported_exceptions_dict[ExceptionCauseVal.ID_STORE_AMO_ADDR_MISALIGNED] = False


        if self.privstate == PrivilegeStateEnum.MACHINE:
            supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_S_MODE] = False
            supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_U_MODE] = False

            if not self.is_mtvec_populated:
                # Forbid all exceptions
                supported_exceptions_dict[ExceptionCauseVal.ID_INSTR_ADDR_MISALIGNED] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_INSTR_ACCESS_FAULT] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_ILLEGAL_INSTRUCTION] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_BREAKPOINT] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_LOAD_ADDR_MISALIGNED] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_STORE_AMO_ADDR_MISALIGNED] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_M_MODE] = False

            return supported_exceptions_dict
        else:
            if DO_ASSERT:
               assert self.medeleg_val is not None, "medeleg must be written at least once before taking an exception in non-machine mode (and generally before transitioning to any non-machine mode, because it is a machine-mode-only CSR), so we may not reliably come back up."

            if fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.SUPERVISOR:
                supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_M_MODE] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_U_MODE] = False
            elif fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.USER:
                supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_M_MODE] = False
                supported_exceptions_dict[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_S_MODE] = False

            # Now we check whether the corresponding mtvec/stvec is populated (depending on current privilege state and delegation)
            for exception_cause_val in list(supported_exceptions_dict.keys()):
                if fuzzerstate.privilegestate.privstate != PrivilegeStateEnum.MACHINE:
                    if DO_ASSERT:
                        assert fuzzerstate.privilegestate.medeleg_val is not None
                    if fuzzerstate.privilegestate.medeleg_val & (1 << exception_cause_val.value):
                        # Delegated to supervisor mode
                        if not fuzzerstate.privilegestate.is_stvec_populated:
                            supported_exceptions_dict[exception_cause_val] = False
                    else:
                        if not fuzzerstate.privilegestate.is_mtvec_populated:
                            supported_exceptions_dict[exception_cause_val] = False

            return supported_exceptions_dict

    def gen_takable_exception_mask(self, fuzzerstate):
        ret = 0
        for k, v in self.gen_takable_exception_dict(fuzzerstate).items():
            ret |= (v << k)
        return ret

    # FUTURE Add page faults and access faults here.
    def is_ready_to_take_exception(self, fuzzerstate):
        curr_dict = self.gen_takable_exception_dict(fuzzerstate)
        return reduce(lambda x, y: x | y, list(curr_dict.values()))

def is_ready_to_descend_privileges(fuzzerstate):
    if DO_ASSERT:
        assert fuzzerstate.privilegestate.medeleg_val is not None, "We don't expect medeleg to be None because we initialize it in the initial block."

    # For the moment, we only support descending privileges on designs that have all of M, S and U modes.
    if not fuzzerstate.authorize_privileges:
        return False

    if not fuzzerstate.design_has_supervisor_mode or not fuzzerstate.design_has_user_mode:
        return False

    if fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.USER:
        return False
    # If the current state is machine, then we can descend privileges only if we can come back.
    # - If we go to supervisor, only if mtvec is required.
    # - If we go to user, we require mtvec, and stvec if all exceptions are delegated.

    elif fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE:
        if not fuzzerstate.privilegestate.is_mepc_populated:
            return False
        if fuzzerstate.privilegestate.curr_mstatus_mpp == PrivilegeStateEnum.MACHINE \
            or fuzzerstate.privilegestate.curr_mstatus_mpp == PrivilegeStateEnum.SUPERVISOR:
            return fuzzerstate.privilegestate.is_mtvec_populated
    # The below for implementing sret in machine mode
    # elif fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE:
    #     if not fuzzerstate.privilegestate.is_mepc_populated and (not fuzzerstate.design_has_supervisor_mode or not fuzzerstate.privilegestate.is_sepc_populated):
    #         return False
    #     if fuzzerstate.privilegestate.curr_mstatus_mpp == PrivilegeStateEnum.MACHINE \
    #         or fuzzerstate.privilegestate.curr_mstatus_mpp == PrivilegeStateEnum.SUPERVISOR:
    #         return fuzzerstate.privilegestate.is_mtvec_populated
        else:
            return fuzzerstate.privilegestate.is_mtvec_populated and \
                (fuzzerstate.privilegestate.is_stvec_populated or ((~fuzzerstate.privilegestate.medeleg_val) & fuzzerstate.privilegestate.gen_takable_exception_mask(fuzzerstate)))
    # If the current state is supervisor, then we can descend privileges only if we can come back, i.e., same condition as from machine mode to user mode.
    elif fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.SUPERVISOR:
        if not fuzzerstate.privilegestate.is_sepc_populated:
            return False
        return fuzzerstate.privilegestate.is_mtvec_populated and \
            (fuzzerstate.privilegestate.is_stvec_populated or ((~fuzzerstate.privilegestate.medeleg_val) & fuzzerstate.privilegestate.gen_takable_exception_mask(fuzzerstate)))
    else:
        raise NotImplementedError("Unknown privilege state: " + str(fuzzerstate.privilegestate.privstat))
