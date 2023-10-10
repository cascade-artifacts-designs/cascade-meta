# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import enum

# ISAInstrClass differs from CFInstrClass, because:
# ISAInstrClass is sorted by ISA extension (for picking instruction)
# CFInstrClass  is sorted by information flow (e.g., how many registers are taken as an input)

class ISAInstrClass(enum.IntEnum):
    REGFSM      = enum.auto() # Instructions from the other groups that produce offset registers
    FPUFSM      = enum.auto() # enable or disable the FPU, or change rounding modes
    ALU         = enum.auto()
    ALU64       = enum.auto() # ALU instructions only for RISCV-64
    MULDIV      = enum.auto()
    MULDIV64    = enum.auto()
    AMO         = enum.auto()
    AMO64       = enum.auto()
    JAL         = enum.auto() # Separated because have different reg fsm requirements
    JALR        = enum.auto() # Separated because have different reg fsm requirements
    BRANCH      = enum.auto()
    MEM         = enum.auto()
    MEM64       = enum.auto()
    MEMFPU      = enum.auto()
    FPU         = enum.auto()
    FPU64       = enum.auto()
    MEMFPUD     = enum.auto()
    FPUD        = enum.auto()
    FPUD64      = enum.auto()
    TVECFSM     = enum.auto() # We treat it separately for now, but could include it in the CSR class
    PPFSM       = enum.auto() # Writes the xPP fields of mstatus
    EPCFSM      = enum.auto()
    MEDELEG     = enum.auto() # Writing a new value to medeleg
    EXCEPTION   = enum.auto() # Any instruction that generates an exception
    RANDOM_CSR  = enum.auto() # Any CSR instruction that does not require a consumed register
    DESCEND_PRV = enum.auto() # mret and sret
    SPECIAL     = enum.auto() # fence, ecall, ebreak

# Also used by the medeleg CSR
class ExceptionCauseVal(enum.IntEnum):
    # Important: the values must match the ones in the RISC-V specification, so do not use enum.auto and make sure to skip the reserved values
    ID_INSTR_ADDR_MISALIGNED        = 0
    ID_INSTR_ACCESS_FAULT           = 1
    ID_ILLEGAL_INSTRUCTION          = 2
    ID_BREAKPOINT                   = 3
    ID_LOAD_ADDR_MISALIGNED         = 4
    ID_LOAD_ACCESS_FAULT            = 5
    ID_STORE_AMO_ADDR_MISALIGNED    = 6
    ID_STORE_AMO_ACCESS_FAULT       = 7
    ID_ENVIRONMENT_CALL_FROM_U_MODE = 8
    ID_ENVIRONMENT_CALL_FROM_S_MODE = 9
    ID_ENVIRONMENT_CALL_FROM_M_MODE = 11
    ID_INSTRUCTION_PAGE_FAULT       = 12
    ID_LOAD_PAGE_FAULT              = 13
    ID_STORE_AMO_PAGE_FAULT         = 15

