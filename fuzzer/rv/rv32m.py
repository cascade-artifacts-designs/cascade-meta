# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV32M_OPCODE_MUL = 0b0110011

# All functions return uint32_t

def rv32m_mul(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b000, rs1, rs2, 0b1)
def rv32m_mulh(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b001, rs1, rs2, 0b1)
def rv32m_mulhsu(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b010, rs1, rs2, 0b1)
def rv32m_mulhu(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b011, rs1, rs2, 0b1)
def rv32m_div(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b100, rs1, rs2, 0b1)
def rv32m_divu(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b101, rs1, rs2, 0b1)
def rv32m_rem(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b110, rs1, rs2, 0b1)
def rv32m_remu(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32M_OPCODE_MUL, rd, 0b111, rs1, rs2, 0b1)
