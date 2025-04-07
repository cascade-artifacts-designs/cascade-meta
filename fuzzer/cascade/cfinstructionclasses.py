# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script defines.

from params.fuzzparams import MAX_NUM_PICKABLE_REGS, RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID
from params.runparams import DO_ASSERT
from rv.csrids import CSR_IDS
from rv.util import INSTRUCTION_IDS, PARAM_SIZES_BITS_32, PARAM_SIZES_BITS_64, PARAM_IS_SIGNED
from rv.asmutil import li_into_reg, twos_complement, to_unsigned
from rv.rvprivileged import rvprivileged_mret, rvprivileged_sret
from rv.zifencei import *
from rv.zicsr import *
from rv.rv32i import *
from rv.rv32f import *
from rv.rv32d import *
from rv.rv32m import *
from rv.rv64i import *
from rv.rv64f import *
from rv.rv64d import *
from rv.rv64m import *

import random

# These classes are here for generating multi-instruction fuzzing programs.

###
# Abstract classes
###

class CFInstruction:
    # Could be any instruction
    authorized_instr_strs = range(len(INSTRUCTION_IDS))

    # Check that it's not a wrong instruction id.
    def assert_authorized_instr_strs(self):
        if DO_ASSERT:
            assert self.instr_str in self.__class__.authorized_instr_strs

    def __init__(self, instr_str: str, iscompressed: bool = False):
        self.instr_str = instr_str
        self.iscompressed = iscompressed
        assert not iscompressed, "Compressed instructions are not yet supported."
        self.assert_authorized_instr_strs()

    # @param is_spike_resolution: some rare instructions (typically offset management placeholders) are treated differently between spike resolution and the subsequent actual simulation.
    def gen_bytecode_int(self, is_spike_resolution: bool):
        raise ValueError('Cannot generate bytecode in the abstract instruction classes.')