INSTRUCTIONS_BY_ISA_CLASS = {
    ISAInstrClass.ALU: [
        "lui",
        "auipc",
        "addi",
        "slti",
        "sltiu",
        "xori",
        "ori",
        "andi",
        "slli",
        "srli",
        "srai",
        "add",
        "sub",
        "sll",
        "slt",
        "sltu",
        "xor",
        "srl",
        "sra",
        "or",
        "and"
    ],
    ISAInstrClass.ALU64: [
        "addiw",
        "slliw",
        "srliw",
        "sraiw",
        "addw",
        "subw",
        "sllw",
        "srlw",
        "sraw"
    ],
    ISAInstrClass.MULDIV: [
        "mul",
        "mulh",
        "mulhsu",
        "mulhu",
        "div",
        "divu",
        "rem",
        "remu"
    ],
    ISAInstrClass.MULDIV64: [
        "mulw",
        "divw",
        "divuw",
        "remw",
        "remuw"
    ],
    ISAInstrClass.AMO: [
        "lr.w",
        "sc.w",
        "amoswap.w",
        "amoadd.w",
        "amoxor.w",
        "amoand.w",
        "amoor.w",
        "amomin.w",
        "amomax.w",
        "amominu.w",
        "amomaxu.w"
    ],
    ISAInstrClass.AMO64: [
        "lr.d",
        "sc.d",
        "amoswap.d",
        "amoadd.d",
        "amoxor.d",
        "amoand.d",
        "amoor.d",
        "amomin.d",
        "amomax.d",
        "amominu.d",
        "amomaxu.d"
    ],
    ISAInstrClass.JAL: [
        "jal",
    ],
    ISAInstrClass.JALR: [
        "jalr"
    ],
    ISAInstrClass.BRANCH: [
        "beq",
        "bne",
        "blt",
        "bge",
        "bltu",
        "bgeu"
    ],
    ISAInstrClass.MEM: [
        "lb",
        "lh",
        "lw",
        "lbu",
        "lhu",
        "sb",
        "sh",
        "sw"
    ],
    ISAInstrClass.MEM64: [
        "lwu",
        "ld",
        "sd"
    ],
    ISAInstrClass.MEMFPU: [
        "flw",
        "fsw"
    ],
    ISAInstrClass.FPU: [
        "fmadd.s",
        "fmsub.s",
        "fnmsub.s",
        "fnmadd.s",
        "fadd.s",
        "fsub.s",
        "fmul.s",
        "fdiv.s",
        "fsqrt.s",
        "fsgnj.s",
        "fsgnjn.s",
        "fsgnjx.s",
        "fmin.s",
        "fmax.s",
        "fcvt.w.s",
        "fcvt.wu.s",
        "fmv.x.w",
        "feq.s",
        "flt.s",
        "fle.s",
        "fclass.s",
        "fcvt.s.w",
        "fcvt.s.wu",
        "fmv.w.x"
    ],
    ISAInstrClass.FPU64: [
        "fcvt.l.s",
        "fcvt.lu.s",
        "fcvt.s.l",
        "fcvt.s.lu"
    ],
    ISAInstrClass.MEMFPUD: [
        "fld",
        "fsd"
    ],
    ISAInstrClass.FPUD: [
        "fmadd.d",
        "fmsub.d",
        "fnmsub.d",
        "fnmadd.d",
        "fadd.d",
        "fsub.d",
        "fmul.d",
        "fdiv.d",
        "fsqrt.d",
        "fsgnj.d",
        "fsgnjn.d",
        "fsgnjx.d",
        "fmin.d",
        "fmax.d",
        "fcvt.s.d",
        "fcvt.d.s",
        "feq.d",
        "flt.d",
        "fle.d",
        "fclass.d",
        "fcvt.w.d",
        "fcvt.wu.d",
        "fcvt.d.w",
        "fcvt.d.wu"
    ],
    ISAInstrClass.FPUD64: [
        "fcvt.l.d",
        "fcvt.lu.d",
        "fmv.x.d",
        "fcvt.d.l",
        "fcvt.d.lu",
        "fmv.d.x"
    ],
    ISAInstrClass.RANDOM_CSR: [
        "csrrw",
        "csrrs",
        "csrrc",
        "csrrwi",
        "csrrsi",
        "csrrci"
    ],
    ISAInstrClass.SPECIAL: [
        "fence",
        "fence.i"
    ],
}

def get_range_bits_per_instrclass(isaclass: ISAInstrClass):
    if isaclass == ISAInstrClass.BRANCH:
        return 12
    elif isaclass == ISAInstrClass.JAL:
        return 20
    elif isaclass == ISAInstrClass.JALR:
        return 31
    elif isaclass in (ISAInstrClass.EXCEPTION, ISAInstrClass.DESCEND_PRV):
        return 31 # xtvec and xepc can send to everywhere
    else:
        print('isaclass:', isaclass)
        raise ValueError(f"Unsupported control flow ISA class: {isaclass}")

###
# Some enums and constants
###

from enum import IntEnum, auto

# The state in which each register can be.
class IntRegIndivState(IntEnum):
    FREE               = auto() # FREE because either initial state, or PRODUCED1 and was used by a consumer but is not its output, or FRESH
    PRODUCED0          = auto() # aka "gen"
    PRODUCED1          = auto() # aka "ready"
    CONSUMED           = auto() # aka "applied". Was either PRODUCED1 and directly consumed as input and output of the consumer, or FREE and just output of the consumer.
    UNRELIABLE         = auto() # If offset but not chosen as applied

BASIC_BLOCK_MIN_SPACE = 24 # bytes.
