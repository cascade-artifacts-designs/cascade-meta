# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV64I_OPCODE_LWU     = 0b0000011
RV64I_OPCODE_LD      = 0b0000011
RV64I_OPCODE_SD      = 0b0100011
RV64I_OPCODE_ALU_IMM = 0b0011011 # For all rv64i arithmetics with immediate
RV64I_OPCODE_ALU_REG = 0b0111011 # For all rv64i arithmetics without immediate

# All functions return uint32_t

def rv64i_lwu(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV64I_OPCODE_LWU, rd, 0b110, rs1, imm)
def rv64i_ld(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV64I_OPCODE_LD, rd, 0b011, rs1, imm)
def rv64i_sd(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_stype(RV64I_OPCODE_SD, 0b011, rs1, rs2, imm)
def rv64i_addiw(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV64I_OPCODE_ALU_IMM, rd, 0b000, rs1, imm)
def rv64i_slliw(rd: int, rs1: int, shamt: int):
    imm = shamt
    return rvprotoinstrs.instruc_itype(RV64I_OPCODE_ALU_IMM, rd, 0b001, rs1, imm)
def rv64i_srliw(rd: int, rs1: int, shamt: int):
    imm = shamt
    return rvprotoinstrs.instruc_itype(RV64I_OPCODE_ALU_IMM, rd, 0b101, rs1, imm)
def rv64i_sraiw(rd: int, rs1: int, shamt: int):
    imm = 0b010000000000 | shamt
    return rvprotoinstrs.instruc_itype(RV64I_OPCODE_ALU_IMM, rd, 0b101, rs1, imm)
def rv64i_addw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64I_OPCODE_ALU_REG, rd, 0b000, rs1, rs2, 0)
def rv64i_subw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64I_OPCODE_ALU_REG, rd, 0b000, rs1, rs2, 0b0100000)
def rv64i_sllw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64I_OPCODE_ALU_REG, rd, 0b001, rs1, rs2, 0)
def rv64i_srlw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64I_OPCODE_ALU_REG, rd, 0b101, rs1, rs2, 0)
def rv64i_sraw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64I_OPCODE_ALU_REG, rd, 0b101, rs1, rs2, 0b0100000)