# Any instruction with an immediate
class ImmInstruction(CFInstruction):
    # static
    authorized_instr_strs = ("lui", "auipc", "jal", "jalr", "beq", "bne", "blt", "bge", "bltu", "bgeu", "lb", "lh", "lw", "lbu", "lhu", "sb", "sh", "sw", "addi", "slti", "sltiu", "xori", "ori", "andi", "slli", "srli", "srai", "lwu", "ld", "sd", "addiw", "slliw", "srliw", "sraiw", "flw", "fsw", "fld", "fsd")
    # Checks the immediate size.
    def assert_imm_size(self):
        if DO_ASSERT:
            assert hasattr(self, 'imm')
            if self.is_design_64bit:
                curr_param_size = PARAM_SIZES_BITS_64[INSTRUCTION_IDS[self.instr_str]][-1]
            else:
                curr_param_size = PARAM_SIZES_BITS_32[INSTRUCTION_IDS[self.instr_str]][-1]
            if PARAM_IS_SIGNED[INSTRUCTION_IDS[self.instr_str]][-1]:
                assert self.imm >= -(1<<(curr_param_size-1))
                assert self.imm <  1<<(curr_param_size-1)
            else:
                assert self.imm >= 0
                assert self.imm <  1<<curr_param_size

    def __init__(self, instr_str: str, imm: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        self.is_design_64bit = is_design_64bit
        self.imm = imm
        self.assert_imm_size()

###
# Concrete classes: integers
###

# Instructions with rs1, rs2 and rd
R12DInstructions = ("add", "sub", "sll", "slt", "sltu", "xor", "srl", "sra", "or", "and", "addw", "subw", "sllw", "srlw", "sraw", "mul", "mulh", "mulhsu", "mulhu", "div", "divu", "rem", "remu", "mulw", "divw", "divuw", "remw", "remuw")
class R12DInstruction(CFInstruction):
    authorized_instr_strs = R12DInstructions

    def __init__(self, instr_str: str, rd: int, rs1: int, rs2: int, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS or rs1 in (RELOCATOR_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID)
            assert rs2 >= 0
            assert rs2 < MAX_NUM_PICKABLE_REGS or rs2 in (RELOCATOR_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID)
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS or rd in (RELOCATOR_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID)
        self.rs1 = rs1
        self.rs2 = rs2
        self.rd =  rd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "add":
            return rv32i_add(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "sub":
            return rv32i_sub(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "sll":
            return rv32i_sll(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "slt":
            return rv32i_slt(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "sltu":
            return rv32i_sltu(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "xor":
            return rv32i_xor(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "srl":
            return rv32i_srl(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "sra":
            return rv32i_sra(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "or":
            return rv32i_or(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "and":
            return rv32i_and(self.rd, self.rs1, self.rs2)
        # rv64i
        elif self.instr_str == "addw":
            return rv64i_addw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "subw":
            return rv64i_subw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "sllw":
            return rv64i_sllw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "srlw":
            return rv64i_srlw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "sraw":
            return rv64i_sraw(self.rd, self.rs1, self.rs2)
        # rv32m
        elif self.instr_str == "mul":
            return rv32m_mul(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "mulh":
            return rv32m_mulh(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "mulhsu":
            return rv32m_mulhsu(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "mulhu":
            return rv32m_mulhu(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "div":
            return rv32m_div(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "divu":
            return rv32m_divu(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "rem":
            return rv32m_rem(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "remu":
            return rv32m_remu(self.rd, self.rs1, self.rs2)
        # rv64m
        elif self.instr_str == "mulw":
            return rv64m_mulw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "divw":
            return rv64m_divw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "divuw":
            return rv64m_divuw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "remw":
            return rv64m_remw(self.rd, self.rs1, self.rs2)
        elif self.instr_str == "remuw":
            return rv64m_remuw(self.rd, self.rs1, self.rs2)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Instructions with imm and rd
ImmRdInstructions = ("lui", "auipc")
class ImmRdInstruction(ImmInstruction):
    authorized_instr_strs = ImmRdInstructions

    def __init__(self, instr_str: str, rd: int, imm: int, is_design_64bit: bool, iscompressed: bool = False, is_rd_nonpickable_ok: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rd >= 0
            assert is_rd_nonpickable_ok or rd < MAX_NUM_PICKABLE_REGS or rd in (RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID)
        self.imm = imm
        self.rd =  rd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "lui":
            return rv32i_lui(self.rd, self.imm)
        elif self.instr_str == "auipc":
            return rv32i_auipc(self.rd, self.imm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")


# Instructions with rs1, imm and rd
RegImmInstructions = ("addi", "slti", "sltiu", "xori", "ori", "andi", "slli", "srli", "srai", "addiw", "slliw", "srliw", "sraiw")
class RegImmInstruction(ImmInstruction):
    authorized_instr_strs = RegImmInstructions

    def __init__(self, instr_str: str, rd: int, rs1: int, imm: int, is_design_64bit: bool, iscompressed: bool = False, is_rd_nonpickable_ok: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rs1 >= 0
            assert is_rd_nonpickable_ok or rs1 < MAX_NUM_PICKABLE_REGS or rs1 in (RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID), f"Got rs1 (select) =`{rs1}`"
            assert rd >= 0
            assert is_rd_nonpickable_ok or rd < MAX_NUM_PICKABLE_REGS or rd in (RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID), f"Got rd (select) =`{rd}`"
        self.rs1 = rs1
        self.rd =  rd
        if self.instr_str == "sraiw" and self.imm < 0:
            assert False

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "addi":
            return rv32i_addi(self.rd, self.rs1, self.imm)
        elif self.instr_str == "slti":
            return rv32i_slti(self.rd, self.rs1, self.imm)
        elif self.instr_str == "sltiu":
            return rv32i_sltiu(self.rd, self.rs1, self.imm)
        elif self.instr_str == "xori":
            return rv32i_xori(self.rd, self.rs1, self.imm)
        elif self.instr_str == "ori":
            return rv32i_ori(self.rd, self.rs1, self.imm)
        elif self.instr_str == "andi":
            return rv32i_andi(self.rd, self.rs1, self.imm)
        elif self.instr_str == "slli":
            return rv32i_slli(self.rd, self.rs1, self.imm)
        elif self.instr_str == "srli":
            return rv32i_srli(self.rd, self.rs1, self.imm)
        elif self.instr_str == "srai":
            return rv32i_srai(self.rd, self.rs1, self.imm)
        # rv64i
        elif self.instr_str == "addiw":
            return rv64i_addiw(self.rd, self.rs1, self.imm)
        elif self.instr_str == "slliw":
            return rv64i_slliw(self.rd, self.rs1, self.imm)
        elif self.instr_str == "srliw":
            return rv64i_srliw(self.rd, self.rs1, self.imm)
        elif self.instr_str == "sraiw":
            return rv64i_sraiw(self.rd, self.rs1, self.imm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Branch instructions: with rs1, rs2 and an immediate
BranchInstructions = ("beq", "bne", "blt", "bge", "bltu", "bgeu")
class BranchInstruction(ImmInstruction):
    authorized_instr_strs = BranchInstructions

    # @param plan_taken is True iff the branch instruction is planned to be taken.
    def __init__(self, instr_str: str, rs1: int, rs2: int, imm: int, plan_taken: bool, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS
            assert rs2 >= 0
            assert rs2 < MAX_NUM_PICKABLE_REGS
        self.rs1 = rs1
        self.rs2 = rs2
        self.plan_taken = plan_taken
        # self.producer_id = producer_id We do not use producers anymore for branches

    # Choose an opcode that, given the values of rs1 and rs2, will comply with the required takenness
    def select_suitable_opcode(self, rs1_content: int, rs2_content: int):
        int_plan_taken = int(self.plan_taken)
        can_take_opcodes = [
            # beq
            int_plan_taken ^ int(rs1_content != rs2_content),
            # bne
            int_plan_taken ^ int(rs1_content == rs2_content),
            # blt
            int_plan_taken ^ int(twos_complement(rs1_content, self.is_design_64bit) >= twos_complement(rs2_content, self.is_design_64bit)),
            # bge
            int_plan_taken ^ int(twos_complement(rs1_content, self.is_design_64bit) < twos_complement(rs2_content, self.is_design_64bit)),
            # bltu
            int_plan_taken ^ int(rs1_content >= rs2_content),
            # bgeu
            int_plan_taken ^ int(rs1_content < rs2_content),
        ]

        self.instr_str = random.choices(BranchInstructions, can_take_opcodes, k=1)[0]

    def gen_bytecode_int(self, is_spike_resolution: bool):
        if is_spike_resolution:
            if self.plan_taken:
                return rv32i_jal(0, self.imm) # Just unconditionally jump to the next basic block
            else:
                return rv32i_addi(0, 0, 0) # Nop
        else:
            # rv32i
            if self.instr_str == "beq":
                return rv32i_beq(self.rs1, self.rs2, self.imm)
            elif self.instr_str == "bne":
                return rv32i_bne(self.rs1, self.rs2, self.imm)
            elif self.instr_str == "blt":
                return rv32i_blt(self.rs1, self.rs2, self.imm)
            elif self.instr_str == "bge":
                return rv32i_bge(self.rs1, self.rs2, self.imm)
            elif self.instr_str == "bltu":
                return rv32i_bltu(self.rs1, self.rs2, self.imm)
            elif self.instr_str == "bgeu":
                return rv32i_bgeu(self.rs1, self.rs2, self.imm)
            # Default case
            else:
                raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# The jal instruction
JALInstructions = ("jal",)
class JALInstruction(ImmInstruction):
    authorized_instr_strs = JALInstructions

    def __init__(self, instr_str: str, rd: int, imm: int, iscompressed: bool = False):
        # 32 or 64 bit does not matter for JAL
        super().__init__(instr_str, imm, False, iscompressed)
        if DO_ASSERT:
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
        self.rd  = rd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        return rv32i_jal(self.rd, self.imm)

# The jalr instruction
JALRInstructions = ("jalr",)
class JALRInstruction(ImmInstruction):
    authorized_instr_strs = JALRInstructions

    def __init__(self, instr_str: str, rd: int, rs1: int, imm: int, producer_id: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS
        self.rd  = rd
        self.rs1 = rs1
        self.producer_id = producer_id

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        return rv32i_jalr(self.rd, self.rs1, self.imm)

# Instructions that create no information flow
SpecialInstructions = ("fence", "fence.i")
class SpecialInstruction(CFInstruction):
    authorized_instr_strs = SpecialInstructions

    def __init__(self, instr_str: str, rd: int = 0, rs1: int = 0, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        self.rd = rd
        self.rs1 = rs1

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "fence":
            return rv32i_fence(self.rd, self.rs1)
        # zifencei
        elif self.instr_str == "fence.i":
            return zifencei_fencei(self.rd, self.rs1)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

EcallEbreakInstructions = ("ecall", "ebreak")
class EcallEbreakInstruction(CFInstruction):
    authorized_instr_strs = EcallEbreakInstructions

    def __init__(self, instr_str: str, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "ecall":
            return rv32i_ecall()
        elif self.instr_str == "ebreak":
            return rv32i_ebreak()
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Integer load instructions
IntLoadInstructions = ("lb", "lh", "lw", "lbu", "lhu", "lwu", "ld")
class IntLoadInstruction(ImmInstruction):
    authorized_instr_strs = IntLoadInstructions

    def __init__(self, instr_str: str, rd: int, rs1: int, imm: int, producer_id: int, is_design_64bit: bool, iscompressed: bool = False, is_rd_nonpickable_ok: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
            assert rs1 >= 0
            assert is_rd_nonpickable_ok or rs1 < MAX_NUM_PICKABLE_REGS
        self.rd  = rd
        self.rs1 =  rs1
        self.producer_id = producer_id

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "lb":
            return rv32i_lb(self.rd, self.rs1, self.imm)
        elif self.instr_str == "lh":
            return rv32i_lh(self.rd, self.rs1, self.imm)
        elif self.instr_str == "lw":
            return rv32i_lw(self.rd, self.rs1, self.imm)
        elif self.instr_str == "lbu":
            return rv32i_lbu(self.rd, self.rs1, self.imm)
        elif self.instr_str == "lhu":
            return rv32i_lhu(self.rd, self.rs1, self.imm)
        # rv64i
        elif self.instr_str == "lwu":
            return rv64i_lwu(self.rd, self.rs1, self.imm)
        elif self.instr_str == "ld":
            return rv64i_ld(self.rd, self.rs1, self.imm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Integer store instructions
IntStoreInstructions = ("sb", "sh", "sw", "sd")
class IntStoreInstruction(ImmInstruction):
    authorized_instr_strs = IntStoreInstructions

    def __init__(self, instr_str: str, rs1: int, rs2: int, imm: int, producer_id: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS or rs1 in (RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID)
            assert rs2 >= 0
            assert rs2 < MAX_NUM_PICKABLE_REGS
        self.rs1 =  rs1
        self.rs2  = rs2
        self.producer_id = producer_id

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "sb":
            return rv32i_sb(self.rs1, self.rs2, self.imm)
        elif self.instr_str == "sh":
            return rv32i_sh(self.rs1, self.rs2, self.imm)
        elif self.instr_str == "sw":
            return rv32i_sw(self.rs1, self.rs2, self.imm)
        # rv64i
        elif self.instr_str == "sd":
            return rv64i_sd(self.rs1, self.rs2, self.imm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

###
# Floating-point
###

# Float load instructions
FloatLoadInstructions = ("flw", "fld")
class FloatLoadInstruction(ImmInstruction):
    authorized_instr_strs = FloatLoadInstructions

    def __init__(self, instr_str: str, frd: int, rs1: int, imm: int, producer_id: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS
        self.frd  = frd
        self.rs1 =  rs1
        self.producer_id = producer_id

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "flw":
            return rv32f_flw(self.frd, self.rs1, self.imm)
        # rv32d
        elif self.instr_str == "fld":
            return rv32d_fld(self.frd, self.rs1, self.imm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Float store instructions
FloatStoreInstructions = ("fsw", "fsd")
class FloatStoreInstruction(ImmInstruction):
    authorized_instr_strs = FloatStoreInstructions

    def __init__(self, instr_str: str, rs1: int, frs2: int, imm: int, producer_id: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, imm, is_design_64bit, iscompressed)
        if DO_ASSERT:
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS or rs1 in (RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID)
            assert frs2 >= 0
            assert frs2 < MAX_NUM_PICKABLE_REGS
        self.rs1  =  rs1
        self.frs2 = frs2
        self.producer_id = producer_id

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fsw":
            return rv32f_fsw(self.rs1, self.frs2, self.imm)
        # rv32d
        elif self.instr_str == "fsd":
            return rv32d_fsd(self.rs1, self.frs2, self.imm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Float to int instructions
FloatToIntInstructions = ("fcvt.w.s", "fcvt.wu.s", "fcvt.l.s", "fcvt.lu.s", "fcvt.w.d", "fcvt.wu.d", "fcvt.l.d", "fcvt.lu.d")
class FloatToIntInstruction(CFInstruction):
    authorized_instr_strs = FloatToIntInstructions

    def __init__(self, instr_str: str, rd: int, frs1: int, rm: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rm >= 0
            assert rm < MAX_NUM_PICKABLE_REGS
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
        self.rm   = rm
        self.frs1 = frs1
        self.rd   = rd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fcvt.w.s":
            return rv32f_fcvtws(self.rd, self.frs1, self.rm)
        elif self.instr_str == "fcvt.wu.s":
            return rv32f_fcvtwus(self.rd, self.frs1, self.rm)
        # rv64f
        elif self.instr_str == "fcvt.l.s":
            return rv64f_fcvtls(self.rd, self.frs1, self.rm)
        elif self.instr_str == "fcvt.lu.s":
            return rv64f_fcvtlus(self.rd, self.frs1, self.rm)
        # rv32d
        elif self.instr_str == "fcvt.w.d":
            return rv32d_fcvtwd(self.rd, self.frs1, self.rm)
        # rv32d
        elif self.instr_str == "fcvt.wu.d":
            return rv32d_fcvtwud(self.rd, self.frs1, self.rm)
        # rv64d
        elif self.instr_str == "fcvt.l.d":
            return rv64d_fcvtld(self.rd, self.frs1, self.rm)
        elif self.instr_str == "fcvt.lu.d":
            return rv64d_fcvtlud(self.rd, self.frs1, self.rm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")


# Int to float instructions
IntToFloatInstructions = ("fcvt.s.w", "fcvt.s.wu", "fcvt.s.l", "fcvt.s.lu", "fcvt.d.w", "fcvt.d.wu", "fcvt.d.l", "fcvt.d.lu")
class IntToFloatInstruction(CFInstruction):
    authorized_instr_strs = IntToFloatInstructions

    def __init__(self, instr_str: str, frd: int, rs1: int, rm: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rm >= 0
            assert rm < 8
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
        self.rs1 = rs1
        self.frd = frd
        self.rm  = rm

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fcvt.s.w":
            return rv32f_fcvtsw(self.frd, self.rs1, self.rm)
        elif self.instr_str == "fcvt.s.wu":
            return rv32f_fcvtswu(self.frd, self.rs1, self.rm)
        # rv64f
        elif self.instr_str == "fcvt.s.l":
            return rv64f_fcvtsl(self.frd, self.rs1, self.rm)
        elif self.instr_str == "fcvt.s.lu":
            return rv64f_fcvtslu(self.frd, self.rs1, self.rm)
        # rv32d
        elif self.instr_str == "fcvt.d.w":
            return rv32d_fcvtdw(self.frd, self.rs1, self.rm)
        elif self.instr_str == "fcvt.d.wu":
            return rv32d_fcvtdwu(self.frd, self.rs1, self.rm)
        # rv64d
        elif self.instr_str == "fcvt.d.l":
            return rv64d_fcvtdl(self.frd, self.rs1, self.rm)
        elif self.instr_str == "fcvt.d.lu":
            return rv64d_fcvtdlu(self.frd, self.rs1, self.rm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Pure float instructions with frs1, frs2, frs3 and frd
Float4Instructions = ("fmadd.s", "fmsub.s", "fnmsub.s", "fnmadd.s", "fmadd.d", "fmsub.d", "fnmsub.d", "fnmadd.d")
class Float4Instruction(CFInstruction):
    authorized_instr_strs = Float4Instructions

    def __init__(self, instr_str: str, frd: int, frs1: int, frs2: int, frs3: int, rm: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rm >= 0
            assert rm < 8
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert frs2 >= 0
            assert frs2 < MAX_NUM_PICKABLE_REGS
            assert frs3 >= 0
            assert frs3 < MAX_NUM_PICKABLE_REGS
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
        self.rm   = rm
        self.frs1 = frs1
        self.frs2 = frs2
        self.frs3 = frs3
        self.frd  = frd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fmadd.s":
            return rv32f_fmadds(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        elif self.instr_str == "fmsub.s":
            return rv32f_fmsubs(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        elif self.instr_str == "fnmsub.s":
            return rv32f_fnmsubs(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        elif self.instr_str == "fnmadd.s":
            return rv32f_fnmadds(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        # rv32d
        elif self.instr_str == "fmadd.d":
            return rv32d_fmaddd(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        elif self.instr_str == "fmsub.d":
            return rv32d_fmsubd(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        elif self.instr_str == "fnmsub.d":
            return rv32d_fnmsubd(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        elif self.instr_str == "fnmadd.d":
            return rv32d_fnmaddd(self.frd, self.frs1, self.frs2, self.frs3, self.rm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Pure float instructions with frs1, frs2 and frd
Float3Instructions = ("fadd.s", "fsub.s", "fmul.s", "fdiv.s", "fadd.d", "fsub.d", "fmul.d", "fdiv.d")
class Float3Instruction(CFInstruction):
    authorized_instr_strs = Float3Instructions

    def __init__(self, instr_str: str, frd: int, frs1: int, frs2: int, rm: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rm >= 0
            assert rm < 8
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert frs2 >= 0
            assert frs2 < MAX_NUM_PICKABLE_REGS
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
        self.rm   = rm
        self.frs1 = frs1
        self.frs2 = frs2
        self.frd  = frd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fadd.s":
            return rv32f_fadds(self.frd, self.frs1, self.frs2, self.rm)
        elif self.instr_str == "fsub.s":
            return rv32f_fsubs(self.frd, self.frs1, self.frs2, self.rm)
        elif self.instr_str == "fmul.s":
            return rv32f_fmuls(self.frd, self.frs1, self.frs2, self.rm)
        elif self.instr_str == "fdiv.s":
            return rv32f_fdivs(self.frd, self.frs1, self.frs2, self.rm)
        # rv32d
        elif self.instr_str == "fadd.d":
            return rv32d_faddd(self.frd, self.frs1, self.frs2, self.rm)
        elif self.instr_str == "fsub.d":
            return rv32d_fsubd(self.frd, self.frs1, self.frs2, self.rm)
        elif self.instr_str == "fmul.d":
            return rv32d_fmuld(self.frd, self.frs1, self.frs2, self.rm)
        elif self.instr_str == "fdiv.d":
            return rv32d_fdivd(self.frd, self.frs1, self.frs2, self.rm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Pure float instructions with frs1, frs2 and frd
Float3NoRmInstructions = ("fsgnj.s", "fsgnjn.s", "fsgnjx.s", "fmin.s", "fmax.s", "fsgnj.d", "fsgnjn.d", "fsgnjx.d", "fmin.d", "fmax.d")
class Float3NoRmInstruction(CFInstruction):
    authorized_instr_strs = Float3NoRmInstructions

    def __init__(self, instr_str: str, frd: int, frs1: int, frs2: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert frs2 >= 0
            assert frs2 < MAX_NUM_PICKABLE_REGS
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
        self.frs1 = frs1
        self.frs2 = frs2
        self.frd  = frd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if  self.instr_str == "fsgnj.s":
            return rv32f_fsgnjs(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fsgnjn.s":
            return rv32f_fsgnjns(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fsgnjx.s":
            return rv32f_fsgnjxs(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fmin.s":
            return rv32f_fmins(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fmax.s":
            return rv32f_fmaxs(self.frd, self.frs1, self.frs2)
        # rv32d
        if  self.instr_str == "fsgnj.d":
            return rv32d_fsgnjd(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fsgnjn.d":
            return rv32d_fsgnjnd(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fsgnjx.d":
            return rv32d_fsgnjxd(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fmin.d":
            return rv32d_fmind(self.frd, self.frs1, self.frs2)
        elif self.instr_str == "fmax.d":
            return rv32d_fmaxd(self.frd, self.frs1, self.frs2)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Pure float instructions with frs1, and frd
Float2Instructions = ("fsqrt.s", "fsqrt.d", "fcvt.d.s", "fcvt.s.d")
class Float2Instruction(CFInstruction):
    authorized_instr_strs = Float2Instructions

    def __init__(self, instr_str: str, frd: int, frs1: int, rm: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rm >= 0
            assert rm < 8
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
        self.rm   = rm
        self.frs1 = frs1
        self.frd  = frd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fsqrt.s":
            return rv32f_fsqrts(self.frd, self.frs1, self.rm)
        # rv32d
        elif self.instr_str == "fsqrt.d":
            return rv32d_fsqrtd(self.frd, self.frs1, self.rm)
        # rv32d
        elif self.instr_str == "fcvt.d.s":
            return rv32d_fcvtds(self.frd, self.frs1, self.rm)
        # rv32d
        elif self.instr_str == "fcvt.s.d":
            return rv32d_fcvtsd(self.frd, self.frs1, self.rm)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Flating point instructions of 2 source floats but an integer destination
FloatIntRd2Instructions = ("feq.s", "flt.s", "fle.s", "feq.d", "flt.d", "fle.d")
class FloatIntRd2Instruction(CFInstruction):
    authorized_instr_strs = FloatIntRd2Instructions

    def __init__(self, instr_str: str, rd: int, frs1: int, frs2: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert frs2 >= 0
            assert frs2 < MAX_NUM_PICKABLE_REGS
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
        self.frs1 = frs1
        self.frs2 = frs2
        self.rd   = rd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "feq.s":
            return rv32f_feqs(self.rd, self.frs1, self.frs2)
        elif self.instr_str == "flt.s":
            return rv32f_flts(self.rd, self.frs1, self.frs2)
        elif self.instr_str == "fle.s":
            return rv32f_fles(self.rd, self.frs1, self.frs2)
        # rv32d
        elif self.instr_str == "feq.d":
            return rv32d_feqd(self.rd, self.frs1, self.frs2)
        elif self.instr_str == "flt.d":
            return rv32d_fltd(self.rd, self.frs1, self.frs2)
        elif self.instr_str == "fle.d":
            return rv32d_fled(self.rd, self.frs1, self.frs2)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Flating point instructions of 1 source float but an integer destination
FloatIntRd1Instructions = ("fmv.x.w", "fclass.s", "fclass.d", "fmv.x.d")
class FloatIntRd1Instruction(CFInstruction):
    authorized_instr_strs = FloatIntRd1Instructions

    def __init__(self, instr_str: str, rd: int, frs1: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert frs1 >= 0
            assert frs1 < MAX_NUM_PICKABLE_REGS
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
        self.frs1 = frs1
        self.rd   = rd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fmv.x.w":
            return rv32f_fmvxw(self.rd, self.frs1)
        elif self.instr_str == "fclass.s":
            return rv32f_fclasss(self.rd, self.frs1)
        # rv32d
        elif self.instr_str == "fclass.d":
            return rv32d_fclassd(self.rd, self.frs1)
        # rv64d
        elif self.instr_str == "fmv.x.d":
            return rv64d_fmvxd(self.rd, self.frs1)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# Flating point instructions of 1 source int but a float destination
FloatIntRs1Instructions = ("fmv.w.x", "fmv.d.x")
class FloatIntRs1Instruction(CFInstruction):
    authorized_instr_strs = FloatIntRs1Instructions

    def __init__(self, instr_str: str, frd: int, rs1: int, is_design_64bit: bool, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        if DO_ASSERT:
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS
            assert frd >= 0
            assert frd < MAX_NUM_PICKABLE_REGS
        self.rs1 = rs1
        self.frd = frd

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32f
        if self.instr_str == "fmv.w.x":
            return rv32f_fmvwx(self.frd, self.rs1)
        # rv64d
        elif self.instr_str == "fmv.d.x":
            return rv64d_fmvdx(self.frd, self.rs1)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

###
# Atomic instructions
###

# Atomic instructions are not yet supported.

###
# CSR instructions
###

# Any instruction with an immediate
class CSRInstruction(CFInstruction):
    # static
    authorized_instr_strs = ("csrrw", "csrrs", "csrrc", "csrrwi", "csrrsi", "csrrci")
    # Checks the immediate size.
    def assert_csr_size(self):
        if DO_ASSERT:
            assert hasattr(self, 'csr_id')
            assert self.csr_id >= 0
            assert self.csr_id <  1 << 12

    def __init__(self, instr_str: str, csr_id: int, iscompressed: bool = False):
        super().__init__(instr_str, iscompressed)
        self.csr_id = csr_id
        self.assert_csr_size()

# CSR operations without immediate
CSRRegInstructions = "csrrw", "csrrs", "csrrc"
class CSRRegInstruction(CSRInstruction):
    authorized_instr_strs = CSRRegInstructions

    def __init__(self, instr_str: str, rd: int, rs1: int, csr_id: int, iscompressed: bool = False):
        super().__init__(instr_str, csr_id, iscompressed)
        if DO_ASSERT:
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS, f"rd: {rd}, MAX_NUM_PICKABLE_REGS: {MAX_NUM_PICKABLE_REGS}"
            assert rs1 >= 0
            assert rs1 < MAX_NUM_PICKABLE_REGS or rs1 in (FPU_ENDIS_REGISTER_ID, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID), f"rs1: {rs1}, MAX_NUM_PICKABLE_REGS: {MAX_NUM_PICKABLE_REGS}"
        self.rd  = rd
        self.rs1 =  rs1

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "csrrw":
            return zicsr_csrrw(self.rd, self.rs1, self.csr_id)
        elif self.instr_str == "csrrs":
            return zicsr_csrrs(self.rd, self.rs1, self.csr_id)
        elif self.instr_str == "csrrc":
            return zicsr_csrrc(self.rd, self.rs1, self.csr_id)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")

# CSR operations with immediate
CSRImmInstructions = "csrrwi", "csrrsi", "csrrci"
class CSRImmInstruction(CSRInstruction):
    authorized_instr_strs = CSRImmInstructions

    def __init__(self, instr_str: str, rd: int, uimm: int, csr_id: int, iscompressed: bool = False):
        super().__init__(instr_str, csr_id, iscompressed)
        if DO_ASSERT:
            assert rd >= 0
            assert rd < MAX_NUM_PICKABLE_REGS
            assert uimm >= 0
            assert uimm < 1 << 5
        self.rd   = rd
        self.uimm = uimm

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # rv32i
        if self.instr_str == "csrrwi":
            return zicsr_csrrwi(self.rd, self.uimm, self.csr_id)
        elif self.instr_str == "csrrsi":
            return zicsr_csrrsi(self.rd, self.uimm, self.csr_id)
        elif self.instr_str == "csrrci":
            return zicsr_csrrci(self.rd, self.uimm, self.csr_id)
        # Default case
        else:
            raise ValueError(f"Unexpected instruction string: `{self.instr_str}`.")


###
# Placeholder instructions
###

# For offset producers and consumers.
# The offset producers and consumers do not yet know the final immediate values, and are used differently in the spike resolution from the actual simulation.
# 1. For the spike resolution
#   a. The offset producer creates the target address (or branch decision register).
#   b. The offset consumer forwards this offset which is also the target address in this case.
# 2. For the actual simulation
#   a. The offset producer computes an offset dependent on the resolution.
#   b. The offset consumer computes the generated, target address, by making the difference between the dependent register and the offset. This instruction does not require the spike resolution to be known, but still is different between the two scenari.

# Does not inherit from CFInstruction.
class PlaceholderProducerInstr0:
    # When it is instantiated, the producer instructions do not know the offset yet, just the target address.
    def __init__(self, rd: int, producer_id: int, is_design_64bit: bool):
        self.rd = rd
        self.producer_id = producer_id
        self.relocation_offset = 0
        self.spike_resolution_offset = None
        self.rtl_offset = None
        self.is_design_64bit = is_design_64bit

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # If this is the spike resolution, then load the target address using lui
        if is_spike_resolution:
            if DO_ASSERT:
                assert self.spike_resolution_offset < (1 << 32)
            return rv32i_lui(self.rd, li_into_reg(to_unsigned(self.spike_resolution_offset, self.is_design_64bit), False)[0])
        else:
            if DO_ASSERT:
                assert self.rtl_offset is not None, "Producer0 cannot produce final bytecode because it does not yet know the final offset."
            return rv32i_lui(self.rd, li_into_reg(to_unsigned(self.rtl_offset, self.is_design_64bit), False)[0])

# Does not inherit from CFInstruction.
class PlaceholderProducerInstr1:
    # When it is instantiated, the producer instructions do not know the offset yet, just the target address.
    def __init__(self, rd: int, producer_id: int, is_design_64bit: bool):
        self.rd = rd
        self.producer_id = producer_id
        self.relocation_offset = 0
        self.spike_resolution_offset = None # Is also the target address
        self.rtl_offset = None
        self.is_design_64bit = is_design_64bit

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # If this is the spike resolution, then load the target address using addi
        if is_spike_resolution:
            if DO_ASSERT:
                assert self.spike_resolution_offset < (1 << 32)
            return rv32i_addi(self.rd, self.rd, li_into_reg(to_unsigned(self.spike_resolution_offset, self.is_design_64bit), False)[1])
        else:
            if DO_ASSERT:
                assert self.rtl_offset is not None, "Producer1 cannot produce final bytecode because it does not yet know the final rtl_offset."
            return rv32i_addi(self.rd, self.rd, li_into_reg(to_unsigned(self.rtl_offset, self.is_design_64bit), False)[1])

# Does not inherit from CFInstruction.
class PlaceholderPreConsumerInstr:
    # @param rdep: the register that creates the dependency
    def __init__(self, rdep: int):
        self.rdep = rdep

    def gen_bytecode_int(self, is_spike_resolution: bool):
        # Reduce the size of the rdep id to 30 bits
        return rv32i_and(self.rdep, self.rdep, RDEP_MASK_REGISTER_ID)

# Does not inherit from CFInstruction.
class PlaceholderConsumerInstr:
    # @param rd: the generated register, i.e., the target address for example
    # @param rdep: the register that creates the dependency
    # @param producer_id: is required to feed spike's feedback
    def __init__(self, rd: int, rdep: int, rprod: int, producer_id: int):
        self.rd = rd
        self.rdep = rdep
        self.rprod = rprod
        self.producer_id = producer_id
        self.dont_relocate_spike = False # We want to relocate spike for addresses, but not for some CSRs such as medeleg.
        # self.target_val = None

    def gen_bytecode_int(self, is_spike_resolution: bool):
        if DO_ASSERT:
            assert not self.dont_relocate_spike, "We do not yet support dont_relocate_spike because it causes other problems that cause vals to change from the DUT by an offset of 0x80000000."
        # If this is the spike resolution, then just transmit the produced register
        if is_spike_resolution:
            return rv32i_xor(self.rd, self.rprod, RELOCATOR_REGISTER_ID) # self.rprod - 0
        else:
            return rv32i_xor(self.rd, self.rdep, self.rprod) # self.rdep - self.rprod

def is_placeholder(obj):
    return isinstance(obj, PlaceholderProducerInstr0) or isinstance(obj, PlaceholderProducerInstr1) or isinstance(obj, PlaceholderPreConsumerInstr) or isinstance(obj, PlaceholderConsumerInstr)

###
# Raw data
###

class RawDataWord:
    # @param intentionally_signed: When unset, we expect a non-negative wordval
    def __init__(self, wordval: int, signed: bool = False):
        if DO_ASSERT:
            if signed:
                assert wordval >= -(1 << 31)
                assert wordval < (1 << 32), f"signed wordval: {wordval}, 1 << 32: {1 << 32}"
            else:
                assert wordval >= 0
                assert wordval < (1 << 32), f"unsigned wordval: {hex(wordval)}, 1 << 32: {hex(1 << 32)}"
        self.wordval = wordval
        if signed:
            if wordval < 0:
                self.wordval = wordval + (1 << 32)

    def gen_bytecode_int(self, is_spike_resolution: bool):
        return self.wordval

###
# For exceptions
###

# This is a superclass for exceptions. This is useful for how we generate the produced registers.
# When an exception is encountered, we find back the last corresponding tvec write and set its expected value properly.
# Inheritance from ExceptionInstruction allows us to distinguish, for example, a real JAL form a JAL to a misaligned address that should cause an exception.
# It also serves to abstract exception types in general parts of the codebase such as basicblock.py.
class ExceptionInstruction:
    # @param producer_id: Used for exceptions (typically intentionally faulty jalr/loads/stores) that require a produced register for themselves in addition to the target address (held in the corresponding tvec). Keep None if none is needed.
    # @param is_mtvec: if the exception will be handled in machine mode. If false, then stvec.
    # Remargk: is_mtvec also determines which of mepc and sepc will be set.
    def __init__(self, is_mtvec: bool, producer_id: int = None):
        self.instr_str = 'ExceptionInstruction'  # Just for compatibility with the fuzzer
        self.is_mtvec = is_mtvec
        self.producer_id = producer_id

class SimpleIllegalInstruction(ExceptionInstruction):
    def __init__(self, is_mtvec):
        super().__init__(is_mtvec, None)
    def gen_bytecode_int(self, is_spike_resolution: bool):
        return 0x00000000

# Exception that encapsulates an instruction that causes an exception, such as a misaligned JAL.
class SimpleExceptionEncapsulator(ExceptionInstruction):
    def __init__(self, is_mtvec, producer_id: int, instr):
        super().__init__(is_mtvec, producer_id)
        if DO_ASSERT:
            assert producer_id is None, "SimpleExceptionEncapsulator does not support a producer_id. If we want to support it, then we need to adapt gen_producer_id_to_tgtaddr in basicblock.py."
        self.instr = instr
    def gen_bytecode_int(self, is_spike_resolution: bool):
        return self.instr.gen_bytecode_int(is_spike_resolution)

# This is a wrapper class for a misaligned load or store.
# As opposed to usual load and store operations used above, this class chooses a consumed register by itself.
class MisalignedMemInstruction(ExceptionInstruction):
    MISALIGNED_LH  = 0
    MISALIGNED_LW  = 1
    MISALIGNED_LHU = 2
    MISALIGNED_LWU = 3
    MISALIGNED_LD  = 4
    MISALIGNED_SH  = 5
    MISALIGNED_SW  = 6
    MISALIGNED_SD  = 7
    MISALIGNED_FLW = 8 # Requires F extension
    MISALIGNED_FSW = 9
    MISALIGNED_FLD = 10 # Requires D extension
    MISALIGNED_FSD = 11

    def __init__(self, is_mtvec: bool, fuzzerstate, is_load: bool, iscompressed: bool = False):
        super().__init__(is_mtvec, None) # We compute the producer id later

        from cascade.randomize.pickreg import IntRegIndivState
        # First, choose a consumed register.
        if DO_ASSERT:
            assert fuzzerstate.intregpickstate.exists_reg_in_state(IntRegIndivState.CONSUMED)
        rs1 = fuzzerstate.intregpickstate.pick_int_reg_in_state(IntRegIndivState.CONSUMED)
        # Here, in principle no need for "self." in producer_id because it is already known by the wrapped instance.
        # But it is practical to have it here to discriminate between exceptions that require a consumed register and those that do not.
        self.producer_id = fuzzerstate.intregpickstate.get_producer_id(rs1)
        fuzzerstate.intregpickstate.set_regstate(rs1, IntRegIndivState.FREE)

        # Second, choose a random memory instruction type that can be misaligned.
        meminstr_type_weights = [
          is_load,                                       # MISALIGNED_LH
          is_load,                                       # MISALIGNED_LW
          is_load and fuzzerstate.is_design_64bit,       # MISALIGNED_LHU
          is_load and fuzzerstate.is_design_64bit,       # MISALIGNED_LWU
          is_load and fuzzerstate.is_design_64bit,       # MISALIGNED_LD
          not is_load,                                   # MISALIGNED_SH
          not is_load,                                   # MISALIGNED_SW
          (not is_load) and fuzzerstate.is_design_64bit, # MISALIGNED_SD
          is_load and fuzzerstate.design_has_fpu and fuzzerstate.is_fpu_activated,        # MISALIGNED_FLW
          (not is_load) and fuzzerstate.design_has_fpu and fuzzerstate.is_fpu_activated,  # MISALIGNED_FSW
          is_load and fuzzerstate.design_has_fpud and fuzzerstate.is_fpu_activated,       # MISALIGNED_FLD
          (not is_load) and fuzzerstate.design_has_fpud and fuzzerstate.is_fpu_activated  # MISALIGNED_FSD
        ]
        meminstr_type = random.choices(range(len(meminstr_type_weights)), meminstr_type_weights)[0]
        # Third, the destination register for loads, and the source register for stores does not matter because will not be architecturally accessed.
        random_reg = random.randrange(MAX_NUM_PICKABLE_REGS)
        # Finally, pick a readable or writable address, since page or access faults would have priority
        # if meminstr_type in (MisalignedMemInstruction.MISALIGNED_LH, MisalignedMemInstruction.MISALIGNED_LW, MisalignedMemInstruction.MISALIGNED_LHU, MisalignedMemInstruction.MISALIGNED_LWU, MisalignedMemInstruction.MISALIGNED_LD, MisalignedMemInstruction.MISALIGNED_FLW, MisalignedMemInstruction.MISALIGNED_FLD):
        memrange = 0, fuzzerstate.memsize
        # Choose a misaligned address in the range
        if meminstr_type in (MisalignedMemInstruction.MISALIGNED_LH, MisalignedMemInstruction.MISALIGNED_LHU, MisalignedMemInstruction.MISALIGNED_SH):
            curr_access_size = 2
        elif meminstr_type in (MisalignedMemInstruction.MISALIGNED_LW, MisalignedMemInstruction.MISALIGNED_LWU, MisalignedMemInstruction.MISALIGNED_SW, MisalignedMemInstruction.MISALIGNED_FLW, MisalignedMemInstruction.MISALIGNED_FSW):
            curr_access_size = 4
        else:
            curr_access_size = 8
        memrange_base, memrange_size = memrange[0], memrange[1] - memrange[0]
        if DO_ASSERT:
            assert memrange_base >= 0, "memrange_base: %d" % memrange_base
            assert memrange_base + memrange_size <= fuzzerstate.memsize, "memrange_base: %d, memrange_size: %d, fuzzerstate.memsize: %d" % (memrange_base, memrange_size, fuzzerstate.memsize)
            assert memrange_size > curr_access_size, "memrange_size: %d, curr_access_size: %d" % (memrange_size, curr_access_size)

        random_block = (random.randrange(memrange_base, memrange_base + memrange_size) // curr_access_size) * curr_access_size
        random_offset = random.randrange(1, curr_access_size)
        self.misaligned_addr = random_block + random_offset

        if DO_ASSERT:
            assert self.misaligned_addr >= memrange_base, "misaligned_addr: %d, memrange_base: %d" % (self.misaligned_addr, memrange_base)
            assert self.misaligned_addr < memrange_base + memrange_size, "misaligned_addr: %d, memrange_base: %d, memrange_size: %d" % (self.misaligned_addr, memrange_base, memrange_size)
            assert self.misaligned_addr % curr_access_size != 0, "misaligned_addr: %d, curr_access_size: %d" % (self.misaligned_addr, curr_access_size)

        # Instantiate the wrapped instruction
        imm = 0
        if meminstr_type == MisalignedMemInstruction.MISALIGNED_LH:
            self.meminstr = IntLoadInstruction("lh", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_LW:
            self.meminstr = IntLoadInstruction("lw", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_LHU:
            self.meminstr = IntLoadInstruction("lhu", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_LWU:
            self.meminstr = IntLoadInstruction("lwu", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_LD:
            if DO_ASSERT:
                assert fuzzerstate.design_has_fpu
            self.meminstr = IntLoadInstruction("ld", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_SH:
            self.meminstr = IntStoreInstruction("sh", rs1, random_reg, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_SW:
            self.meminstr = IntStoreInstruction("sw", rs1, random_reg, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_SD:
            if DO_ASSERT:
                assert fuzzerstate.design_has_fpu
            self.meminstr = IntStoreInstruction("sd", rs1, random_reg, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_FLW:
            if DO_ASSERT:
                assert fuzzerstate.design_has_fpu
            self.meminstr = FloatLoadInstruction("flw", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_FSD:
            if DO_ASSERT:
                assert fuzzerstate.design_has_fpud
            self.meminstr = FloatStoreInstruction("fsd", rs1, random_reg, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_FSW:
            if DO_ASSERT:
                assert fuzzerstate.design_has_fpu
            self.meminstr = FloatStoreInstruction("fsw", rs1, random_reg, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        elif meminstr_type == MisalignedMemInstruction.MISALIGNED_FLD:
            if DO_ASSERT:
                assert fuzzerstate.design_has_fpud
            self.meminstr = FloatLoadInstruction("fld", random_reg, rs1, imm, self.producer_id, fuzzerstate.is_design_64bit, iscompressed)
        else:
            raise NotImplementedError('Unsupported meminstrtype: ' + str(meminstr_type))
        # print('Generated misaligned memory instruction: ' + str(self.meminstr.instr_str), 'misaligned address', hex(self.misaligned_addr))

    def gen_bytecode_int(self, is_spike_resolution: bool):
        return self.meminstr.gen_bytecode_int(is_spike_resolution)


###
# CSR writers
###

# @remark we use a specific instruction for xtvec to find them easily when an exception occurs, to transmit back the expected value to the producer
# @brief this instruction writes to mtvec or stvec
class TvecWriterInstruction():
    def __init__(self, is_mtvec: bool, rd: int, rs1: int, producer_id: int):
        self.instr_str = 'TvecWriterInstruction'  # Just for compatibility with the fuzzer

        self.producer_id = producer_id
        self.is_mtvec = is_mtvec # A bit redundant with the content of csr_instr, but practical.

        csr_id = CSR_IDS.MTVEC if is_mtvec else CSR_IDS.STVEC
        self.csr_instr = CSRRegInstruction("csrrw", rd, rs1, csr_id)

    def gen_bytecode_int(self, is_spike_resolution: bool):
        return self.csr_instr.gen_bytecode_int(is_spike_resolution)

# @remark we use a specific instruction for xtvec to find them easily when an exception occurs, to transmit back the expected value to the producer
# @brief this instruction writes to mepc or sepc
class EPCWriterInstruction():
    def __init__(self, is_mepc: bool, rd: int, rs1: int, producer_id: int):
        self.instr_str = 'EPCWriterInstruction'  # Just for compatibility with the fuzzer

        self.producer_id = producer_id
        self.is_mepc = is_mepc # A bit redundant with the content of csr_instr, but practical.

        csr_id = CSR_IDS.MEPC if is_mepc else CSR_IDS.SEPC
        self.csr_instr = CSRRegInstruction("csrrw", rd, rs1, csr_id)

    def gen_bytecode_int(self, is_spike_resolution: bool):
        return self.csr_instr.gen_bytecode_int(is_spike_resolution)

# @brief this instruction writes to mtvec or stvec
# @The value written may differ between Spike and CPU
class GenericCSRWriterInstruction():
    def __init__(self, csr_id: int, rd: int, rs1: int, producer_id: int, val_to_write_spike: int, val_to_write_cpu: int):
        if DO_ASSERT:
            assert csr_id in CSR_IDS
            # These two CSRs are treated separately in TvecWriterInstruction
            assert csr_id != CSR_IDS.MTVEC and csr_id != CSR_IDS.STVEC
            # Currently to ease analysis, we impose val_to_write_spike == val_to_write_cpu

        self.instr_str = 'GenericCSRWriterInstruction' # Just for compatibility with the fuzzer

        self.producer_id = producer_id
        self.val_to_write_spike = val_to_write_spike
        self.val_to_write_cpu = val_to_write_cpu

        self.csr_instr = CSRRegInstruction("csrrw", rd, rs1, csr_id)

    def gen_bytecode_int(self, is_spike_resolution: bool):
        return self.csr_instr.gen_bytecode_int(is_spike_resolution)

class PrivilegeDescentInstruction():
    def __init__(self, is_mret: bool):
        self.instr_str = 'PrivilegeDescentInstruction' # Just for compatibility with the fuzzer
        self.is_mret = is_mret

    def gen_bytecode_int(self, is_spike_resolution: bool):
        if self.is_mret:
            return rvprivileged_mret()
        else:
            return rvprivileged_sret()
