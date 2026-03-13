# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module picks some random valid CSR operation.

import logging
logger = logging.getLogger(__name__)

from params.runparams import DO_ASSERT
from rv.csrids import CSR_IDS
from cascade.toleratebugs import is_no_interaction_minstret, is_tolerate_kronos_minstret, is_tolerate_vexriscv_minstret, is_tolerate_picorv32_missingmandatorycsrs, is_tolerate_picorv32_readnonimplcsr, is_tolerate_picorv32_writehpm, is_tolerate_cva6_mhpmcounter, is_tolerate_boom_minstret, is_tolerate_picorv32_readhpm_nocsrrs, is_tolerate_vexriscv_mhpmcountern, is_tolerate_cva6_mhpmevent31
from cascade.privilegestate import PrivilegeStateEnum
from cascade.cfinstructionclasses import CSRRegInstruction, CSRImmInstruction, RegImmInstruction
import random

from enum import Enum, auto

class MachineCSROpCandidates64(Enum):
    SCAUSE = auto()
    MCAUSE = auto()
    SSCRATCH = auto()
    MSCRATCH = auto()
    MINSTRET = auto()
    MHPMCOUNTER3 = auto()
    MHPMEVENT31 = auto()

class MachineCSROpCandidates32(Enum):
    SCAUSE = auto()
    MCAUSE = auto()
    SSCRATCH = auto()
    MSCRATCH = auto()
    MINSTRET = auto()

class SupervisorCSROpCandidates(Enum):
    SCAUSE = auto()
    SSCRATCH = auto()

