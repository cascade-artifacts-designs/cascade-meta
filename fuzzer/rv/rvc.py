# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# RISC-V "C" extension (compressed instructions) encoders.
#
# The Cascade fuzzer keeps each instruction "slot" 4-byte aligned. To exercise
# the RVC decoder without disturbing the existing alignment, branch range and
# producer/consumer infrastructure, we pack a single 16-bit compressed
# instruction together with a c.nop into a single 4-byte slot:
#
#     +----------------+----------------+
#     | c.nop (16-bit) | RVC instr (16) |   stored little-endian => low half = RVC
#     +----------------+----------------+
#
# When the slot's CF instruction is taken (c.j / c.jal / c.jr / c.jalr / c.beqz
# taken / c.bnez taken), control transfers before the c.nop is reached. When
# the CF is not taken or the slot is non-CF, the c.nop is decoded and retired
# but has no architectural effect: the resulting state at slot+4 matches the
# semantically equivalent uncompressed instruction.
#
# Each helper here returns a uint16; ``pack_with_cnop`` lifts that into the
# uint32 placed in the slot.

from params.runparams import DO_ASSERT

# c.nop = addi x0, x0, 0 == 0x0001
C_NOP = 0x0001

# ---------------------------------------------------------------------------
# Low-level format helpers
# ---------------------------------------------------------------------------

def _check_bits(val: int, nbits: int, signed: bool = False, name: str = 'val'):
    if not DO_ASSERT:
        return
    if signed:
        assert -(1 << (nbits - 1)) <= val < (1 << (nbits - 1)), \
            f"{name}={val} out of signed {nbits}-bit range"
    else:
        assert 0 <= val < (1 << nbits), \
            f"{name}={val} out of unsigned {nbits}-bit range"


def _cr(opcode: int, rs2: int, rds1: int, funct4: int) -> int:
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rs2 < 32
        assert 0 <= rds1 < 32
        assert 0 <= funct4 < 16
    return opcode | (rs2 << 2) | (rds1 << 7) | (funct4 << 12)


def _ci(opcode: int, rds1: int, funct3: int, imm6: int) -> int:
    """CI: imm split as imm[5] @12, imm[4:0] @[6:2]; rds1 @[11:7]."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rds1 < 32
        assert 0 <= funct3 < 8
        assert 0 <= imm6 < 64
    return opcode | ((imm6 & 0x1F) << 2) | (rds1 << 7) | (((imm6 >> 5) & 1) << 12) | (funct3 << 13)


def _css(opcode: int, rs2: int, funct3: int, imm6: int) -> int:
    """CSS: imm @[12:7], rs2 @[6:2]."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rs2 < 32
        assert 0 <= funct3 < 8
        assert 0 <= imm6 < 64
    return opcode | (rs2 << 2) | (imm6 << 7) | (funct3 << 13)


def _ciw(opcode: int, rdp: int, funct3: int, imm8: int) -> int:
    """CIW: rd' @[4:2], imm @[12:5]."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rdp < 8
        assert 0 <= funct3 < 8
        assert 0 <= imm8 < 256
    return opcode | (rdp << 2) | (imm8 << 5) | (funct3 << 13)


def _cl(opcode: int, rdp: int, rs1p: int, funct3: int, imm5: int) -> int:
    """CL: rd' @[4:2], imm[1:0] @[6:5], rs1' @[9:7], imm[4:2] @[12:10]."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rdp < 8
        assert 0 <= rs1p < 8
        assert 0 <= funct3 < 8
        assert 0 <= imm5 < 32
    imm10 = imm5 & 0x3
    imm432 = (imm5 >> 2) & 0x7
    return opcode | (rdp << 2) | (imm10 << 5) | (rs1p << 7) | (imm432 << 10) | (funct3 << 13)


