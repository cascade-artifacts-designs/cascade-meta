# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

ZICSR_OPCODE_CSR = 0b1110011

# All functions return uint32_t

def zicsr_csrrw(rd: int, rs1: int, csr: int):
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b001, rs1, csr)
def zicsr_csrrs(rd: int, rs1: int, csr: int):
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b010, rs1, csr)
def zicsr_csrrc(rd: int, rs1: int, csr: int):
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b011, rs1, csr)
def zicsr_csrrwi(rd: int, uimm: int, csr: int):
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b101, uimm, csr)
def zicsr_csrrsi(rd: int, uimm: int, csr: int):
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b110, uimm, csr)
def zicsr_csrrci(rd: int, uimm: int, csr: int):
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b111, uimm, csr)
