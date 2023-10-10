# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV32I_OPCODE_LUI     = 0b0110111
RV32I_OPCODE_AUIPC   = 0b0010111
RV32I_OPCODE_JAL     = 0b1101111
RV32I_OPCODE_JALR    = 0b1100111
RV32I_OPCODE_B       = 0b1100011 # For all rv32i branches
RV32I_OPCODE_L       = 0b0000011 # For all rv32i loads
RV32I_OPCODE_S       = 0b0100011 # For all rv32i stores
RV32I_OPCODE_ALU_IMM = 0b0010011 # For all rv32i arithmetics with immediate
RV32I_OPCODE_ALU_REG = 0b0110011 # For all rv32i arithmetics without immediate
RV32I_OPCODE_FEN     = 0b0001111 # For rv32i fences
RV32I_OPCODE_E       = 0b1110011 # For rv32i ECALL and EBREAK

# All functions return uint32_t

def rv32i_lui(rd: int, imm: int):
    return rvprotoinstrs.instruc_utype(RV32I_OPCODE_LUI, rd, imm)
def rv32i_auipc(rd: int, imm: int):
    return rvprotoinstrs.instruc_utype(RV32I_OPCODE_AUIPC, rd, imm)
def rv32i_jal(rd: int, imm: int):
    return rvprotoinstrs.instruc_jtype(RV32I_OPCODE_JAL, rd, imm)
def rv32i_jalr(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_JALR, rd, 0, rs1, imm)
def rv32i_beq(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_btype(RV32I_OPCODE_B, 0b000, rs1, rs2, imm)
def rv32i_bne(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_btype(RV32I_OPCODE_B, 0b001, rs1, rs2, imm)
def rv32i_blt(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_btype(RV32I_OPCODE_B, 0b100, rs1, rs2, imm)
def rv32i_bge(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_btype(RV32I_OPCODE_B, 0b101, rs1, rs2, imm)
def rv32i_bltu(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_btype(RV32I_OPCODE_B, 0b110, rs1, rs2, imm)
def rv32i_bgeu(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_btype(RV32I_OPCODE_B, 0b111, rs1, rs2, imm)
def rv32i_lb(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_L, rd, 0b000, rs1, imm)
def rv32i_lh(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_L, rd, 0b001, rs1, imm)
def rv32i_lw(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_L, rd, 0b010, rs1, imm)
def rv32i_lbu(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_L, rd, 0b100, rs1, imm)
def rv32i_lhu(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_L, rd, 0b101, rs1, imm)
def rv32i_sb(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_stype(RV32I_OPCODE_S, 0b000, rs1, rs2, imm)
def rv32i_sh(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_stype(RV32I_OPCODE_S, 0b001, rs1, rs2, imm)
def rv32i_sw(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_stype(RV32I_OPCODE_S, 0b010, rs1, rs2, imm)
def rv32i_addi(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b000, rs1, imm)
def rv32i_slti(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b010, rs1, imm)
def rv32i_sltiu(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b011, rs1, imm)
def rv32i_xori(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b100, rs1, imm)
def rv32i_ori(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b110, rs1, imm)
def rv32i_andi(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b111, rs1, imm)
# Also works as the rv64i instruction of the same name (but with one more shamt bit)
def rv32i_slli(rd: int, rs1: int, shamt: int):
    imm = shamt
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b001, rs1, imm)
# Also works as the rv64i instruction of the same name (but with one more shamt bit)
def rv32i_srli(rd: int, rs1: int, shamt: int):
    imm = shamt
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b101, rs1, imm)
# Also works as the rv64i instruction of the same name (but with one more shamt bit)
def rv32i_srai(rd: int, rs1: int, shamt: int):
    imm = 0b010000000000 | shamt
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_ALU_IMM, rd, 0b101, rs1, imm)
def rv32i_add(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b000, rs1, rs2, 0b0000000)
def rv32i_sub(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b000, rs1, rs2, 0b0100000)
def rv32i_sll(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b001, rs1, rs2, 0b0000000)
def rv32i_slt(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b010, rs1, rs2, 0b0000000)
def rv32i_sltu(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b011, rs1, rs2, 0b0000000)
def rv32i_xor(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b100, rs1, rs2, 0b0000000)
def rv32i_srl(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b101, rs1, rs2, 0b0000000)
def rv32i_sra(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b101, rs1, rs2, 0b0100000)
def rv32i_or(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b110, rs1, rs2, 0b0000000)
def rv32i_and(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32I_OPCODE_ALU_REG, rd, 0b111, rs1, rs2, 0b0000000)
# @param imm is fm, pred and succ.
def rv32i_fence(rd: int = 0, rs1: int = 0):
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_FEN, rd, 0b000, rs1, 0b000011111111)
def rv32i_ecall():
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_E, 0, 0b000, 0, 0)
def rv32i_ebreak():
    return rvprotoinstrs.instruc_itype(RV32I_OPCODE_E, 0, 0b000, 0, 1)
