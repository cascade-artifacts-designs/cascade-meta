# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module is responsible for setting up the context for pruning the basic blocks and instructions happening before the faulty instruction.

from dataclasses import dataclass
from params.runparams import DO_ASSERT
from params.fuzzparams import MAX_NUM_PICKABLE_REGS, MPP_TOP_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID
from rv.csrids import CSR_IDS
from common.spike import SPIKE_STARTADDR
from cascade.privilegestate import PrivilegeStateEnum
from cascade.cfinstructionclasses import ImmRdInstruction, RegImmInstruction, IntLoadInstruction, IntStoreInstruction, FloatLoadInstruction, CSRRegInstruction, JALInstruction, RawDataWord, PrivilegeDescentInstruction
from cascade.randomize.pickstoreaddr import ALIGNMENT_BITS_MAX

# @brief This function computes an upper bound on the size of the context setter basic block.
# Do not functools.cache because it is cheap to compute, even though it is not expected to change during a fuzzing run.
def get_context_setter_max_size(fuzzerstate):
    # Static overhead: 20: Upper bound on the number of instructions needed to set up the context setter. Includes some margin.
    num_instrs_static = 20
    # Each CSR's overhead: 4: 3 instructions to set up fcsr, and 4 bytes (~1 instr) to store its value.
    num_instrs_csrs = 0
    num_instrs_csrs += 4 # fcsr
    num_instrs_csrs += 4 # mepc
    num_instrs_csrs += 4 # sepc
    num_instrs_csrs += 4 # mcause
    num_instrs_csrs += 4 # scause
    num_instrs_csrs += 4 # mscratch
    num_instrs_csrs += 4 # sscratch
    num_instrs_csrs += 4 # mtvec
    num_instrs_csrs += 4 # stvec
    num_instrs_csrs += 4 # medeleg
    num_instrs_csrs += 8 # mstatus  is a bit special and requires more instructions.
    num_instrs_csrs += 8 # minstret is a bit special and requires more instructions.
    num_instrs_reset_last_reg = 1 # Reset the register used as an offset (should not be necessary)
    # Privilege restoration overhead
    num_instr_privilege_restoration = 6
    # Memory restoration overhead: 4: 3 instructions + 4 bytes (~1 instr) to store the address where the byte will be stored. The number of bytes in a store location is defined as 1 << (ALIGNMENT_BITS_MAX)
    num_instrs_mem = 4 * fuzzerstate.num_store_locations * (1 << (ALIGNMENT_BITS_MAX))
    # Floating registers overhead: 4: 3 instructions + 4-8 bytes (~1-2 instrs) to store the data + 4 bytes to potentially align.
    if fuzzerstate.design_has_fpu:
        if fuzzerstate.design_has_fpud:
            num_instrs_freg = fuzzerstate.num_pickable_floating_regs*4
        else:
            num_instrs_freg = 1+fuzzerstate.num_pickable_floating_regs*5
    else:
        num_instrs_freg = 0
    # 4: 3 instructions + 4-8 bytes (~1-2 instrs) to store the data + 4 bytes to potentially align.
    if fuzzerstate.is_design_64bit:
        num_instrs_reg = fuzzerstate.num_pickable_regs*4
    else:
        num_instrs_reg = 1+fuzzerstate.num_pickable_regs*5
    return 4*(num_instrs_static + num_instrs_csrs + num_instr_privilege_restoration + num_instrs_mem + num_instrs_freg + num_instrs_reg + num_instrs_reset_last_reg)

@dataclass
class SavedContext:
    fcsr: int
    mepc: int
    sepc: int
    mcause: int
    scause: int
    mscratch: int
    sscratch: int
    mtvec: int
    stvec: int
    medeleg: int
    mstatus: int
    minstret: int
    minstreth: int # Only used for 32-bit
    privilege: PrivilegeStateEnum
    mem_bytes_dict: dict # mem_bytes_dict[addr]: value
    freg_vals: list
    reg_vals: list