# @brief Generate a privileged descent instruction or an mpp/spp write instruction.
# @return a list of instructions
def gen_random_csr_op(fuzzerstate):
    if DO_ASSERT:
        assert fuzzerstate.privilegestate.privstate in (PrivilegeStateEnum.MACHINE, PrivilegeStateEnum.SUPERVISOR)

    if fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE:
        if fuzzerstate.is_design_64bit:
            target_csr = None
            while target_csr is None or (target_csr == MachineCSROpCandidates64.MINSTRET and is_no_interaction_minstret(fuzzerstate.design_name)):
                target_csr = random.choice(list(MachineCSROpCandidates64))
            if not fuzzerstate.design_has_supervisor_mode:
                while target_csr in (MachineCSROpCandidates64.SCAUSE, MachineCSROpCandidates64.SSCRATCH):
                    target_csr = random.choice(list(MachineCSROpCandidates64))
            while 'cva6' in fuzzerstate.design_name and not is_tolerate_cva6_mhpmcounter() and not is_tolerate_cva6_mhpmevent31() and target_csr in (MachineCSROpCandidates64.MHPMCOUNTER3, MachineCSROpCandidates64.MHPMEVENT31):
                target_csr = random.choice(list(MachineCSROpCandidates64))

            if target_csr == MachineCSROpCandidates64.SCAUSE:
                # According to the spec, the SCAUSE CSR must be able to hold bits 0 to 4. mret is not required to.
                logger.warning(f"[pickrandomcsrop:55] Creating CSR instruction: csrrwi to SCAUSE (64-bit Machine)")
                ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(32), CSR_IDS.SCAUSE)
            elif target_csr == MachineCSROpCandidates64.MCAUSE:
                logger.warning(f"[pickrandomcsrop:61] Creating CSR instruction: csrrwi to MCAUSE (64-bit Machine)")
                ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(16), CSR_IDS.MCAUSE)
            elif target_csr == MachineCSROpCandidates64.SSCRATCH:
                    logger.warning(f"[pickrandomcsrop:64] Creating CSR instruction: csrrw to SSCRATCH (64-bit Machine)")
                    ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.SSCRATCH)
            elif target_csr == MachineCSROpCandidates64.MSCRATCH:
                    logger.warning(f"[pickrandomcsrop:67] Creating CSR instruction: csrrw to MSCRATCH (64-bit Machine)")
                    ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.MSCRATCH)
            elif target_csr == MachineCSROpCandidates64.MINSTRET:
                if fuzzerstate.is_minstret_inaccurate_because_ecall_ebreak or ("boom" in fuzzerstate.design_name and not is_tolerate_boom_minstret()):
                    logger.warning(f"[pickrandomcsrop:71] Creating CSR instruction: csrrwi to MINSTRET (64-bit Machine, inaccurate)")
                    ret = CSRImmInstruction("csrrwi", 0, random.randrange(16), CSR_IDS.MINSTRET)
                else:
                    logger.warning(f"[pickrandomcsrop:75] Creating CSR instruction: csrrw to MINSTRET (64-bit Machine)")
                    ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.MINSTRET)
                fuzzerstate.is_minstret_inaccurate_because_ecall_ebreak = False
            elif target_csr == MachineCSROpCandidates64.MHPMCOUNTER3:
                logger.warning(f"[pickrandomcsrop:78] Creating CSR instruction: csrrwi to MHPMCOUNTER3 (64-bit Machine)")
                ret = CSRImmInstruction("csrrwi", 0, random.randrange(16), CSR_IDS.MHPMCOUNTER3)
            elif target_csr == MachineCSROpCandidates64.MHPMEVENT31:
                logger.warning(f"[pickrandomcsrop:81] Creating CSR instruction: csrrwi to MHPMEVENT31 (64-bit Machine)")
                ret = CSRImmInstruction("csrrwi", 0, random.randrange(16), CSR_IDS.MHPMEVENT31)
            else:
                raise Exception("Unexpected target_csr: {}".format(target_csr))
        else:
            if "vexriscv" in fuzzerstate.design_name and is_tolerate_vexriscv_mhpmcountern():
                logger.warning(f"[pickrandomcsrop:87] Creating CSR instruction: csrrwi to MHPMCOUNTER3 (32-bit vexriscv)")
                return CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(16), CSR_IDS.MHPMCOUNTER3)
            elif "picorv32" in fuzzerstate.design_name and not is_tolerate_picorv32_missingmandatorycsrs() and not is_tolerate_picorv32_readnonimplcsr():
                assert not is_no_interaction_minstret(fuzzerstate.design_name), "picorv32 only has minstret in this config."
                target_csr = MachineCSROpCandidates32.MINSTRET
            else:
                target_csr = None
                while target_csr is None or (target_csr == MachineCSROpCandidates32.MINSTRET and is_no_interaction_minstret(fuzzerstate.design_name)) \
                    or (not fuzzerstate.design_has_supervisor_mode and (target_csr in (MachineCSROpCandidates32.SCAUSE, MachineCSROpCandidates32.SSCRATCH))):
                    target_csr = random.choice(list(MachineCSROpCandidates32))
            if target_csr == MachineCSROpCandidates32.SCAUSE:
                # According to the spec, the SCAUSE CSR must be able to hold bits 0 to 4. mret is not required to.
                if "vexriscv" in fuzzerstate.design_name: # vexriscv complies with the privileged spec v1.10, which does not require scause to hold the 5th bit. Similarly, kronos implements privileged spec v1.11
                    randval = random.randrange(16)
                    logger.warning(f"[pickrandomcsrop:91] Creating CSR instruction: csrrwi to SCAUSE (32-bit Machine, vexriscv)")
                    ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), randval, CSR_IDS.SCAUSE)
                else:
                    logger.warning(f"[pickrandomcsrop:104] Creating CSR instruction: csrrwi to SCAUSE (32-bit Machine)")
                    ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(32), CSR_IDS.SCAUSE)
            elif target_csr == MachineCSROpCandidates32.MCAUSE:
                logger.warning(f"[pickrandomcsrop:107] Creating CSR instruction: csrrwi to MCAUSE (32-bit Machine)")
                ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(16), CSR_IDS.MCAUSE)
            elif target_csr == MachineCSROpCandidates32.SSCRATCH:
                logger.warning(f"[pickrandomcsrop:109] Creating CSR instruction: csrrw to SSCRATCH (32-bit Machine)")
                ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.SSCRATCH)
            elif target_csr == MachineCSROpCandidates32.MSCRATCH:
                logger.warning(f"[pickrandomcsrop:113] Creating CSR instruction: csrrw to MSCRATCH (32-bit Machine)")
                ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.MSCRATCH)
            elif target_csr == MachineCSROpCandidates32.MINSTRET:
                if "kronos" in fuzzerstate.design_name and not is_tolerate_kronos_minstret() or "vexriscv" in fuzzerstate.design_name and not is_tolerate_vexriscv_minstret():
                    logger.warning(f"[pickrandomcsrop:117] Creating CSR instruction: csrrw to MINSTRET (32-bit Machine, kronos/vexriscv)")
                    ret = CSRRegInstruction("csrrw", 0, fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.MINSTRET)
                elif "picorv32" in fuzzerstate.design_name:
                    if is_tolerate_picorv32_readhpm_nocsrrs():
                        opcode_str = random.choice(("csrrw", "csrrs"))
                    else:
                        opcode_str = "csrrs"
                    if is_tolerate_picorv32_writehpm():
                        rs = fuzzerstate.intregpickstate.pick_int_inputreg()
                    else:
                        rs = 0
                    logger.warning(f"[pickrandomcsrop:128] Creating CSR instruction: {opcode_str} to MINSTRET (32-bit Machine, picorv32)")
                    ret = CSRRegInstruction(opcode_str, fuzzerstate.intregpickstate.pick_int_outputreg(), rs, CSR_IDS.MINSTRET)
                else:
                    logger.warning(f"[pickrandomcsrop:131] Creating CSR instruction: csrrw to MINSTRET (32-bit Machine)")
                    ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.MINSTRET)
            else:
                raise Exception("Unexpected target_csr: {}".format(target_csr))
    else:
        target_csr = random.choice(list(SupervisorCSROpCandidates))
        if target_csr == SupervisorCSROpCandidates.SCAUSE:
            if "vexriscv" in fuzzerstate.design_name: # vexriscv complies with the privileged spec v1.10, which does not require scause to hold the 5th bit. Similarly, kronos implements privileged spec v1.11
                logger.warning(f"[pickrandomcsrop:139] Creating CSR instruction: csrrwi to SCAUSE (Supervisor, vexriscv)")
                ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(16), CSR_IDS.SCAUSE)
            else:
                logger.warning(f"[pickrandomcsrop:142] Creating CSR instruction: csrrwi to SCAUSE (Supervisor)")
                ret = CSRImmInstruction("csrrwi", fuzzerstate.intregpickstate.pick_int_outputreg(), random.randrange(32), CSR_IDS.SCAUSE)
        elif target_csr == SupervisorCSROpCandidates.SSCRATCH:
            logger.warning(f"[pickrandomcsrop:145] Creating CSR instruction: csrrw to SSCRATCH (Supervisor)")
            ret = CSRRegInstruction("csrrw", fuzzerstate.intregpickstate.pick_int_outputreg(), fuzzerstate.intregpickstate.pick_int_inputreg(), CSR_IDS.SSCRATCH)
        else:
            raise Exception("Unexpected target_csr: {}".format(target_csr))
    return ret