def _cs(opcode: int, rs1p: int, rs2p: int, funct3: int, imm5: int) -> int:
    """CS: rs2' @[4:2], imm[1:0] @[6:5], rs1' @[9:7], imm[4:2] @[12:10]."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rs1p < 8
        assert 0 <= rs2p < 8
        assert 0 <= funct3 < 8
        assert 0 <= imm5 < 32
    imm10 = imm5 & 0x3
    imm432 = (imm5 >> 2) & 0x7
    return opcode | (rs2p << 2) | (imm10 << 5) | (rs1p << 7) | (imm432 << 10) | (funct3 << 13)


def _ca(opcode: int, rs2p: int, funct2: int, rds1p: int, funct6: int) -> int:
    """CA: rs2' @[4:2], funct2 @[6:5], rds1' @[9:7], funct6 @[15:10]."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rs2p < 8
        assert 0 <= rds1p < 8
        assert 0 <= funct2 < 4
        assert 0 <= funct6 < 64
    return opcode | (rs2p << 2) | (funct2 << 5) | (rds1p << 7) | (funct6 << 10)


def _cb_branch(opcode: int, rs1p: int, funct3: int, imm9: int) -> int:
    """CB (c.beqz / c.bnez): imm[8|4:3] @[12:10], rs1' @[9:7], imm[7:6|2:1|5] @[6:2].

    imm9 is the byte offset, must be 2-byte aligned and fit in signed 9 bits.
    """
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rs1p < 8
        assert 0 <= funct3 < 8
        assert -(1 << 8) <= imm9 < (1 << 8)
        assert (imm9 & 1) == 0
    u = imm9 & 0x1FF
    bit8 = (u >> 8) & 1
    bit7_6 = (u >> 6) & 0x3
    bit5 = (u >> 5) & 1
    bit4_3 = (u >> 3) & 0x3
    bit2_1 = (u >> 1) & 0x3
    high = (bit8 << 2) | bit4_3   # 3 bits @[12:10]
    low = (bit7_6 << 3) | (bit2_1 << 1) | bit5  # 5 bits @[6:2]
    return opcode | (low << 2) | (rs1p << 7) | (high << 10) | (funct3 << 13)


def _cb_alu(opcode: int, rs1p: int, funct3: int, funct2: int, imm6: int) -> int:
    """CB form used by c.srli / c.srai / c.andi.

    funct2 selects the sub-op (00=srli, 01=srai, 10=andi). For srli/srai the
    immediate is treated as unsigned (shamt); for andi it is signed.
    Layout: imm[5] @12, funct2 @[11:10], rs1' @[9:7], imm[4:0] @[6:2].
    """
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= rs1p < 8
        assert 0 <= funct3 < 8
        assert 0 <= funct2 < 4
        assert -(1 << 5) <= imm6 < (1 << 6)
    bit5 = (imm6 >> 5) & 1
    bits4_0 = imm6 & 0x1F
    return opcode | (bits4_0 << 2) | (rs1p << 7) | (funct2 << 10) | (bit5 << 12) | (funct3 << 13)


def _cj(opcode: int, funct3: int, imm12: int) -> int:
    """CJ (c.j / c.jal): byte offset, must be 2-byte aligned, signed 12 bits."""
    if DO_ASSERT:
        assert 0 <= opcode < 4
        assert 0 <= funct3 < 8
        assert -(1 << 11) <= imm12 < (1 << 11)
        assert (imm12 & 1) == 0
    u = imm12 & 0xFFF
    b11 = (u >> 11) & 1
    b10 = (u >> 10) & 1
    b9_8 = (u >> 8) & 0x3
    b7 = (u >> 7) & 1
    b6 = (u >> 6) & 1
    b5 = (u >> 5) & 1
    b4 = (u >> 4) & 1
    b3_1 = (u >> 1) & 0x7
    # Spec layout from MSB: [11|4|9:8|10|6|7|3:1|5]
    field = (b11 << 10) | (b4 << 9) | (b9_8 << 7) | (b10 << 6) | (b6 << 5) | (b7 << 4) | (b3_1 << 1) | b5
    return opcode | (field << 2) | (funct3 << 13)


# ---------------------------------------------------------------------------
# Public encoders
# ---------------------------------------------------------------------------

# Quadrant 1 ALU
def c_addi(rd: int, imm: int) -> int:
    if DO_ASSERT:
        assert rd != 0
        assert imm != 0
        assert -32 <= imm < 32
    return _ci(0b01, rd, 0b000, imm & 0x3F)


