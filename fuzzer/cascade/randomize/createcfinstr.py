# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import random
import numpy as np

from params.runparams import DO_ASSERT

from params.fuzzparams import NUM_MIN_FREE_INTREGS, REG_FSM_WEIGHTS, NONTAKEN_BRANCH_INTO_RANDOM_DATA_PROBA
from cascade.util import IntRegIndivState
from cascade.cfinstructionclasses import *
from rv.util import PARAM_REGTYPE, PARAM_SIZES_BITS_32, PARAM_SIZES_BITS_64

# This module creates an instruction from its instruction string, and some state which will condition which registers and immediates will be picked, and with which probability.

###
# Utility functions
###

def gen_random_imm(instr_str: str, is_design_64bit: bool):
    if DO_ASSERT:
        assert PARAM_REGTYPE[INSTRUCTION_IDS[instr_str]][-1] == ''
    if is_design_64bit:
        imm_width = PARAM_SIZES_BITS_64[INSTRUCTION_IDS[instr_str]][-1]
    else:
        imm_width = PARAM_SIZES_BITS_32[INSTRUCTION_IDS[instr_str]][-1]
    if PARAM_IS_SIGNED[INSTRUCTION_IDS[instr_str]][-1]:
        left_bound  = -(1<<(imm_width-1))
        right_bound = 1<<(imm_width-1)
    else:
        left_bound  = 0
        right_bound = 1<<imm_width
    return random.randrange(left_bound, right_bound)

# Random rounding modes
def gen_random_rounding_mode():
    return random.sample([0, 1, 2, 3, 4, 7], 1)[0]

###
# Functions for creation by CFInstructionClass
###

# Integer instructions

def _create_R12DInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in R12DInstructions
    rs1, rs2 = tuple(fuzzerstate.intregpickstate.pick_int_inputregs(2))
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    return R12DInstruction(instr_str, rd, rs1, rs2, iscompressed)

def _create_ImmRdInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in ImmRdInstructions
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    imm = gen_random_imm(instr_str, fuzzerstate.is_design_64bit)
    if instr_str == "auipc" and rd > 0:
        fuzzerstate.intregpickstate.set_regstate(rd, IntRegIndivState.FREE)
    return ImmRdInstruction(instr_str, rd, imm, fuzzerstate.is_design_64bit, iscompressed)

def _create_RegImmInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in RegImmInstructions
    rs1 = fuzzerstate.intregpickstate.pick_int_inputreg()
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    imm = gen_random_imm(instr_str, fuzzerstate.is_design_64bit)
    return RegImmInstruction(instr_str, rd, rs1, imm, fuzzerstate.is_design_64bit, iscompressed)

