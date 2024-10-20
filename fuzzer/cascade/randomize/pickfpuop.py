# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module is responsible for picking floating-point operations

from params.runparams import DO_ASSERT
from rv.csrids import CSR_IDS
from params.fuzzparams import FPU_ENDIS_REGISTER_ID
from cascade.privilegestate import PrivilegeStateEnum
from cascade.cfinstructionclasses import CSRRegInstruction, RegImmInstruction
import random

ROUNDING_MODES = [0, 1, 2, 3, 4] # The non-reserved ones

def __pick_rounding_mode():
    import random
    return random.sample(ROUNDING_MODES, 1)[0]

def create_rmswitch_instrobjs(fuzzerstate):
    # Check that the FPU exists and is activated
    if DO_ASSERT:
        assert fuzzerstate.design_has_fpu
        assert fuzzerstate.is_fpu_activated
    # Put a random (valid) value to rm
    new_rm = __pick_rounding_mode()
    rinterm = fuzzerstate.intregpickstate.pick_int_inputreg_nonzero()
    # rd = fuzzerstate.intregpickstate.pick_int_outputreg() # Can be equal to rinterm
    rd = 0 # FUTURE WARL
    # Either through the frm CSR, or through the fcsr register
    use_frm_csr = random.randint(0, 1)
    if use_frm_csr:
        return [
            # Put the rounding mode to rinterm, and unset the flag bits
            RegImmInstruction("addi", rinterm, 0, new_rm, fuzzerstate.is_design_64bit),
            CSRRegInstruction("csrrw", rd, rinterm, CSR_IDS.FRM)
        ]
    else:
        return [
            # Put the rounding mode to rinterm, and unset the flag bits
            RegImmInstruction("addi", rinterm, 0, new_rm << 5, fuzzerstate.is_design_64bit),
            CSRRegInstruction("csrrw", rd, rinterm, CSR_IDS.FCSR)
        ]


# @return a list of instrobjs
def gen_fpufsm_instrs(fuzzerstate):
    if DO_ASSERT:
        assert fuzzerstate.design_has_fpu
        assert fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE

    ret = []
    if random.random() < fuzzerstate.proba_turn_on_off_fpu_again:
        rd = 0 # FUTURE WARL
        if fuzzerstate.is_fpu_activated:
            ret = [CSRRegInstruction("csrrs", rd, FPU_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS)]
        else:
            ret = [CSRRegInstruction("csrrc", rd, FPU_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS)]

    # If the FPU is off, then we turn the FPU on.
    elif fuzzerstate.is_fpu_activated:
        # Else, we arbitrate randomly between changing the rounding mode and turning off the FPU
        do_change_rounding_mode = random.random() < fuzzerstate.proba_change_rm
        if do_change_rounding_mode:
            ret = create_rmswitch_instrobjs(fuzzerstate)
        else:
            fuzzerstate.is_fpu_activated = False
            rd = 0 # Do not read the value because for triaging we want to be ablw to remove these instructions
            ret = [CSRRegInstruction("csrrc", rd, FPU_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS)]
    else:
        rd = 0 # WARL
        fuzzerstate.is_fpu_activated = True
        ret = [CSRRegInstruction("csrrs", rd, FPU_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS)]
    
    if len(ret) == 1: # Equivalent to FPU enable/disable
        fuzzerstate.add_fpu_coord()
    return ret 