def c_addiw(rd: int, imm: int) -> int:
    if DO_ASSERT:
        assert rd != 0
        assert -32 <= imm < 32
    return _ci(0b01, rd, 0b001, imm & 0x3F)


def c_li(rd: int, imm: int) -> int:
    if DO_ASSERT:
        assert rd != 0
        assert -32 <= imm < 32
    return _ci(0b01, rd, 0b010, imm & 0x3F)


def c_lui(rd: int, imm: int) -> int:
    """``imm`` is the LUI-style 20-bit immediate field (placed into rd[31:12]
    by the regular lui instruction). c.lui only encodes the low 6 bits of that
    field; the caller is responsible for ensuring the high 14 bits sign-extend
    bit 5.
    """
    if DO_ASSERT:
        assert rd != 0 and rd != 2
    imm6 = imm & 0x3F
    if DO_ASSERT:
        assert imm6 != 0
    return _ci(0b01, rd, 0b011, imm6)


def c_addi16sp(imm: int) -> int:
    if DO_ASSERT:
        assert imm != 0
        assert (imm & 0xF) == 0
        assert -512 <= imm < 512
    # Spec-mandated bit ordering for the 6-bit field
    bit9 = (imm >> 9) & 1
    bit8_7 = (imm >> 7) & 0x3
    bit6 = (imm >> 6) & 1
    bit5 = (imm >> 5) & 1
    bit4 = (imm >> 4) & 1
    field6 = (bit9 << 5) | (bit4 << 4) | (bit6 << 3) | (bit8_7 << 1) | bit5
    return _ci(0b01, 2, 0b011, field6)


def c_addi4spn(rdp: int, imm: int) -> int:
    if DO_ASSERT:
        assert imm != 0
        assert (imm & 0x3) == 0
        assert 0 < imm < (1 << 10)
    bit5_4 = (imm >> 4) & 0x3
    bit9_6 = (imm >> 6) & 0xF
    bit2 = (imm >> 2) & 1
    bit3 = (imm >> 3) & 1
    field8 = (bit5_4 << 6) | (bit9_6 << 2) | (bit2 << 1) | bit3
    return _ciw(0b00, rdp, 0b000, field8)


def c_slli(rd: int, shamt: int) -> int:
    if DO_ASSERT:
        assert rd != 0
        assert 0 < shamt < 64
    return _ci(0b10, rd, 0b000, shamt & 0x3F)


def c_srli(rdp: int, shamt: int) -> int:
    if DO_ASSERT:
        assert 0 < shamt < 64
    return _cb_alu(0b01, rdp, 0b100, 0b00, shamt)


def c_srai(rdp: int, shamt: int) -> int:
    if DO_ASSERT:
        assert 0 < shamt < 64
    return _cb_alu(0b01, rdp, 0b100, 0b01, shamt)


def c_andi(rdp: int, imm: int) -> int:
    if DO_ASSERT:
        assert -32 <= imm < 32
    return _cb_alu(0b01, rdp, 0b100, 0b10, imm)


def c_and(rdp: int, rs2p: int) -> int:
    return _ca(0b01, rs2p, 0b11, rdp, 0b100011)


def c_or(rdp: int, rs2p: int) -> int:
    return _ca(0b01, rs2p, 0b10, rdp, 0b100011)


def c_xor(rdp: int, rs2p: int) -> int:
    return _ca(0b01, rs2p, 0b01, rdp, 0b100011)


def c_sub(rdp: int, rs2p: int) -> int:
    return _ca(0b01, rs2p, 0b00, rdp, 0b100011)


def c_addw(rdp: int, rs2p: int) -> int:
    return _ca(0b01, rs2p, 0b01, rdp, 0b100111)


def c_subw(rdp: int, rs2p: int) -> int:
    return _ca(0b01, rs2p, 0b00, rdp, 0b100111)


def c_mv(rd: int, rs2: int) -> int:
    if DO_ASSERT:
        assert rd != 0 and rs2 != 0
    return _cr(0b10, rs2, rd, 0b1000)


