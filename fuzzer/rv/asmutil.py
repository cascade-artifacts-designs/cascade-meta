# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import DO_ASSERT
import random

def get_another_random_reg_id(forbidden_reg: int, x0_allowed: bool):
    if DO_ASSERT:
        assert 0 <= forbidden_reg
        assert forbidden_reg < 32
    if x0_allowed:
        ret = (forbidden_reg + random.randrange(1, 32)) & 0x1F
        if DO_ASSERT:
            assert 0 <= ret
    else:
        if DO_ASSERT:
            assert 0 < forbidden_reg
        ret = ((forbidden_reg - 1 + random.randrange(1, 31)) % 31) + 1
        if DO_ASSERT:
            assert 0 < ret
    if DO_ASSERT:
        assert ret < 32
        assert ret != forbidden_reg
    return ret

# Generates a section that will contain a typically pseudo-random 8-byte data.
# @param sectionname. It should not have duplicates. Typically 'randdata0' or 'randdata1' or 'randdata2'.
# @param contentval must be nonnegative and fit on 8 bytes.
# @return a list of gnuasm lines that create the section and feed it with the provided data.
def gen_val_section(sectionname: str, contentval: int):
    if DO_ASSERT:
        assert contentval >= 0 and contentval < 0x10000000000000000
    return [
        f'.section ".{sectionname}","ax",@progbits',
        # .align 2  <-- alignment is already enforced by the linker script.
        f'  .8byte {hex(contentval)}'
    ]

# @param val_section_id the section id so that different registers get potentially different values (and do not point to the same)
# @return a list of asm lines that put the random val into the designated register.
def put_random_value_into_reg_if_not_x0(val_section_id: int, tgt_reg_id: int, is_design_32bit: bool, interm_reg: int = None, forbidden_interms = set()):
    if tgt_reg_id == 0:
        return []

    if DO_ASSERT:
        assert 0 <= tgt_reg_id
        assert tgt_reg_id < 32

    # Generate and check the intermediate register.
    while interm_reg is None or interm_reg in forbidden_interms:
        interm_reg = get_another_random_reg_id(tgt_reg_id, False) # Load the symbol using any other symbol
    if DO_ASSERT:
        assert 0 < interm_reg
        assert interm_reg < 32
        assert interm_reg not in forbidden_interms
        assert tgt_reg_id != interm_reg

    # Load a word or a double, depending on bit width of the CPU ISA.
    if is_design_32bit:
        load_opcode = 'lw'
    else:
        load_opcode = 'ld'

    return [
        f"la x{interm_reg}, randdata{val_section_id}",
        f"{load_opcode} x{tgt_reg_id}, (x{interm_reg})"
    ]

# Helper function that generates assembly lines to load random data into a floating point register
# @param val_section_id the section id so that different registers get potentially different values (and do not point to the same)
# @param tgt_reg_id the id of the register to be assigned, must be included between 0 and 31.
# @param interm_reg the intermediate register id. Leave None for a constrained random choice.
# @return a list of assembly lines.
def put_random_value_into_floating_double_reg(val_section_id: int, tgt_reg_id: int, interm_reg: int = None, forbidden_interms = set()):
    if DO_ASSERT:
        assert 0 <= tgt_reg_id
        assert tgt_reg_id < 32

    # Generate and check the intermediate register.
    while interm_reg is None or interm_reg in forbidden_interms:
        interm_reg = random.randrange(1, 32) # Load the symbol using any other symbol
    if DO_ASSERT:
        assert 0 < interm_reg
        assert interm_reg < 32
        assert interm_reg not in forbidden_interms
    # For a target floating register, the reg id can be the same as the interm (because one is floating is one is integer)
    # assert tgt_reg_id != interm_reg

    # Load a word or a double, depending on bit width of the CPU ISA.
    load_opcode = 'fld'

    return [
        f"la x{interm_reg}, randdata{val_section_id}",
        f"{load_opcode} f{tgt_reg_id}, (x{interm_reg})"
    ]

# This function sets the value of the given register using an lui+addi sequence.
# @param do_check_bounds if True, will check that the value is not too big to fit in 31 bits (i.e., in 32 bits but without being sign-extended to 64 bits). DO_ASSERT must be True for it to be effective.
# @return pair (lui_imm: int, addi_imm: int)
def li_into_reg(val_unsigned: int, do_check_bounds: bool = True):
    if DO_ASSERT:
        assert val_unsigned >= 0
        if do_check_bounds:
            assert val_unsigned < 0x80000000, f"For the destination address `{hex(val_unsigned)}`, we will need to manage sign extension, which is not yet implemented here."

    # Check whether the MSB of the addi would be 1. In this case, we will add 1 to the lui
    is_sign_extend_ones = (val_unsigned >> 11) & 1

    addi_imm = val_unsigned & 0xFFF
    # Make it negative properly
    if is_sign_extend_ones:
        addi_imm = -((~addi_imm) & 0xFFF) - 1
    lui_imm  = (int(is_sign_extend_ones) + (val_unsigned >> 12)) & 0xFFFFF
    return lui_imm, addi_imm

# From an unsigned int coded on 32 or 64 bits, returns the signed value when interpreting the value as signed
def twos_complement(val_unsigned: int, is_design_64bit: bool):
    if is_design_64bit:
        if DO_ASSERT:
            assert val_unsigned >= 0
            assert val_unsigned < 1 << 64
        return val_unsigned - (((val_unsigned >> 63) & 1) << 64)
    else:
        if DO_ASSERT:
            assert val_unsigned >= 0
            assert val_unsigned < 1 << 32
        return val_unsigned - (((val_unsigned >> 31) & 1) << 32)

# From a signed int, returns an unsigned version.
# This should be a reciprocal function of twos_complement.
def to_unsigned(val_signed: int, is_design_64bit: bool):
    if is_design_64bit:
        if DO_ASSERT:
            assert val_signed < 1 << 63
        return (((val_signed >> 63) & 1) << 64) + val_signed
    else:
        if DO_ASSERT:
            assert val_signed < 1 << 32
        return (((val_signed >> 31) & 1) << 32) + val_signed
