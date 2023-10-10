# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV32D_OPCODE_FLD     = 0b0000111
RV32D_OPCODE_FSD     = 0b0100111
RV32D_OPCODE_FMADDD  = 0b1000011
RV32D_OPCODE_FMSUBD  = 0b1000111
RV32D_OPCODE_FNMSUBD = 0b1001011
RV32D_OPCODE_FNMADDD = 0b1001111
RV32D_OPCODE_FALU    = 0b1010011

# All functions return uint32_t

def rv32d_fld(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32D_OPCODE_FLD, rd, 0b011, rs1, imm)
def rv32d_fsd(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_stype(RV32D_OPCODE_FSD, 0b011, rs1, rs2, imm)
def rv32d_fmaddd(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32D_OPCODE_FMADDD, rd, rm, rs1, rs2, rs3, 0b01)
def rv32d_fmsubd(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32D_OPCODE_FMSUBD, rd, rm, rs1, rs2, rs3, 0b01)
def rv32d_fnmsubd(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32D_OPCODE_FNMSUBD, rd, rm, rs1, rs2, rs3, 0b01)
def rv32d_fnmaddd(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32D_OPCODE_FNMADDD, rd, rm, rs1, rs2, rs3, 0b01)

def rv32d_faddd(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, rs2, 0b0000001)
def rv32d_fsubd(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, rs2, 0b0000101)
def rv32d_fmuld(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, rs2, 0b0001001)
def rv32d_fdivd(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, rs2, 0b0001101)
def rv32d_fsqrtd(rd: int, rs1: int, rm: int) :
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0, 0b0101101)
def rv32d_fsgnjd(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b000, rs1, rs2, 0b0010001)
def rv32d_fsgnjnd(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b001, rs1, rs2, 0b0010001)
def rv32d_fsgnjxd(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b010, rs1, rs2, 0b0010001)
def rv32d_fmind(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b000, rs1, rs2, 0b0010101)
def rv32d_fmaxd(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b001, rs1, rs2, 0b0010101)
def rv32d_fcvtsd(rd: int, rs1: int, rm: int) :
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0b1, 0b0100000)
def rv32d_fcvtds(rd: int, rs1: int, rm: int) :
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0b0, 0b0100001)
def rv32d_feqd(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b010, rs1, rs2, 0b1010001)
def rv32d_fltd(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b001, rs1, rs2, 0b1010001)
def rv32d_fled(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b000, rs1, rs2, 0b1010001)
def rv32d_fclassd(rd: int, rs1: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, 0b001, rs1, 0b0, 0b1110001)
def rv32d_fcvtwd(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0b0, 0b1100001)
def rv32d_fcvtwud(rd: int, rs1: int, rm: int) :
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0b1, 0b1100001)
def rv32d_fcvtdw(rd: int, rs1: int, rm: int) :
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0b0, 0b1101001)
def rv32d_fcvtdwu(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32D_OPCODE_FALU, rd, rm, rs1, 0b1, 0b1101001)