def c_add(rd: int, rs2: int) -> int:
    if DO_ASSERT:
        assert rd != 0 and rs2 != 0
    return _cr(0b10, rs2, rd, 0b1001)


# Loads / stores
def c_lwsp(rd: int, uimm: int) -> int:
    if DO_ASSERT:
        assert rd != 0
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 8)
    bit5 = (uimm >> 5) & 1
    bit4_2 = (uimm >> 2) & 0x7
    bit7_6 = (uimm >> 6) & 0x3
    field6 = (bit5 << 5) | (bit4_2 << 2) | bit7_6
    return _ci(0b10, rd, 0b010, field6)


def c_ldsp(rd: int, uimm: int) -> int:
    if DO_ASSERT:
        assert rd != 0
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 9)
    bit5 = (uimm >> 5) & 1
    bit4_3 = (uimm >> 3) & 0x3
    bit8_6 = (uimm >> 6) & 0x7
    field6 = (bit5 << 5) | (bit4_3 << 3) | bit8_6
    return _ci(0b10, rd, 0b011, field6)


def c_flwsp(rd: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 8)
    bit5 = (uimm >> 5) & 1
    bit4_2 = (uimm >> 2) & 0x7
    bit7_6 = (uimm >> 6) & 0x3
    field6 = (bit5 << 5) | (bit4_2 << 2) | bit7_6
    return _ci(0b10, rd, 0b011, field6)


def c_fldsp(rd: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 9)
    bit5 = (uimm >> 5) & 1
    bit4_3 = (uimm >> 3) & 0x3
    bit8_6 = (uimm >> 6) & 0x7
    field6 = (bit5 << 5) | (bit4_3 << 3) | bit8_6
    return _ci(0b10, rd, 0b001, field6)


def c_swsp(rs2: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 8)
    bit5_2 = (uimm >> 2) & 0xF
    bit7_6 = (uimm >> 6) & 0x3
    field6 = (bit5_2 << 2) | bit7_6
    return _css(0b10, rs2, 0b110, field6)


def c_sdsp(rs2: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 9)
    bit5_3 = (uimm >> 3) & 0x7
    bit8_6 = (uimm >> 6) & 0x7
    field6 = (bit5_3 << 3) | bit8_6
    return _css(0b10, rs2, 0b111, field6)


def c_fswsp(rs2: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 8)
    bit5_2 = (uimm >> 2) & 0xF
    bit7_6 = (uimm >> 6) & 0x3
    field6 = (bit5_2 << 2) | bit7_6
    return _css(0b10, rs2, 0b111, field6)


def c_fsdsp(rs2: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 9)
    bit5_3 = (uimm >> 3) & 0x7
    bit8_6 = (uimm >> 6) & 0x7
    field6 = (bit5_3 << 3) | bit8_6
    return _css(0b10, rs2, 0b101, field6)


def c_lw(rdp: int, rs1p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 7)
    bit5_3 = (uimm >> 3) & 0x7
    bit2 = (uimm >> 2) & 1
    bit6 = (uimm >> 6) & 1
    field5 = (bit5_3 << 2) | (bit2 << 1) | bit6
    return _cl(0b00, rdp, rs1p, 0b010, field5)


def c_ld(rdp: int, rs1p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 8)
    bit5_3 = (uimm >> 3) & 0x7
    bit7_6 = (uimm >> 6) & 0x3
    field5 = (bit5_3 << 2) | bit7_6
    return _cl(0b00, rdp, rs1p, 0b011, field5)


def c_flw(rdp: int, rs1p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 7)
    bit5_3 = (uimm >> 3) & 0x7
    bit2 = (uimm >> 2) & 1
    bit6 = (uimm >> 6) & 1
    field5 = (bit5_3 << 2) | (bit2 << 1) | bit6
    return _cl(0b00, rdp, rs1p, 0b011, field5)


def c_fld(rdp: int, rs1p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 8)
    bit5_3 = (uimm >> 3) & 0x7
    bit7_6 = (uimm >> 6) & 0x3
    field5 = (bit5_3 << 2) | bit7_6
    return _cl(0b00, rdp, rs1p, 0b001, field5)


