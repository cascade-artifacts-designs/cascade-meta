# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import DO_ASSERT

# @return uint32_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @param rs2: uint8_t
# @param funct7: uint8_t
def instruc_rtype(opcode: int, rd: int, funct3: int, rs1: int, rs2: int, funct7: int):
    if DO_ASSERT:
        assert(opcode >= 0)
        assert(rd >= 0)
        assert(funct3 >= 0)
        assert(rs1 >= 0)
        assert(rs2 >= 0)
        assert(funct7 >= 0)

        assert(opcode < (1 << 7))
        assert(rd < 32)
        assert(funct3 < 8)
        assert(rs1 < 32)
        assert(rs2 < 32)
        assert(funct7 < (1 << 7))

    rd_offset     = 7
    funct3_offset = rd_offset + 5
    rs1_offset    = funct3_offset + 3
    rs2_offset    = rs1_offset + 5
    funct7_offset = rs2_offset + 5

    return opcode | \
        (rd << rd_offset) | \
        (funct3 << funct3_offset) | \
        (rs1 << rs1_offset) | \
        (rs2 << rs2_offset) | \
        (funct7 << funct7_offset)

# @return uint32_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
def instruc_itype(opcode: int, rd: int, funct3: int, rs1: int, imm: int):
    if DO_ASSERT:
        assert(opcode < (1 << 7))
        assert(rd < 32)
        assert(funct3 < 8)
        assert(rs1 < 32)
        # assert(imm < (1 << 12))

        assert(opcode >= 0)
        assert(rd >= 0)
        assert(funct3 >= 0)
        assert(rs1 >= 0)
        # assert(imm >= 0)

    imm = imm & 0b111111111111

    rd_offset     = 7
    funct3_offset = rd_offset + 5
    rs1_offset    = funct3_offset + 3
    imm_offset    = rs1_offset + 5

    return opcode | \
        (rd << rd_offset) | \
        (funct3 << funct3_offset) | \
        (rs1 << rs1_offset) | \
        (imm << imm_offset)

# @return uint32_t
# @param opcode: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @param rs2: uint8_t
def instruc_stype(opcode: int, funct3: int, rs1: int, rs2: int, imm: int):
    if DO_ASSERT:
        assert(opcode < (1 << 7))
        assert(funct3 < 8)
        assert(rs1 < 32)
        assert(rs2 < 32)
        # assert(imm < (1 << 12))

        assert(opcode >= 0)
        assert(funct3 >= 0)
        assert(rs1 >= 0)
        assert(rs2 >= 0)
        # assert(imm >= 0)

    imm = imm & 0b111111111111

    imm4_0_offset = 7
    funct3_offset = imm4_0_offset + 5
    rs1_offset = funct3_offset + 3
    rs2_offset = rs1_offset + 5
    imm11_5_offset = rs2_offset + 5

    imm4_0 = imm & 0b11111
    imm11_5 = (imm >> 5) & 0b1111111

    return opcode | \
        (imm4_0 << imm4_0_offset) | \
        (funct3 << funct3_offset) | \
        (rs1 << rs1_offset) | \
        (rs2 << rs2_offset) | \
        (imm11_5 << imm11_5_offset)

# @return uint32_t
# @param opcode: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @para rs2: uint8_tm
# @param imm the lsb should be zero (will be ignored).

def instruc_btype(opcode: int, funct3: int, rs1: int, rs2: int, imm: int):
    if DO_ASSERT:
        assert(opcode < (1 << 7))
        assert(funct3 < 8)
        assert(rs1 < 32)
        assert(rs2 < 32)
        # assert(imm < (1 << 13))
        # assert(not (imm & 0b1))

        assert(opcode >= 0)
        assert(funct3 >= 0)
        assert(rs1 >= 0)
        assert(rs2 >= 0)
        # assert(imm >= 0)

    imm = imm & 0b1111111111111

    imm4_1_11_offset = 7
    funct3_offset = imm4_1_11_offset + 5
    rs1_offset = funct3_offset + 3
    rs2_offset = rs1_offset + 5
    imm12_10_5_offset = rs2_offset + 5

    imm4_1_11 = ((imm >> 11) & 1) | (((imm >> 1) & 0b1111) << 1)
    imm12_10_5 = ((imm >> 5) & 0b111111) | (((imm >> 12) & 0b1) << 6)

    return opcode | \
        (imm4_1_11 << imm4_1_11_offset) | \
        (funct3 << funct3_offset) | \
        (rs1 << rs1_offset) | \
        (rs2 << rs2_offset) | \
        (imm12_10_5 << imm12_10_5_offset)