def _create_BranchInstruction(instr_str: str, fuzzerstate, curr_addr: int, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in BranchInstructions
    rs1 = fuzzerstate.intregpickstate.pick_int_inputreg()
    rs2 = fuzzerstate.intregpickstate.pick_int_inputreg()
    plan_taken = fuzzerstate.curr_branch_taken
    if plan_taken:
        # print('A', flush=True)
        imm = fuzzerstate.next_bb_addr-curr_addr
    else:
        # Select whether to direct toward the random data basic block
        is_random_data_block_in_reach = abs(fuzzerstate.random_data_block_start_addr - curr_addr) < (1<<11) and abs(fuzzerstate.random_data_block_end_addr-4 - curr_addr) < (1<<11)
        if is_random_data_block_in_reach and random.random() < NONTAKEN_BRANCH_INTO_RANDOM_DATA_PROBA:
            lowest_random_data_reachable_addr = max(fuzzerstate.random_data_block_start_addr+4, curr_addr - (1<<11))
            highest_random_data_reachable_addr = min(fuzzerstate.random_data_block_end_addr-4, curr_addr + (1<<11))

            target_addr_in_random_data_block = random.randrange(lowest_random_data_reachable_addr//2, highest_random_data_reachable_addr//2)*2
            imm = target_addr_in_random_data_block-curr_addr
        else:
            imm = gen_random_imm(instr_str, fuzzerstate.is_design_64bit)
    
    # print('New imm', hex(imm), flush=True)
    return BranchInstruction(instr_str, rs1, rs2, imm, plan_taken, fuzzerstate.is_design_64bit, iscompressed)

def _create_JALInstruction(instr_str: str, fuzzerstate, curr_addr: int, iscompressed: bool):
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    imm = fuzzerstate.next_bb_addr-curr_addr
    if rd > 0:
        fuzzerstate.intregpickstate.set_regstate(rd, IntRegIndivState.FREE)
    return JALInstruction(instr_str, rd, imm, iscompressed)
def _create_JALRInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    rs1 = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.CONSUMED)
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    imm = 0
    producer_id = fuzzerstate.intregpickstate.get_producer_id(rs1)
    fuzzerstate.intregpickstate.set_regstate(rs1, IntRegIndivState.FREE)
    if rd > 0:
        fuzzerstate.intregpickstate.set_regstate(rd, IntRegIndivState.FREE)
    if DO_ASSERT:
        assert producer_id > 0
    return JALRInstruction(instr_str, rd, rs1, imm, producer_id, fuzzerstate.is_design_64bit, iscompressed)
def _create_SpecialInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    rs1 = fuzzerstate.intregpickstate.pick_int_inputreg()
    return SpecialInstruction(instr_str, rd, rs1, iscompressed)

def _create_IntLoadInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in IntLoadInstructions
    rs1 = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.CONSUMED)
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    imm = 0
    producer_id = fuzzerstate.intregpickstate.get_producer_id(rs1)
    fuzzerstate.intregpickstate.set_regstate(rs1, IntRegIndivState.FREE)
    if DO_ASSERT:
        assert producer_id > 0
    return IntLoadInstruction(instr_str, rd, rs1, imm, producer_id, fuzzerstate.is_design_64bit, iscompressed)

def _create_IntStoreInstruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in IntStoreInstructions
    rs1 = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.CONSUMED)
    rs2 = fuzzerstate.intregpickstate.pick_int_inputreg()
    imm = 0
    producer_id = fuzzerstate.intregpickstate.get_producer_id(rs1)
    fuzzerstate.intregpickstate.set_regstate(rs1, IntRegIndivState.FREE)
    if DO_ASSERT:
        assert producer_id > 0
    return IntStoreInstruction(instr_str, rs1, rs2, imm, producer_id, fuzzerstate.is_design_64bit, iscompressed)

# Floating-point instructions

def _create_FloatLoadInstruction  (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in FloatLoadInstructions
    rs1 = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.CONSUMED)
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    imm = 0
    producer_id = fuzzerstate.intregpickstate.get_producer_id(rs1)
    fuzzerstate.intregpickstate.set_regstate(rs1, IntRegIndivState.FREE)
    if DO_ASSERT:
        assert producer_id > 0
    return FloatLoadInstruction(instr_str, frd, rs1, imm, producer_id, fuzzerstate.is_design_64bit, iscompressed)
def _create_FloatStoreInstruction (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in FloatStoreInstructions
    rs1 = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.CONSUMED)
    frs2 = fuzzerstate.floatregpickstate.pick_float_inputreg()
    imm = 0
    producer_id = fuzzerstate.intregpickstate.get_producer_id(rs1)
    fuzzerstate.intregpickstate.set_regstate(rs1, IntRegIndivState.FREE)
    if DO_ASSERT:
        assert producer_id > 0
    return FloatStoreInstruction(instr_str, rs1, frs2, imm, producer_id, fuzzerstate.is_design_64bit, iscompressed)
