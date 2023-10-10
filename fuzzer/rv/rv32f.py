# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

RV32F_OPCODE_FLW     = 0b0000111
RV32F_OPCODE_FSW     = 0b0100111
RV32F_OPCODE_FMADDS  = 0b1000011
RV32F_OPCODE_FMSUBS  = 0b1000111
RV32F_OPCODE_FNMSUBS = 0b1001011
RV32F_OPCODE_FNMADDS = 0b1001111
RV32F_OPCODE_FALU    = 0b1010011

# All functions return uint32_t

def rv32f_flw(rd: int, rs1: int, imm: int):
    return rvprotoinstrs.instruc_itype(RV32F_OPCODE_FLW, rd, 0b010, rs1, imm)
def rv32f_fsw(rs1: int, rs2: int, imm: int):
    return rvprotoinstrs.instruc_stype(RV32F_OPCODE_FSW, 0b010, rs1, rs2, imm)
def rv32f_fmadds(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32F_OPCODE_FMADDS, rd, rm, rs1, rs2, rs3, 0)
def rv32f_fmsubs(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32F_OPCODE_FMSUBS, rd, rm, rs1, rs2, rs3, 0)
def rv32f_fnmsubs(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32F_OPCODE_FNMSUBS, rd, rm, rs1, rs2, rs3, 0)
def rv32f_fnmadds(rd: int, rs1: int, rs2: int, rs3: int, rm: int):
    return rvprotoinstrs.instruc_r4type(RV32F_OPCODE_FNMADDS, rd, rm, rs1, rs2, rs3, 0)

def rv32f_fadds(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, rs2, 0b0000000)
def rv32f_fsubs(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, rs2, 0b0000100)
def rv32f_fmuls(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, rs2, 0b0001000)
def rv32f_fdivs(rd: int, rs1: int, rs2: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, rs2, 0b0001100)
def rv32f_fsqrts(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, 0, 0b0101100)
def rv32f_fsgnjs(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b000, rs1, rs2, 0b0010000)
def rv32f_fsgnjns(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b001, rs1, rs2, 0b0010000)
def rv32f_fsgnjxs(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b010, rs1, rs2, 0b0010000)
def rv32f_fmins(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b000, rs1, rs2, 0b0010100)
def rv32f_fmaxs(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b001, rs1, rs2, 0b0010100)
def rv32f_fcvtws(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, 0b0, 0b1100000)
def rv32f_fcvtwus(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, 0b1, 0b1100000)
def rv32f_fmvxw(rd: int, rs1: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b000, rs1, 0b0, 0b1110000)
def rv32f_feqs(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b010, rs1, rs2, 0b1010000)
def rv32f_flts(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b001, rs1, rs2, 0b1010000)
def rv32f_fles(rd: int, rs1: int, rs2: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b000, rs1, rs2, 0b1010000)
def rv32f_fclasss(rd: int, rs1: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b001, rs1, 0b0, 0b1110000)
def rv32f_fcvtsw(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, 0b0, 0b1101000)
def rv32f_fcvtswu(rd: int, rs1: int, rm: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, rm, rs1, 0b1, 0b1101000)
def rv32f_fmvwx(rd: int, rs1: int):
    return rvprotoinstrs.instruc_rtype(RV32F_OPCODE_FALU, rd, 0b000, rs1, 0b0, 0b1111000)