# @return uint32_t
# @param opcode: uint8_t
# @param rd: uint8_t
def instruc_utype(opcode: int, rd: int, imm: int):
    if DO_ASSERT:
        assert(opcode < (1 << 7))
        assert(rd < 32)
        # assert(imm < (1 << 32))

        assert(opcode >= 0)
        assert(rd >= 0)
        # assert(imm >= 0)

    rd_offset = 7
    imm31_12_offset = rd_offset + 5

    imm31_12 = imm & 0b11111111111111111111

    return opcode | \
        rd << rd_offset | \
        imm31_12 << imm31_12_offset

# @return uint32_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param imm the lsb should be zero (will be ignored).
def instruc_jtype(opcode: int, rd: int, imm: int):
    if DO_ASSERT:
        assert(opcode < (1 << 7))
        assert(rd < 32)
        # assert(imm < (1 << 20))

        assert(opcode >= 0)
        assert(rd >= 0)
        # assert(imm < (1 << 21))

    rd_offset = 7
    immparts_offset = rd_offset + 5

    immparts = ((imm >> 12) & 0b11111111) | \
        (((imm >> 11) & 0b1) << 8) | \
        (((imm >> 1) & 0b1111111111) << 9) | \
        (((imm >> 20) & 0b1) << 19)

    return opcode | \
        rd << rd_offset | \
        immparts << immparts_offset

# @return uint32_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @param rs2: uint8_t
# @param rs3: uint8_t
# @param funct2: uint8_t
def instruc_r4type(opcode: int, rd: int, funct3: int, rs1: int, rs2: int, rs3: int, funct2: int):
    if DO_ASSERT:
        assert(opcode < (1 << 7))
        assert(rd < 32)
        assert(funct3 < 8)
        assert(rs1 < 32)
        assert(rs2 < 32)
        assert(rs3 < 32)
        assert(funct2 < (1 << 2))

        assert(opcode >= 0)
        assert(rd >= 0)
        assert(funct3 >= 0)
        assert(rs1 >= 0)
        assert(rs2 >= 0)
        assert(rs3 >= 0)
        assert(funct2 >= 0)

    rd_offset     = 7
    funct3_offset = rd_offset + 5
    rs1_offset    = funct3_offset + 3
    rs2_offset    = rs1_offset + 5
    funct2_offset = rs2_offset + 5
    rs3_offset = funct2_offset + 2

    return opcode | \
        (rd << rd_offset) | \
        (funct3 << funct3_offset) | \
        (rs1 << rs1_offset) | \
        (rs2 << rs2_offset) | \
        (funct2 << funct2_offset) | \
        (rs3 << rs3_offset)

###########################
# Compressed instructions
###########################