def c_sw(rs1p: int, rs2p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 7)
    bit5_3 = (uimm >> 3) & 0x7
    bit2 = (uimm >> 2) & 1
    bit6 = (uimm >> 6) & 1
    field5 = (bit5_3 << 2) | (bit2 << 1) | bit6
    return _cs(0b00, rs1p, rs2p, 0b110, field5)


def c_sd(rs1p: int, rs2p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 8)
    bit5_3 = (uimm >> 3) & 0x7
    bit7_6 = (uimm >> 6) & 0x3
    field5 = (bit5_3 << 2) | bit7_6
    return _cs(0b00, rs1p, rs2p, 0b111, field5)


def c_fsw(rs1p: int, rs2p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x3) == 0
        assert 0 <= uimm < (1 << 7)
    bit5_3 = (uimm >> 3) & 0x7
    bit2 = (uimm >> 2) & 1
    bit6 = (uimm >> 6) & 1
    field5 = (bit5_3 << 2) | (bit2 << 1) | bit6
    return _cs(0b00, rs1p, rs2p, 0b111, field5)


def c_fsd(rs1p: int, rs2p: int, uimm: int) -> int:
    if DO_ASSERT:
        assert (uimm & 0x7) == 0
        assert 0 <= uimm < (1 << 8)
    bit5_3 = (uimm >> 3) & 0x7
    bit7_6 = (uimm >> 6) & 0x3
    field5 = (bit5_3 << 2) | bit7_6
    return _cs(0b00, rs1p, rs2p, 0b101, field5)


# Control flow
def c_j(imm: int) -> int:
    return _cj(0b01, 0b101, imm)


def c_jal(imm: int) -> int:  # RV32 only
    return _cj(0b01, 0b001, imm)


def c_beqz(rs1p: int, imm: int) -> int:
    return _cb_branch(0b01, rs1p, 0b110, imm)


def c_bnez(rs1p: int, imm: int) -> int:
    return _cb_branch(0b01, rs1p, 0b111, imm)


def c_jr(rs1: int) -> int:
    if DO_ASSERT:
        assert rs1 != 0
    return _cr(0b10, 0, rs1, 0b1000)


def c_jalr(rs1: int) -> int:
    if DO_ASSERT:
        assert rs1 != 0
    return _cr(0b10, 0, rs1, 0b1001)


def c_ebreak() -> int:
    return _cr(0b10, 0, 0, 0b1001)


def c_nop() -> int:
    return C_NOP


# ---------------------------------------------------------------------------
# Slot packing
# ---------------------------------------------------------------------------

def pack_with_cnop(c_instr_low16: int) -> int:
    """Pack a 16-bit C instruction with a c.nop into a 32-bit slot value."""
    if DO_ASSERT:
        assert 0 <= c_instr_low16 < (1 << 16)
    return c_instr_low16 | (C_NOP << 16)


# ---------------------------------------------------------------------------
# Compressibility predicates
# ---------------------------------------------------------------------------

def _is_rvc_reg(r: int) -> bool:
    return 8 <= r <= 15


def _fits_signed(val: int, nbits: int) -> bool:
    return -(1 << (nbits - 1)) <= val < (1 << (nbits - 1))


def _fits_unsigned(val: int, nbits: int) -> bool:
    return 0 <= val < (1 << nbits)


# ---------------------------------------------------------------------------
# Per-instruction-class compression dispatcher
# ---------------------------------------------------------------------------

# Maps from cfinstructionclasses.* names to compression attempts. Each helper
# below receives the high-level instruction object and returns the compressed
# 16-bit encoding or ``None`` if the operands do not satisfy the RVC encoding
# constraints.