def _create_FloatToIntInstruction (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in FloatToIntInstructions
    rm = gen_random_rounding_mode()
    frs1 = fuzzerstate.floatregpickstate.pick_float_inputreg()
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    return FloatToIntInstruction(instr_str, rd, frs1, rm, iscompressed)
def _create_IntToFloatInstruction (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in IntToFloatInstructions
    rm = gen_random_rounding_mode()
    rs1 = fuzzerstate.intregpickstate.pick_int_inputreg()
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    return IntToFloatInstruction(instr_str, frd, rs1, rm, iscompressed)
def _create_Float4Instruction     (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in Float4Instructions
    rm = gen_random_rounding_mode()
    frs1, frs2, frs3 = tuple(fuzzerstate.floatregpickstate.pick_float_inputregs(3))
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    return Float4Instruction(instr_str, frd, frs1, frs2, frs3, rm, iscompressed)
def _create_Float3Instruction     (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in Float3Instructions
    rm = gen_random_rounding_mode()
    frs1, frs2 = tuple(fuzzerstate.floatregpickstate.pick_float_inputregs(2))
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    return Float3Instruction(instr_str, frd, frs1, frs2, rm, iscompressed)
def _create_Float3NoRmInstruction (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in Float3NoRmInstructions
    frs1, frs2 = tuple(fuzzerstate.floatregpickstate.pick_float_inputregs(2))
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    return Float3NoRmInstruction(instr_str, frd, frs1, frs2, iscompressed)
def _create_Float2Instruction     (instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in Float2Instructions
    rm = gen_random_rounding_mode()
    frs1 = fuzzerstate.floatregpickstate.pick_float_inputreg()
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    return Float2Instruction(instr_str, frd, frs1, rm, iscompressed)
def _create_FloatIntRd2Instruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in FloatIntRd2Instructions
    frs1, frs2 = tuple(fuzzerstate.floatregpickstate.pick_float_inputregs(2))
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    return FloatIntRd2Instruction(instr_str, rd, frs1, frs2, iscompressed)
def _create_FloatIntRd1Instruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in FloatIntRd1Instructions
    frs1 = fuzzerstate.floatregpickstate.pick_float_inputreg()
    rd = fuzzerstate.intregpickstate.pick_int_outputreg()
    return FloatIntRd1Instruction(instr_str, rd, frs1, iscompressed)
def _create_FloatIntRs1Instruction(instr_str: str, fuzzerstate, iscompressed: bool):
    if DO_ASSERT:
        assert instr_str in FloatIntRs1Instructions
    frd = fuzzerstate.floatregpickstate.pick_float_outputreg()
    rs1 = fuzzerstate.intregpickstate.pick_int_inputreg()
    return FloatIntRs1Instruction(instr_str, frd, rs1, iscompressed)

###
# Exposed function
###

def create_regfsm_instrobjs(fuzzerstate):
    # Check which reg fsm operations are doable
    doable_fsm_ops = np.zeros(3, dtype=np.int8)
    doable_fsm_ops[0] = fuzzerstate.intregpickstate.get_num_regs_in_state(IntRegIndivState.FREE) > NUM_MIN_FREE_INTREGS
    doable_fsm_ops[1] = fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.PRODUCED0)
    doable_fsm_ops[2] = fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.PRODUCED1)

    effective_weights = doable_fsm_ops * REG_FSM_WEIGHTS

    choice = None
    while choice is None or not doable_fsm_ops[choice]:
        choice = random.choices(range(3), effective_weights, k=1)[0]

    if choice == 0: # FREE -> PRODUCED0
        return create_targeted_producer0_instrobj(fuzzerstate)
    elif choice == 1: # PRODUCED0 -> PRODUCED1
        return create_targeted_producer1_instrobj(fuzzerstate)
    elif choice == 2: # PRODUCED1 -> FREE/CONSUMED
        return create_targeted_consumer_instrobj(fuzzerstate)
    else:
        raise ValueError(f"Unexpected choice: `{choice}`.")

def create_targeted_producer0_instrobj(fuzzerstate):
    fuzzerstate.next_producer_id += 1
    rd = fuzzerstate.intregpickstate.pick_int_outputreg_nonzero(False)
    fuzzerstate.intregpickstate.set_producer_id(rd, fuzzerstate.next_producer_id)
    # fuzzerstate.intregpickstate.set_producer1_location(rd, len(fuzzerstate.instr_objs_seq), len(fuzzerstate.instr_objs_seq[0])) # Optimization currently unused
    fuzzerstate.intregpickstate.set_regstate(rd, IntRegIndivState.PRODUCED0)
    return [PlaceholderProducerInstr0(rd, fuzzerstate.next_producer_id, fuzzerstate.is_design_64bit)]
def create_targeted_producer1_instrobj(fuzzerstate):
    rd = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.PRODUCED0)
    # fuzzerstate.intregpickstate.set_producer1_location(rd, len(fuzzerstate.instr_objs_seq), len(fuzzerstate.instr_objs_seq[0])) # Optimization currently unused
    fuzzerstate.intregpickstate.set_regstate(rd, IntRegIndivState.PRODUCED1)
    return [PlaceholderProducerInstr1(rd, fuzzerstate.intregpickstate.get_producer_id(rd), fuzzerstate.is_design_64bit)]
def create_targeted_consumer_instrobj(fuzzerstate):
    rdep = fuzzerstate.intregpickstate.pick_int_inputreg_nonzero(False) # We want to create dependencies, therefore we choose not to accept x0
    rprod = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.PRODUCED1)
    # WARNING: We CANNOT throw a PRODUCEDX into the nature because its value will change between spike and RTL.
    rd = rprod
    fuzzerstate.intregpickstate.set_regstate(rprod, IntRegIndivState.CONSUMED)
    if fuzzerstate.is_design_64bit:
        return [PlaceholderPreConsumerInstr(rprod), PlaceholderPreConsumerInstr(rdep), PlaceholderConsumerInstr(rd, rdep, rprod, fuzzerstate.intregpickstate.get_producer_id(rprod))]
    else:
        return [PlaceholderConsumerInstr(rd, rdep, rprod, fuzzerstate.intregpickstate.get_producer_id(rprod))]

# The reservation in the MemoryView is already done ahead and should not be reiterated here.
# @param jalr_addr_reg: only meaningful if a jalr is present (in the latter case, it should be the next instruction)
def create_instr(instr_str: str, fuzzerstate, curr_addr: int, iscompressed: bool = False):
    if DO_ASSERT:
        assert not iscompressed

    # Integer instructions
    if instr_str in R12DInstructions:
        return _create_R12DInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in ImmRdInstructions:
        return _create_ImmRdInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in RegImmInstructions:
        return _create_RegImmInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in BranchInstructions:
        return _create_BranchInstruction(instr_str, fuzzerstate, curr_addr, iscompressed)
    elif instr_str in JALInstructions:
        return _create_JALInstruction(instr_str, fuzzerstate, curr_addr, iscompressed)
    elif instr_str in JALRInstructions:
        return _create_JALRInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in SpecialInstructions:
        return _create_SpecialInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in IntLoadInstructions:
        return _create_IntLoadInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in IntStoreInstructions:
        return _create_IntStoreInstruction(instr_str, fuzzerstate, iscompressed)
    # Floating point instructions
    elif instr_str in FloatLoadInstructions:
        return _create_FloatLoadInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in FloatStoreInstructions:
        return _create_FloatStoreInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in FloatToIntInstructions:
        return _create_FloatToIntInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in IntToFloatInstructions:
        return _create_IntToFloatInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in Float4Instructions:
        return _create_Float4Instruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in Float3Instructions:
        return _create_Float3Instruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in Float3NoRmInstructions:
        return _create_Float3NoRmInstruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in Float2Instructions:
        return _create_Float2Instruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in FloatIntRd2Instructions:
        return _create_FloatIntRd2Instruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in FloatIntRd1Instructions:
        return _create_FloatIntRd1Instruction(instr_str, fuzzerstate, iscompressed)
    elif instr_str in FloatIntRs1Instructions:
        return _create_FloatIntRs1Instruction(instr_str, fuzzerstate, iscompressed)

    else:
        raise ValueError(f"Unexpected instruction string: `{instr_str}`")
