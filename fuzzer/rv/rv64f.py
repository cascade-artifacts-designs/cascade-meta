# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV64F_OPCODE_FCVT = 0b1010011

# All functions return uint32_t

def rv64f_fcvtls(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV64F_OPCODE_FCVT, rd, rm, rs1, 0b00010, 0b1100000)
def rv64f_fcvtlus(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV64F_OPCODE_FCVT, rd, rm, rs1, 0b00011, 0b1100000)
def rv64f_fcvtsl(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV64F_OPCODE_FCVT, rd, rm, rs1, 0b00010, 0b1101000)
def rv64f_fcvtslu(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV64F_OPCODE_FCVT, rd, rm, rs1, 0b00011, 0b1101000)