def _try_R12D(instr) -> int:
    rd, rs1, rs2 = instr.rd, instr.rs1, instr.rs2
    s = instr.instr_str
    if s == "add":
        # c.add: rd = rd + rs2, rd != 0, rs2 != 0
        if rs1 == rd and rd != 0 and rs2 != 0:
            return c_add(rd, rs2)
        # c.mv: rd = rs2, rd != 0, rs2 != 0  (here rs1 == 0 makes rd = 0+rs2)
        if rs1 == 0 and rd != 0 and rs2 != 0:
            return c_mv(rd, rs2)
        return None
    if s == "sub":
        if _is_rvc_reg(rd) and rd == rs1 and _is_rvc_reg(rs2):
            return c_sub(rd - 8, rs2 - 8)
        return None
    if s == "and":
        if _is_rvc_reg(rd) and rd == rs1 and _is_rvc_reg(rs2):
            return c_and(rd - 8, rs2 - 8)
        return None
    if s == "or":
        if _is_rvc_reg(rd) and rd == rs1 and _is_rvc_reg(rs2):
            return c_or(rd - 8, rs2 - 8)
        return None
    if s == "xor":
        if _is_rvc_reg(rd) and rd == rs1 and _is_rvc_reg(rs2):
            return c_xor(rd - 8, rs2 - 8)
        return None
    if s == "addw":
        if _is_rvc_reg(rd) and rd == rs1 and _is_rvc_reg(rs2):
            return c_addw(rd - 8, rs2 - 8)
        return None
    if s == "subw":
        if _is_rvc_reg(rd) and rd == rs1 and _is_rvc_reg(rs2):
            return c_subw(rd - 8, rs2 - 8)
        return None
    return None


def _try_ImmRd(instr) -> int:
    rd, imm = instr.rd, instr.imm
    s = instr.instr_str
    if s == "lui":
        if rd == 0 or rd == 2:
            return None
        # Cascade stores the 20-bit lui-immediate field directly; lui sign-extends
        # bit 19 across rd. c.lui only encodes 6 bits of immediate (imm20[5:0])
        # and sign-extends bit 5. To stay semantically equivalent we need
        # imm20[19:6] to be exactly the sign-extension of imm20[5].
        imm20 = imm & 0xFFFFF
        bit5 = (imm20 >> 5) & 1
        upper14 = imm20 >> 6
        if bit5:
            if upper14 != ((1 << 14) - 1):
                return None
        else:
            if upper14 != 0:
                return None
        imm6 = imm20 & 0x3F
        if imm6 == 0:
            return None
        return c_lui(rd, imm)
    return None


def _try_RegImm(instr) -> int:
    rd, rs1, imm = instr.rd, instr.rs1, instr.imm
    s = instr.instr_str
    if s == "addi":
        # c.li: rs1 == 0 and -32 <= imm < 32 and rd != 0
        if rs1 == 0 and rd != 0 and _fits_signed(imm, 6):
            return c_li(rd, imm)
        # c.addi16sp: rd == rs1 == 2, imm % 16 == 0, imm != 0, fits 10-bit signed
        if rd == 2 and rs1 == 2 and imm != 0 and (imm & 0xF) == 0 and _fits_signed(imm, 10):
            return c_addi16sp(imm)
        # c.addi4spn: rd is rvc reg, rs1 == 2, imm % 4 == 0, imm != 0, fits unsigned 10-bit
        if _is_rvc_reg(rd) and rs1 == 2 and imm != 0 and (imm & 0x3) == 0 and _fits_unsigned(imm, 10):
            return c_addi4spn(rd - 8, imm)
        # c.addi: rd == rs1, rd != 0, imm != 0, fits 6-bit signed
        if rd == rs1 and rd != 0 and imm != 0 and _fits_signed(imm, 6):
            return c_addi(rd, imm)
        return None
    if s == "addiw":
        # c.addiw: rd == rs1, rd != 0, fits 6-bit signed (imm can be 0 in addi but
        # for c.addiw the spec allows imm == 0 since it's not redundant with c.li).
        if rd == rs1 and rd != 0 and _fits_signed(imm, 6):
            return c_addiw(rd, imm)
        return None
    if s == "slli":
        if rd == rs1 and rd != 0 and 0 < imm < 64 and (instr.is_design_64bit or imm < 32):
            return c_slli(rd, imm)
        return None
    if s == "srli":
        if _is_rvc_reg(rd) and rd == rs1 and 0 < imm < 64 and (instr.is_design_64bit or imm < 32):
            return c_srli(rd - 8, imm)
        return None
    if s == "srai":
        # `imm` for srai may carry the spec's high "01" bits in some encodings;
        # cascade stores the shamt directly.
        shamt = imm & 0x3F
        if _is_rvc_reg(rd) and rd == rs1 and 0 < shamt < 64 and (instr.is_design_64bit or shamt < 32):
            return c_srai(rd - 8, shamt)
        return None
    if s == "andi":
        if _is_rvc_reg(rd) and rd == rs1 and _fits_signed(imm, 6):
            return c_andi(rd - 8, imm)
        return None
    return None


