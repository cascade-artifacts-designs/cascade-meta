# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module defines the final block.

from params.runparams import DO_ASSERT
from rv.csrids import CSR_IDS
from common.designcfgs import is_design_32bit, get_design_stop_sig_addr, get_design_reg_dump_addr, design_has_float_support, design_has_double_support, get_design_fpreg_dump_addr
from params.fuzzparams import RDEP_MASK_REGISTER_ID, MAX_NUM_PICKABLE_REGS, MAX_NUM_PICKABLE_FLOATING_REGS, FPU_ENDIS_REGISTER_ID
from cascade.privilegestate import PrivilegeStateEnum
from rv.asmutil import li_into_reg
from cascade.cfinstructionclasses import ImmRdInstruction, RegImmInstruction, IntStoreInstruction, FloatStoreInstruction, JALInstruction, SpecialInstruction, CSRRegInstruction

def get_finalblock_max_size():
    return (10 + 2*MAX_NUM_PICKABLE_REGS + 2*MAX_NUM_PICKABLE_FLOATING_REGS - 1) * 4

# We must instantiate it in the end because we must know whether we have the privileges to turn on the FPU.
# Returns the instruction objects of the tail basic block
def finalblock(fuzzerstate, design_name: str):
    try:
        stopsig_addr = get_design_stop_sig_addr(design_name)
    except:
        raise ValueError(f"Design `{design_name}` does not have the `stopsigaddr` attribute.")
    try:
        regdump_addr = get_design_reg_dump_addr(design_name)
    except:
        raise ValueError(f"Design `{design_name}` does not have the `regdumpaddr` attribute.")

    if DO_ASSERT:
        assert regdump_addr < 0x80000000, f"For the destination address `{hex(regdump_addr)}`, we will need to manage sign extension, which is not yet implemented here."
        assert stopsig_addr < 0x80000000, f"For the destination address `{hex(stopsig_addr)}`, we will need to manage sign extension, which is not yet implemented here."

    ret = []
    is_design_64bit = not is_design_32bit(design_name)
    design_has_fpu = design_has_float_support(design_name)
    design_has_fpudouble = design_has_double_support(design_name)

    ###
    # Dump registers
    ###

    lui_imm_regdump, addi_imm_regdump = li_into_reg(regdump_addr)

    # We re-purpose RDEP_MASK_REGISTER_ID, because we will not need it anymore.
    # Compute the register dump address
    ret += [
        ImmRdInstruction("lui", RDEP_MASK_REGISTER_ID, lui_imm_regdump, is_design_64bit),
        RegImmInstruction("addi", RDEP_MASK_REGISTER_ID, RDEP_MASK_REGISTER_ID, addi_imm_regdump, is_design_64bit)
    ]

    # Store the register values to the register dump address
    ret.append(SpecialInstruction("fence")) # Hopefully this prevents speculative execution of the stores
    for reg_id in range(1, MAX_NUM_PICKABLE_REGS):
        ret.append(IntStoreInstruction("sd" if is_design_64bit else "sw", RDEP_MASK_REGISTER_ID, reg_id, 0, -1, is_design_64bit))
        ret.append(SpecialInstruction("fence"))

    # Store the floating values as well, if FPU is supported and if there is no risk of it being deactivated
    if design_has_fpu and not fuzzerstate.is_fpu_activated:
        # Check that the fpregdump addr is correctly positioned
        if DO_ASSERT:
            assert get_design_fpreg_dump_addr(design_name) == regdump_addr + 8, f"We make the assumption that the FP regdump addr is the int regdump address + 8. However, currently, they are respectively {hex(get_design_fpreg_dump_addr(design_name))} and regdump_addr={hex(regdump_addr)}"
        if fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE:
            # Enable the FPU
            ret.append(CSRRegInstruction("csrrw", 0, FPU_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS))
            fuzzerstate.is_fpu_activated = True
        if fuzzerstate.is_fpu_activated:
            for reg_id in range(MAX_NUM_PICKABLE_FLOATING_REGS):
                ret.append(FloatStoreInstruction("fsd" if design_has_fpudouble else "fsw", RDEP_MASK_REGISTER_ID, reg_id, 8, -1, is_design_64bit))
                ret.append(SpecialInstruction("fence"))

    ###
    # Stop request
    ###

    lui_imm_stopreq, addi_imm_stopreq = li_into_reg(stopsig_addr)

    # We re-purpose RDEP_MASK_REGISTER_ID, because we will not need it anymore.
    # Compute the stop request address
    ret += [
        ImmRdInstruction("lui", RDEP_MASK_REGISTER_ID, lui_imm_stopreq, is_design_64bit),
        RegImmInstruction("addi", RDEP_MASK_REGISTER_ID, RDEP_MASK_REGISTER_ID, addi_imm_stopreq, is_design_64bit)
    ]

    # Store the register values to the register dump address
    ret.append(IntStoreInstruction("sd" if is_design_64bit else "sw", RDEP_MASK_REGISTER_ID, 0, 0 & 0xFFFF, -1, is_design_64bit))
    ret.append(SpecialInstruction("fence"))

    # Infinite loop in the end of the simulation
    ret.append(JALInstruction("jal", 0, 0))

    if DO_ASSERT:
        assert len(ret) * 4 <= get_finalblock_max_size(), f"The final block is larger than expected: {len(ret) * 4} > {get_finalblock_max_size()}"

    return ret

# Spike does not support writing to some signaling addresses, but at the same time, we do not need it for spike resolution anyway. So let's replace it with an infinite loop.
def finalblock_spike_resolution():
    # Infinite loop in the end of the simulation
    return [JALInstruction("jal", 0, 0)]
