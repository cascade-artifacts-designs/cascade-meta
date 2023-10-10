# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import rv.rvprotoinstrs as rvprotoinstrs

ZIFENCEI_OPCODE_FENCEI = 0b0001111

# @return uint32_t
def zifencei_fencei(rd: int = 0, rs1: int = 0):
    return rvprotoinstrs.instruc_itype(ZIFENCEI_OPCODE_FENCEI, rd, 0b001, rs1, 0)
