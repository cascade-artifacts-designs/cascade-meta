# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV64M_OPCODE_MUL = 0b0111011

# All functions return uint32_t

def rv64m_mulw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64M_OPCODE_MUL, rd, 0b000, rs1, rs2, 0b1)
def rv64m_divw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64M_OPCODE_MUL, rd, 0b100, rs1, rs2, 0b1)
def rv64m_divuw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64M_OPCODE_MUL, rd, 0b101, rs1, rs2, 0b1)
def rv64m_remw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64M_OPCODE_MUL, rd, 0b110, rs1, rs2, 0b1)
def rv64m_remuw(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV64M_OPCODE_MUL, rd, 0b111, rs1, rs2, 0b1)