def _try_Branch(instr) -> int:
    s = instr.instr_str
    rs1, rs2, imm = instr.rs1, instr.rs2, instr.imm
    if rs2 != 0:
        return None
    if not _is_rvc_reg(rs1):
        return None
    if (imm & 1) != 0 or not _fits_signed(imm, 9):
        return None
    if s == "beq":
        return c_beqz(rs1 - 8, imm)
    if s == "bne":
        return c_bnez(rs1 - 8, imm)
    return None


def _try_JAL(instr) -> int:
    rd, imm = instr.rd, instr.imm
    if (imm & 1) != 0 or not _fits_signed(imm, 12):
        return None
    if rd == 0:
        return c_j(imm)
    # c.jal stores PC+2 in x1 instead of PC+4: skip to keep semantic equivalence.
    return None


def _try_JALR(instr) -> int:
    rd, rs1, imm = instr.rd, instr.rs1, instr.imm
    if imm != 0 or rs1 == 0:
        return None
    if rd == 0:
        return c_jr(rs1)
    # c.jalr: rd = x1, but writes PC+2 vs PC+4 — skip to keep equivalence.
    return None


def _try_IntLoad(instr) -> int:
    rd, rs1, imm = instr.rd, instr.rs1, instr.imm
    s = instr.instr_str
    if s == "lw":
        if rs1 == 2 and rd != 0 and (imm & 0x3) == 0 and _fits_unsigned(imm, 8):
            return c_lwsp(rd, imm)
        if _is_rvc_reg(rd) and _is_rvc_reg(rs1) and (imm & 0x3) == 0 and _fits_unsigned(imm, 7):
            return c_lw(rd - 8, rs1 - 8, imm)
        return None
    if s == "ld":
        if rs1 == 2 and rd != 0 and (imm & 0x7) == 0 and _fits_unsigned(imm, 9):
            return c_ldsp(rd, imm)
        if _is_rvc_reg(rd) and _is_rvc_reg(rs1) and (imm & 0x7) == 0 and _fits_unsigned(imm, 8):
            return c_ld(rd - 8, rs1 - 8, imm)
        return None
    return None


def _try_IntStore(instr) -> int:
    rs1, rs2, imm = instr.rs1, instr.rs2, instr.imm
    s = instr.instr_str
    if s == "sw":
        if rs1 == 2 and (imm & 0x3) == 0 and _fits_unsigned(imm, 8):
            return c_swsp(rs2, imm)
        if _is_rvc_reg(rs1) and _is_rvc_reg(rs2) and (imm & 0x3) == 0 and _fits_unsigned(imm, 7):
            return c_sw(rs1 - 8, rs2 - 8, imm)
        return None
    if s == "sd":
        if rs1 == 2 and (imm & 0x7) == 0 and _fits_unsigned(imm, 9):
            return c_sdsp(rs2, imm)
        if _is_rvc_reg(rs1) and _is_rvc_reg(rs2) and (imm & 0x7) == 0 and _fits_unsigned(imm, 8):
            return c_sd(rs1 - 8, rs2 - 8, imm)
        return None
    return None