# @return uint16_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param rs2: uint8_t
# @param funct4: uint8_t
def instruc_crtype(opcode: int, rs2: int, rds1: int, funct4: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rs2 < 32)
        assert(rds1 < 32)
        assert(funct4 < (1 << 4))

        assert(opcode >= 0)
        assert(rs2 >= 0)
        assert(rds1 >= 0)
        assert(funct4 >= 0)

    rs2_offset = 2
    rds1_offset = rs2_offset + 5
    funct4_offset = rds1_offset + 5

    return opcode | \
        (rs2 << rs2_offset) | \
        (rds1 << rds1_offset) | \
        (funct4 << funct4_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param funct3: uint8_t
# @param imm: uint8_t
def instruc_citype(opcode: int, rds1: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rds1 < 32)
        assert(funct3 < (1 << 3))
    # assert(imm < (1 << 6)) Do not check because immediate may be signed. We could check that all bits above are all 0s or all 1s.

    imm4_0_offset = 2
    rds1_offset = imm4_0_offset + 5
    imm5_offset = rds1_offset + 5
    funct3_offset = imm5_offset + 1

    imm4_0 = imm & 0x1F
    imm5 = (imm >> 5) & 0x1

    return opcode | \
        (imm4_0 << imm4_0_offset) | \
        (rds1 << rds1_offset) | \
        (imm5 << imm5_offset) | \
        (funct3 << funct3_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param funct3: uint8_t
# @param rs2: uint8_t
def instruc_csstype(opcode: int, rs2: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rs2 < 32)
        assert(funct3 < (1 << 3))
        assert(imm < (1 << 7))

    rs2_offset = 2
    imm_offset = rs2_offset + 5
    funct3_offset = imm_offset + 6

    return opcode | \
        (rs2 << rs2_offset) | \
        (imm << imm_offset) | \
        (funct3 << funct3_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param funct3: uint8_t
def instruc_ciwtype(opcode: int, rdprime: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rdprime < 8)
        assert(funct3 < (1 << 3))
        assert(imm < (1 << 9))

    rdprime_offset = 2
    imm_offset = rdprime_offset + 3
    funct3_offset = imm_offset + 9

    return opcode | \
        (rdprime << rdprime_offset) | \
        (imm << imm_offset) | \
        (funct3 << funct3_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @param imm: uint8_t
def instruc_cltype(opcode: int, rdprime: int, rs1prime: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rdprime < 8)
        assert(rs1prime < 8)
        assert(funct3 < (1 << 3))
        assert(imm < (1 << 5))

    rdprime_offset = 2
    imm1_0_offset = rdprime_offset + 3
    rs1prime_offset = imm1_0_offset + 2
    imm4_2_offset = rs1prime_offset + 3
    funct3_offset = imm4_2_offset + 3

    imm1_0 = imm & 0x3
    imm4_2 = (imm >> 2) & 0x7

    return opcode | \
        (rdprime << rdprime_offset) | \
        (imm1_0 << imm1_0_offset) | \
        (rs1prime << rs1prime_offset) | \
        (imm4_2 << imm4_2_offset) | \
        (funct3 << funct3_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @param rs2: uint8_t
# @param imm: uint8_t
def instruc_cstype(opcode: int, rs1prime: int, rs2prime: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rs1prime < 8)
        assert(rs2prime < 8)
        assert(funct3 < (1 << 3))
        assert(imm < (1 << 5))

    rs2prime_offset = 2
    imm1_0_offset = rs2prime_offset + 3
    rs1prime_offset = imm1_0_offset + 2
    imm4_2_offset = rs1prime_offset + 3
    funct3_offset = imm4_2_offset + 3

    imm1_0 = imm & 0x3
    imm4_2 = (imm >> 2) & 0x7

    return opcode | \
        (rs2prime << rs2prime_offset) | \
        (imm1_0 << imm1_0_offset) | \
        (rs1prime << rs1prime_offset) | \
        (imm4_2 << imm4_2_offset) | \
        (funct3 << funct3_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param rd: uint8_t
# @param rs2: uint8_t
# @param funct2: uint8_t
# @param funct6: uint8_t
def instruc_catype(opcode: int, rs2prime: int, funct2: int, rds1prime: int, funct6: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rds1prime < 8)
        assert(rs2prime < 8)
        assert(funct2 < 4)
        assert(funct6 < (1 << 6))

    rs2prime_offset = 2
    funct2_offset = rs2prime_offset + 3
    rds1prime_offset = funct2_offset + 2
    funct6_offset = rds1prime_offset + 3

    return opcode | \
        (rs2prime << rs2prime_offset) | \
        (funct2 << funct2_offset) | \
        (rds1prime << rds1prime_offset) | \
        (funct6 << funct6_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param funct3: uint8_t
# @param rs1: uint8_t
# @param imm: uint8_t
def instruc_cbtype(opcode: int, rs1prime: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(rs1prime < 8)
        assert(funct3 < 8)

    imm4_0_offset = 2
    rs1prime_offset = imm4_0_offset + 5
    imm7_5_offset = rs1prime_offset + 3
    funct3_offset = imm7_5_offset + 3

    imm4_0 = imm & 0x1F
    imm7_5 = (imm >> 5) & 0x7

    return opcode | \
        (imm4_0 << imm4_0_offset) | \
        (rs1prime << rs1prime_offset) | \
        (imm7_5 << imm7_5_offset) | \
        (funct3 << funct3_offset)

# @return uint16_t
# @param opcode: uint8_t
# @param funct3: uint8_t
def instruc_cjtype(opcode: int, funct3: int, imm: int):
    if DO_ASSERT:
        assert(opcode < 4)
        assert(funct3 < 8)
        assert(imm < (1 << 11))

    imm_offset = 2
    funct3_offset = imm_offset + 11

    return opcode | \
        (imm << imm_offset) | \
        (funct3 << funct3_offset)
