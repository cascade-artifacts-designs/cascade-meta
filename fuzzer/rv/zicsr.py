# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import logging
import traceback
import rv.rvprotoinstrs as rvprotoinstrs

logger = logging.getLogger(__name__)

ZICSR_OPCODE_CSR = 0b1110011

# All functions return uint32_t

def zicsr_csrrw(rd: int, rs1: int, csr: int):
    logger.warning(f"zicsr.py:zicsr_csrrw: Creating CSRRW with CSR=0x{csr:x} ({csr}), rd={rd}, rs1={rs1}")
    logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b001, rs1, csr)
def zicsr_csrrs(rd: int, rs1: int, csr: int):
    logger.warning(f"zicsr.py:zicsr_csrrs: Creating CSRRS with CSR=0x{csr:x} ({csr}), rd={rd}, rs1={rs1}")
    logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b010, rs1, csr)
def zicsr_csrrc(rd: int, rs1: int, csr: int):
    logger.warning(f"zicsr.py:zicsr_csrrc: Creating CSRRC with CSR=0x{csr:x} ({csr}), rd={rd}, rs1={rs1}")
    logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b011, rs1, csr)
def zicsr_csrrwi(rd: int, uimm: int, csr: int):
    logger.warning(f"zicsr.py:zicsr_csrrwi: Creating CSRRWI with CSR=0x{csr:x} ({csr}), rd={rd}, uimm={uimm}")
    logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b101, uimm, csr)
def zicsr_csrrsi(rd: int, uimm: int, csr: int):
    logger.warning(f"zicsr.py:zicsr_csrrsi: Creating CSRRSI with CSR=0x{csr:x} ({csr}), rd={rd}, uimm={uimm}")
    logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b110, uimm, csr)
def zicsr_csrrci(rd: int, uimm: int, csr: int):
    logger.warning(f"zicsr.py:zicsr_csrrci: Creating CSRRCI with CSR=0x{csr:x} ({csr}), rd={rd}, uimm={uimm}")
    logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
    return rvprotoinstrs.instruc_itype(ZICSR_OPCODE_CSR, rd, 0b111, uimm, csr)