def _try_FloatLoad(instr) -> int:
    frd, rs1, imm = instr.frd, instr.rs1, instr.imm
    s = instr.instr_str
    if s == "fld":
        if rs1 == 2 and (imm & 0x7) == 0 and _fits_unsigned(imm, 9):
            return c_fldsp(frd, imm)
        if _is_rvc_reg(frd) and _is_rvc_reg(rs1) and (imm & 0x7) == 0 and _fits_unsigned(imm, 8):
            return c_fld(frd - 8, rs1 - 8, imm)
        return None
    if s == "flw" and not instr.is_design_64bit:
        if rs1 == 2 and (imm & 0x3) == 0 and _fits_unsigned(imm, 8):
            return c_flwsp(frd, imm)
        if _is_rvc_reg(frd) and _is_rvc_reg(rs1) and (imm & 0x3) == 0 and _fits_unsigned(imm, 7):
            return c_flw(frd - 8, rs1 - 8, imm)
        return None
    return None


def _try_FloatStore(instr) -> int:
    rs1, frs2, imm = instr.rs1, instr.frs2, instr.imm
    s = instr.instr_str
    if s == "fsd":
        if rs1 == 2 and (imm & 0x7) == 0 and _fits_unsigned(imm, 9):
            return c_fsdsp(frs2, imm)
        if _is_rvc_reg(rs1) and _is_rvc_reg(frs2) and (imm & 0x7) == 0 and _fits_unsigned(imm, 8):
            return c_fsd(rs1 - 8, frs2 - 8, imm)
        return None
    if s == "fsw" and not instr.is_design_64bit:
        if rs1 == 2 and (imm & 0x3) == 0 and _fits_unsigned(imm, 8):
            return c_fswsp(frs2, imm)
        if _is_rvc_reg(rs1) and _is_rvc_reg(frs2) and (imm & 0x3) == 0 and _fits_unsigned(imm, 7):
            return c_fsw(rs1 - 8, frs2 - 8, imm)
        return None
    return None


# ---------------------------------------------------------------------------
# Top-level dispatcher used by genelf.py
# ---------------------------------------------------------------------------

def try_pack_compressed_with_nop(instr) -> int:
    """Return a 32-bit slot value packing the compressed encoding + c.nop, or
    ``None`` if the instruction cannot be compressed under RVC constraints.
    """
    # Local imports to avoid circular dependency at module load time.
    from cascade.cfinstructionclasses import (
        R12DInstruction, ImmRdInstruction, RegImmInstruction, BranchInstruction,
        JALInstruction, JALRInstruction, IntLoadInstruction, IntStoreInstruction,
        FloatLoadInstruction, FloatStoreInstruction,
    )

    try:
        if isinstance(instr, R12DInstruction):
            c16 = _try_R12D(instr)
        elif isinstance(instr, ImmRdInstruction):
            c16 = _try_ImmRd(instr)
        elif isinstance(instr, RegImmInstruction):
            c16 = _try_RegImm(instr)
        elif isinstance(instr, BranchInstruction):
            c16 = _try_Branch(instr)
        elif isinstance(instr, JALInstruction):
            c16 = _try_JAL(instr)
        elif isinstance(instr, JALRInstruction):
            c16 = _try_JALR(instr)
        elif isinstance(instr, IntLoadInstruction):
            c16 = _try_IntLoad(instr)
        elif isinstance(instr, IntStoreInstruction):
            c16 = _try_IntStore(instr)
        elif isinstance(instr, FloatLoadInstruction):
            c16 = _try_FloatLoad(instr)
        elif isinstance(instr, FloatStoreInstruction):
            c16 = _try_FloatStore(instr)
        else:
            return None
    except AssertionError:
        return None

    if c16 is None:
        return None
    return pack_with_cnop(c16)


def is_compressible_class(instr) -> bool:
    """Return True iff ``instr``'s class is a candidate for compression."""
    from cascade.cfinstructionclasses import (
        R12DInstruction, ImmRdInstruction, RegImmInstruction, BranchInstruction,
        JALInstruction, JALRInstruction, IntLoadInstruction, IntStoreInstruction,
        FloatLoadInstruction, FloatStoreInstruction,
    )
    return isinstance(instr, (
        R12DInstruction, ImmRdInstruction, RegImmInstruction, BranchInstruction,
        JALInstruction, JALRInstruction, IntLoadInstruction, IntStoreInstruction,
        FloatLoadInstruction, FloatStoreInstruction,
    ))
