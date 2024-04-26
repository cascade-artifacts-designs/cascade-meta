# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs
import random
RV32A_OPCODE_AMO = 0b0101111

# All functions return uint32_t

def rv32a_lrw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random < 0.5:
        rl = 0b1
    if aq_random < 0.5:
        aq = 0b1
    rs2 = 0b00000
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b00010)
def rv32a_scw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random<0.5:
        rl = 0b1
    if aq_random<0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b00011)

def rv32a_amoswapw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random < 0.5:
        rl = 0b1
    if aq_random < 0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b00001)

def rv32a_amoaddw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random<0.5:
        rl=0b1
    if aq_random<0.5:
        aq=0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b00000)

def rv32a_amoxorw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl=0b0
    aq=0b0
    if rl_random<0.5:
        rl = 0b1
    if aq_random<0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b00100)

def rv32a_amoandw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random<0.5:
        rl = 0b1
    if aq_random<0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b01100)

def rv32a_amoorw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random<0.5:
        rl = 0b1
    if aq_random<0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b01000)

def rv32a_amominw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random < 0.5:
        rl = 0b1
    if aq_random < 0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b10000)

def rv32a_amomaxw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random < 0.5:
        rl = 0b1
    if aq_random < 0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b10100)

def rv32a_amominuw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl=0b0
    aq=0b0
    if rl_random < 0.5:
        rl = 0b1
    if aq_random < 0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b11000)

def rv32a_amomaxuw(rd: int, rs1: int, rs2: int):
    rl_random = random.random()
    aq_random = random.random()
    rl = 0b0
    aq = 0b0
    if rl_random < 0.5:
        rl = 0b1
    if aq_random < 0.5:
        aq = 0b1
    return rvprotoinstrs.instruc_amotype(RV32A_OPCODE_AMO, rd, 0b010, rs1, rs2, rl, aq, 0b11100)