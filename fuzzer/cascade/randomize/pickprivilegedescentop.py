# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script is used to pick an instruction from the privileged descent instruction ISA class.

from params.runparams import DO_ASSERT
from cascade.privilegestate import PrivilegeStateEnum
from cascade.cfinstructionclasses import PrivilegeDescentInstruction

# @brief Generate a privileged descent instruction or an mpp/spp write instruction.
# @return a list of instructions
def gen_priv_descent_instr(fuzzerstate):
    if DO_ASSERT:
        if fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE:
            # Add `or fuzzerstate.privilegestate.is_sepc_populated` to implement sret in machine mode
            assert fuzzerstate.privilegestate.is_mepc_populated, "If we are in machine mode, then mepc or sepc should be populated if we want to descend privileges."
            assert fuzzerstate.privilegestate.curr_mstatus_mpp is not None, "mpp should be populated if we want to descend privileges from machine mode."
        else:
            assert fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.SUPERVISOR
            assert fuzzerstate.privilegestate.is_sepc_populated, "If we are in supervisor mode, then sepc should be populated if we want to descend privileges."
            assert fuzzerstate.privilegestate.curr_mstatus_spp is not None, "spp should be populated if we want to descend privileges from supervisor mode."

        is_mret = fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE

        # Invalidate the corresponding epc and update the current privilege level.
        # Do not update or invalidate mpp/spp bits.
        if is_mret:
            fuzzerstate.privilegestate.is_mepc_populated = False
            fuzzerstate.privilegestate.privstate = fuzzerstate.privilegestate.curr_mstatus_mpp
            fuzzerstate.privilegestate.curr_mstatus_mpp = PrivilegeStateEnum.USER
        else:
            fuzzerstate.privilegestate.is_sepc_populated = False
            fuzzerstate.privilegestate.privstate = fuzzerstate.privilegestate.curr_mstatus_spp
            fuzzerstate.privilegestate.curr_mstatus_spp = PrivilegeStateEnum.USER

        return PrivilegeDescentInstruction(is_mret)