# FUTURE Set the proper privilege mode, page tables, CSR values, etc.
# @brief This function generates the context setter basic block.
# @param next_jmp_addr: The address where the context setter will jump to. We do not call it next_bb_addr because it may target not the first instruction of a basic block.
def gen_context_setter(fuzzerstate, saved_context, next_jmp_addr: int):
    def addr_to_id_in_ctxsv(addr: int):
        if DO_ASSERT:
            assert addr >= fuzzerstate.ctxsv_bb_base_addr
            assert addr < fuzzerstate.ctxsv_bb_base_addr + get_context_setter_max_size(fuzzerstate)
            assert len(saved_context.mem_bytes_dict) <= fuzzerstate.num_store_locations * (1 << (ALIGNMENT_BITS_MAX)) # Check that we do not have too many writes to memory, Else, we may want to adapt the assumption in get_context_setter_max_size.
        return (addr - fuzzerstate.ctxsv_bb_base_addr) // 4

    fuzzerstate.ctxsv_bb = []
    addr_csr_loads = {} # addr_csr_loads[csr_id]: addr

    curr_addr = fuzzerstate.ctxsv_bb_base_addr

    # Use the register MAX_NUM_PICKABLE_REGS to hold the absolute address of the start of this bb.
    fuzzerstate.ctxsv_bb.append(ImmRdInstruction('auipc', MAX_NUM_PICKABLE_REGS, 0, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
    curr_addr += 4 # NO_COMPRESSED

    ###
    # First, set the CSRs to the expected values
    ###

    # fcsr
    if fuzzerstate.design_has_fpu:
        # Pre-relocate the address where we pre-store the fcsr value
        # Set the address of the fcsr val
        addr_csr_loads[CSR_IDS.FCSR] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        curr_addr += 4 # NO_COMPRESSED
        # Load the fcsr value
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        curr_addr += 4 # NO_COMPRESSED
        # Write the value into fcsr
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.FCSR))
        curr_addr += 4 # NO_COMPRESSED

    # mepc, only if we start in machine mode (else, we will have to overwrite it anyways later)
    if saved_context.privilege == PrivilegeStateEnum.MACHINE and (fuzzerstate.design_has_supervisor_mode or fuzzerstate.design_has_user_mode):
        addr_csr_loads[CSR_IDS.MEPC] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MEPC))
        curr_addr += 12 # NO_COMPRESSED

    # sepc
    if fuzzerstate.design_has_supervisor_mode:
        addr_csr_loads[CSR_IDS.SEPC] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.SEPC))
        curr_addr += 12 # NO_COMPRESSED

    # mcause
    addr_csr_loads[CSR_IDS.MCAUSE] = curr_addr
    fuzzerstate.ctxsv_bb.append(None)
    fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
    fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MCAUSE))
    curr_addr += 12 # NO_COMPRESSED

    # scause
    if fuzzerstate.design_has_supervisor_mode:
        addr_csr_loads[CSR_IDS.SCAUSE] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.SCAUSE))
        curr_addr += 12 # NO_COMPRESSED

    # mscratch
    addr_csr_loads[CSR_IDS.MSCRATCH] = curr_addr
    fuzzerstate.ctxsv_bb.append(None)
    if fuzzerstate.is_design_64bit:
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("ld", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
    else:
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
    fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MSCRATCH))
    curr_addr += 12 # NO_COMPRESSED

    if fuzzerstate.design_has_supervisor_mode:
        addr_csr_loads[CSR_IDS.SSCRATCH] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        if fuzzerstate.is_design_64bit:
            fuzzerstate.ctxsv_bb.append(IntLoadInstruction("ld", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        else:
            fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.SSCRATCH))
        curr_addr += 12 # NO_COMPRESSED

    # mtvec
    # if fuzzerstate.design_has_supervisor_mode:
    if 'picorv32' not in fuzzerstate.design_name:
        addr_csr_loads[CSR_IDS.MTVEC] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MTVEC))
        curr_addr += 12 # NO_COMPRESSED

    # stvec
    if fuzzerstate.design_has_supervisor_mode:
        addr_csr_loads[CSR_IDS.STVEC] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.STVEC))
        curr_addr += 12 # NO_COMPRESSED

    # medeleg
    if fuzzerstate.design_has_supervisor_mode:
        addr_csr_loads[CSR_IDS.MEDELEG] = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MEDELEG))
        curr_addr += 12 # NO_COMPRESSED

    # mstatus is a bit special because bits above 31 are typically used as well. We must hence discriminate between 32 and 64 bit designs.
    addr_csr_loads[CSR_IDS.MSTATUS] = curr_addr
    if fuzzerstate.is_design_64bit:
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("ld", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MSTATUS))
        curr_addr += 12 # NO_COMPRESSED
    else:
        # Register 1 contains the lsbs and register 2 the msbs.
        # This is a draft implementation that has not been tested yet.
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lw", 2, 2, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MSTATUS))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 2, CSR_IDS.MSTATUSH))
        curr_addr += 24 # NO_COMPRESSED

    # minstret is a bit special because bits above 31 are typically used as well. We must hence discriminate between 32 and 64 bit designs.
    addr_csr_loads[CSR_IDS.MINSTRET] = curr_addr
    if fuzzerstate.is_design_64bit:
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("ld", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MINSTRET))
        curr_addr += 12 # NO_COMPRESSED
    else:
        # Register 1 contains the lsbs and register 2 the msbs.
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(None)
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lw", 2, 2, 0, -1, fuzzerstate.is_design_64bit))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MINSTRET))
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 2, CSR_IDS.MINSTRETH))
        curr_addr += 24 # NO_COMPRESSED
    minstret_base_addr = curr_addr


    ###
    # Second, set the correct privilege level, if the saved context specifies something else than machine mode
    ###

    if saved_context.privilege == PrivilegeStateEnum.SUPERVISOR or saved_context.privilege == PrivilegeStateEnum.USER:
        # Populate mpp
        if saved_context.privilege == PrivilegeStateEnum.SUPERVISOR:
            fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrs", 0, MPP_BOTH_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS))
            fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrc", 0, MPP_TOP_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS))
        else:
            fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrc", 0, MPP_BOTH_ENDIS_REGISTER_ID, CSR_IDS.MSTATUS))
            fuzzerstate.ctxsv_bb.append(RegImmInstruction("addi", 0, 0, 0, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
        curr_addr += 8 # NO_COMPRESSED
        # Populate mepc
        mepc_target = curr_addr + 12
        fuzzerstate.ctxsv_bb.append(RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, mepc_target-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)) # The reg `MAX_NUM_PICKABLE_REGS` contains the start address of the context sette, is_rd_nonpickable_ok=Truer
        fuzzerstate.ctxsv_bb.append(CSRRegInstruction("csrrw", 0, 1, CSR_IDS.MEPC))
        fuzzerstate.ctxsv_bb.append(PrivilegeDescentInstruction(True)) # mret
        # Add 2 nops for the mret, just in case the CPU is not doing great with mret sometimes :)
        fuzzerstate.ctxsv_bb.append(RegImmInstruction("addi", 0, 0, 0, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
        curr_addr += 16 # NO_COMPRESSED

    ###
    # Third, set the memory bytes to the expected values
    ###

    addrs_memaddrs = [] # FUTURE: An alternative implementation would be to just load the address once and then play with lb offset. This would do much better packing, even though it may limit the number of bytes that can be loaded (but to a probably large enough number).
    for mem_byte_id, (mem_byte_addr, mem_byte_val) in enumerate(saved_context.mem_bytes_dict.items()):
        if DO_ASSERT:
            assert mem_byte_val >= 0
            assert mem_byte_val < 256
            assert mem_byte_addr >= 0
            assert mem_byte_addr < fuzzerstate.memsize
        # Arbitrarily use register 1 to load the byte addr
        addrs_memaddrs.append(curr_addr)
        fuzzerstate.ctxsv_bb.append(None)
        curr_addr += 4 # NO_COMPRESSED
        # We load the byte addr into register 1
        fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lwu" if fuzzerstate.is_design_64bit else "lw", 1, 1, 0, -1, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
        curr_addr += 4 # NO_COMPRESSED
        # We set the byte value using an immediate
        fuzzerstate.ctxsv_bb.append(RegImmInstruction("addi", 2, 0, mem_byte_val, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
        curr_addr += 4 # NO_COMPRESSED
        # Store the value into memory
        fuzzerstate.ctxsv_bb.append(IntStoreInstruction("sb", 1, 2, 0, -1, fuzzerstate.is_design_64bit)) # sb dest, val, offset
        curr_addr += 4 # NO_COMPRESSED

    ###
    # Fourth, set the memory bytes to the expected values
    ###

    if fuzzerstate.design_has_fpu:
        addr_freg_load_addi = curr_addr
        fuzzerstate.ctxsv_bb.append(None)
        curr_addr += 4 # NO_COMPRESSED
        for freg_id, freg_val in enumerate(saved_context.freg_vals):
            if DO_ASSERT:
                assert freg_val >= 0
                assert freg_val < 1 << 64 if fuzzerstate.design_has_fpud else 1 << 32
            if fuzzerstate.design_has_fpud:
                fuzzerstate.ctxsv_bb.append(FloatLoadInstruction("fld", freg_id, 1, 8*freg_id, -1, fuzzerstate.is_design_64bit))
            else:
                fuzzerstate.ctxsv_bb.append(FloatLoadInstruction("flw", freg_id, 1, 4*freg_id, -1, fuzzerstate.is_design_64bit))
            curr_addr += 4 # NO_COMPRESSED

    ###
    # Finally, load the integer registers
    ###

    addr_reg_load_addi = curr_addr
    fuzzerstate.ctxsv_bb.append(None)
    curr_addr += 4 # NO_COMPRESSED
    for reg_id, reg_val in enumerate(saved_context.reg_vals):
        if DO_ASSERT:
            assert reg_val >= 0
            assert reg_val < 1 << 64 if fuzzerstate.is_design_64bit else 1 << 32
        # Set the address of the reg val
        addr_reg_load = curr_addr
        if fuzzerstate.is_design_64bit:
            fuzzerstate.ctxsv_bb.append(IntLoadInstruction("ld", reg_id, MAX_NUM_PICKABLE_REGS, 8*reg_id, -1, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
            curr_addr += 4 # NO_COMPRESSED
        else:
            fuzzerstate.ctxsv_bb.append(IntLoadInstruction("lw", reg_id, MAX_NUM_PICKABLE_REGS, 4*reg_id, -1, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
            curr_addr += 4 # NO_COMPRESSED

    # Reset the reg MAX_NUM_PICKABLE_REGS to 0
    fuzzerstate.ctxsv_bb.append(RegImmInstruction("addi", MAX_NUM_PICKABLE_REGS, 0, 0, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True))
    curr_addr += 4 # NO_COMPRESSED

    # Jump to the next bb
    if DO_ASSERT:
        assert abs(next_jmp_addr - curr_addr) < 1 << 20 # Ensure that the jump is not too far for a jal
    fuzzerstate.ctxsv_bb.append(JALInstruction("jal", 0, next_jmp_addr - curr_addr))
    fuzzerstate.ctxsv_bb_jal_instr_id = len(fuzzerstate.ctxsv_bb)-1
    curr_addr += 4 # NO_COMPRESSED
    instr_end_addr = curr_addr

    ###
    # The actual values will be set here
    ###

    # For CSRs, we must ensure that the address is aligned to 8 bytes
    while curr_addr % 8 != 0:
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 4

    # Set the CSR values here. Use the register 1 to load the value, arbitrarily.
    if fuzzerstate.design_has_fpu:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.FCSR])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.fcsr))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    if saved_context.privilege == PrivilegeStateEnum.MACHINE and (fuzzerstate.design_has_supervisor_mode or fuzzerstate.design_has_user_mode):
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MEPC])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mepc))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    if fuzzerstate.design_has_supervisor_mode:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.SEPC])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.sepc))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    # mcause
    fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MCAUSE])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
    fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mcause))
    fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
    curr_addr += 8 # NO_COMPRESSED

    if fuzzerstate.design_has_supervisor_mode:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.SCAUSE])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.scause))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    # mscratch
    fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MSCRATCH])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
    fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mscratch & 0xffffffff))
    fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mscratch >> 32))
    curr_addr += 8 # NO_COMPRESSED

    if fuzzerstate.design_has_supervisor_mode:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.SSCRATCH])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.sscratch & 0xffffffff))
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.sscratch >> 32))
        curr_addr += 8 # NO_COMPRESSED

    if 'picorv32' not in fuzzerstate.design_name:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MTVEC])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mtvec))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    if fuzzerstate.design_has_supervisor_mode:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.STVEC])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.stvec))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    if fuzzerstate.design_has_supervisor_mode:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MEDELEG])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.medeleg))
        fuzzerstate.ctxsv_bb.append(RawDataWord(0xdeadbeef))
        curr_addr += 8 # NO_COMPRESSED

    # mstatus is a bit special because bits above 31 are typically used as well. We must hence discriminate between 32 and 64 bit designs.
    if DO_ASSERT:
        assert saved_context.mstatus >> 64 == 0, "mstatus is unexpectedly too large."
    # Little endian. For a number written big endian `abcd`, the bytes should be written in memory as `dcba`. So we write the lsbs first.
    fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MSTATUS])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
    if not fuzzerstate.is_design_64bit:
        # Prepare register 2 to be written to the msb of mstatus
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MSTATUS])+1] = RegImmInstruction("addi", 2, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr+4, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
    fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mstatus & 0xffffffff))
    fuzzerstate.ctxsv_bb.append(RawDataWord(saved_context.mstatus >> 32))
    curr_addr += 8 # NO_COMPRESSED

    # mstatus is a bit special because bits above 31 are typically used as well. We must hence discriminate between 32 and 64 bit designs.
    if DO_ASSERT:
        assert saved_context.minstret >> 64 == 0, "minstret is unexpectedly too large."
    # Little endian. For a number written big endian `abcd`, the bytes should be written in memory as `dcba`. So we write the lsbs first.
    fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MINSTRET])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
    if not fuzzerstate.is_design_64bit:
        # Prepare register 2 to be written to the msb of minstret
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_csr_loads[CSR_IDS.MINSTRET])+1] = RegImmInstruction("addi", 2, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr+4, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)

    fuzzerstate.ctxsv_bb.append(RawDataWord((saved_context.minstret - ((instr_end_addr - (minstret_base_addr - 4 - 4*int(fuzzerstate.is_design_64bit))) // 4)) & 0xffffffff, signed=True))

    if fuzzerstate.is_design_64bit:
        fuzzerstate.ctxsv_bb.append(RawDataWord((saved_context.minstret - ((instr_end_addr - minstret_base_addr - 4) // 4)) >> 32, signed=True))
    else:
        # Should be checked in detail
        if (saved_context.minstret - ((instr_end_addr - (minstret_base_addr - 4 - 4*int(fuzzerstate.is_design_64bit))) // 4)) < 0: # If minstret is negative and will be increased before the start of the run
            fuzzerstate.ctxsv_bb.append(RawDataWord((((saved_context.minstret + (saved_context.minstreth << 32)) - ((instr_end_addr - minstret_base_addr - 4) // 4)) >> 32), signed=True))
        else:
            fuzzerstate.ctxsv_bb.append(RawDataWord((((saved_context.minstret + (saved_context.minstreth << 32)) - ((instr_end_addr - minstret_base_addr - 4) // 4)) >> 32), signed=True))
    curr_addr += 8 # NO_COMPRESSED

    ###
    # We're now done with CSRs.
    ###

    # Memory bytes
    for mem_byte_id, (mem_byte_addr, mem_byte_val) in enumerate(saved_context.mem_bytes_dict.items()):
        # Set the address of the mem byte
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addrs_memaddrs[mem_byte_id])] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        fuzzerstate.ctxsv_bb.append(RawDataWord(mem_byte_addr + SPIKE_STARTADDR))
        curr_addr += 4 # NO_COMPRESSED

    # Set the fpu register values here. Use the register 1 to load the address, arbitrarily.
    if fuzzerstate.design_has_fpu:
        if fuzzerstate.design_has_fpud:
            # Align if needed
            if curr_addr % 8 != 0:
                fuzzerstate.ctxsv_bb.append(RawDataWord(0))
                curr_addr += 4
            fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_freg_load_addi)] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
            for freg_id, freg_val in enumerate(saved_context.freg_vals):
                if DO_ASSERT:
                    assert freg_val >= 0
                    assert freg_val < 1 << 64
                fuzzerstate.ctxsv_bb.append(RawDataWord(freg_val % (1 << 32)))
                fuzzerstate.ctxsv_bb.append(RawDataWord(freg_val // (1 << 32)))
                curr_addr += 8
        else:
            if DO_ASSERT:
                assert freg_val >= 0
                assert freg_val < 1 << 32
            fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_freg_load_addi)] = RegImmInstruction("addi", 1, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
            for freg_id, freg_val in enumerate(saved_context.freg_vals):
                fuzzerstate.ctxsv_bb.append(RawDataWord(freg_val))
                curr_addr += 4 # NO_COMPRESSED

    # Finally, set the integer registers here. Use the last register to load the address, to ensure that we will not overwrite some int register in the process.
    if fuzzerstate.is_design_64bit:
        # Align if needed
        if curr_addr % 8 != 0:
            fuzzerstate.ctxsv_bb.append(RawDataWord(0))
            curr_addr += 4

        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_reg_load_addi)] = RegImmInstruction("addi", MAX_NUM_PICKABLE_REGS, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        for reg_id, reg_val in enumerate(saved_context.reg_vals):
            # print('For reg id %d, reg val is %s. Addr: %s' % (reg_id, hex(reg_val), hex(curr_addr)))
            fuzzerstate.ctxsv_bb.append(RawDataWord(reg_val % (1 << 32)))
            fuzzerstate.ctxsv_bb.append(RawDataWord(reg_val // (1 << 32)))
            curr_addr += 8
    else:
        fuzzerstate.ctxsv_bb[addr_to_id_in_ctxsv(addr_reg_load_addi)] = RegImmInstruction("addi", MAX_NUM_PICKABLE_REGS, MAX_NUM_PICKABLE_REGS, curr_addr-fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.is_design_64bit, is_rd_nonpickable_ok=True)
        for reg_id, reg_val in enumerate(saved_context.reg_vals):
            fuzzerstate.ctxsv_bb.append(RawDataWord(reg_val))
            curr_addr += 4 # NO_COMPRESSED

    if DO_ASSERT:
        assert curr_addr == fuzzerstate.ctxsv_bb_base_addr + len(fuzzerstate.ctxsv_bb)*4, f"curr_addr is `{hex(curr_addr)}`, fuzzerstate.ctxsv_bb_base_addr + len(fuzzerstate.ctxsv_bb)*4 is `{hex(fuzzerstate.ctxsv_bb_base_addr + len(fuzzerstate.ctxsv_bb)*4)}`" # NO_COMPRESSED
        assert curr_addr <= fuzzerstate.ctxsv_bb_base_addr + fuzzerstate.ctxsv_size_upperbound, f"The context setter is too large: size is `{hex(curr_addr-fuzzerstate.ctxsv_bb_base_addr)}`, fuzzerstate.ctxsv_size_upperbound is `{hex(fuzzerstate.ctxsv_size_upperbound)}`."
