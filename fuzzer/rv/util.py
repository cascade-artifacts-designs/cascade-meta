NUM_MAX_OFFSET_NOPS = 100

RV32I_BRANCHES = [
    "beq",
    "bne",
    "blt",
    "bge",
    "bltu",
    "bgeu"
]

CSR_INSTRS = [
    "csrrw",
    "csrrs",
    "csrrc",
    "csrrwi",
    "csrrsi",
    "csrrci"
]

INSTRUCTION_IDS = {
    "lui":     0,
    "auipc":   1,
    "jal":     2,
    "jalr":    3,
    "beq":     4,
    "bne":     5,
    "blt":     6,
    "bge":     7,
    "bltu":    8,
    "bgeu":    9,
    "lb":     10,
    "lh":     11,
    "lw":     12,
    "lbu":    13,
    "lhu":    14,
    "sb":     15,
    "sh":     16,
    "sw":     17,
    "addi":   18,
    "slti":   19,
    "sltiu":  20,
    "xori":   21,
    "ori":    22,
    "andi":   23,
    "slli":   24,
    "srli":   25,
    "srai":   26,
    "add":    27,
    "sub":    28,
    "sll":    29,
    "slt":    30,
    "sltu":   31,
    "xor":    32,
    "srl":    33,
    "sra":    34,
    "or":     35,
    "and":    36,
    "fence":  37,
    "ecall":  38,
    "ebreak": 39,

    "lwu":    40,
    "ld":     41,
    "sd":     42,
    "addiw":  43,
    "slliw":  44,
    "srliw":  45,
    "sraiw":  46,
    "addw":   47,
    "subw":   48,
    "sllw":   49,
    "srlw":   50,
    "sraw":   51,

    "fence.i":   52,

    "csrrw":  53,
    "csrrs":  54,
    "csrrc":  55,
    "csrrwi": 56,
    "csrrsi": 57,
    "csrrci": 58,

    "mul":        59,
    "mulh":       60,
    "mulhsu":     61,
    "mulhu":      62,
    "div":        63,
    "divu":       64,
    "rem":        65,
    "remu":       66,

    "mulw":       67,
    "divw":       68,
    "divuw":      69,
    "remw":       70,
    "remuw":      71,

    "lr.w":       72,
    "sc.w":       73,
    "amoswap.w":  74,
    "amoadd.w":   75,
    "amoxor.w":   76,
    "amoand.w":   77,
    "amoor.w":    78,
    "amomin.w":   79,
    "amomax.w":   80,
    "amominu.w":  81,
    "amomaxu.w":  82,

    "lr.d":       83,
    "sc.d":       84,
    "amoswap.d":  85,
    "amoadd.d":   86,
    "amoxor.d":   87,
    "amoand.d":   88,
    "amoor.d":    89,
    "amomin.d":   90,
    "amomax.d":   91,
    "amominu.d":  92,
    "amomaxu.d":  93,

    "flw":        94,
    "fsw":        95,
    "fmadd.s":    96,
    "fmsub.s":    97,
    "fnmsub.s":   98,
    "fnmadd.s":   99,
    "fadd.s":     100,
    "fsub.s":     101,
    "fmul.s":     102,
    "fdiv.s":     103,
    "fsqrt.s":    104,
    "fsgnj.s":    105,
    "fsgnjn.s":   106,
    "fsgnjx.s":   107,
    "fmin.s":     108,
    "fmax.s":     109,
    "fcvt.w.s":   110,
    "fcvt.wu.s":  111,
    "fmv.x.w":    112,
    "feq.s":      113,
    "flt.s":      114,
    "fle.s":      115,
    "fclass.s":   116,
    "fcvt.s.w":   117,
    "fcvt.s.wu":  118,
    "fmv.w.x":    119,

    "fcvt.l.s":   120,
    "fcvt.lu.s":  121,
    "fcvt.s.l":   122,
    "fcvt.s.lu":  123,

    "fld":        124,
    "fsd":        125,
    "fmadd.d":    126,
    "fmsub.d":    127,
    "fnmsub.d":   128,
    "fnmadd.d":   129,
    "fadd.d":     130,
    "fsub.d":     131,
    "fmul.d":     132,
    "fdiv.d":     133,
    "fsqrt.d":    134,
    "fsgnj.d":    135,
    "fsgnjn.d":   136,
    "fsgnjx.d":   137,
    "fmin.d":     138,
    "fmax.d":     139,
    "fcvt.s.d":   140,
    "fcvt.d.s":   141,
    "feq.d":      142,
    "flt.d":      143,
    "fle.d":      144,
    "fclass.d":   145,
    "fcvt.w.d":   146,
    "fcvt.wu.d":  147,
    "fcvt.d.w":   148,
    "fcvt.d.wu":  149,

    "fcvt.l.d":   150,
    "fcvt.lu.d":  151,
    "fmv.x.d":    152,
    "fcvt.d.l":   153,
    "fcvt.d.lu":  154,
    "fmv.d.x":    155,

    "c.addi4spn": 156,
    "c.fld":      157,
    # "c.lq":       158,
    "c.lw":       158,
    "c.flw":      159,
    "c.ld":       160,
    "c.fsd":      161,
    # "c.sq":       163,
    "c.sw":       162,
    "c.fsw":      163,
    "c.sd":       164,
    "c.nop":      165,
    "c.addi":     166,
    "c.jal":      167,
    "c.addiw":    168,
    "c.li":       169,
    "c.addi16sp": 170,
    "c.lui":      171,
    "c.srli":     172,
    "c.srli64":   173,
    "c.srai":     174,
    "c.srai64":   175,
    "c.andi":     176,
    "c.sub":      177,
    "c.xor":      178,
    "c.or":       179,
    "c.and":      180,
    "c.subw":     181,
    "c.addw":     182,
    "c.j":        183,
    "c.beqz":     184,
    "c.bnez":     185,
    "c.slli":     186,
    "c.slli64":   187,
    "c.fldsp":    188,
    # "c.lqsp":     191,
    "c.lwsp":     189,
    "c.flwsp":    190,
    "c.ldsp":     191,
    "c.jr":       192,
    "c.mv":       193,
    "c.ebreak":   194,
    "c.jalr":     195,
    "c.add":      196,
    "c.fsdsp":    197,
    # "c.sqsp":     201,
    "c.swsp":     198,
    "c.fswsp":    199,
    "c.sdsp":     200,
}
INSTRUCTION_IDS_INV = {v: k for k, v in INSTRUCTION_IDS.items()}

INSTRUCTION_IDS_NORV32 = {
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    48,
    49,
    50,
    51,
    67,
    68,
    69,
    70,
    71,
    72,
    73,
    74,
    75,
    76,
    77,
    78,
    79,
    80,
    81,
    82,
    83,
    84,
    85,
    86,
    87,
    88,
    89,
    90,
    91,
    92,
    93,
    120,
    121,
    122,
    123,
    124,
    125,
    126,
    127,
    128,
    129,
    130,
    131,
    132,
    133,
    134,
    135,
    136,
    137,
    138,
    139,
    140,
    141,
    142,
    143,
    144,
    145,
    146,
    147,
    148,
    149,
    150,
    151,
    152,
    153,
    154,
    155,
    INSTRUCTION_IDS['c.ld'],
    INSTRUCTION_IDS['c.sd'],
    INSTRUCTION_IDS['c.addiw'],
    INSTRUCTION_IDS['c.srli'],
    INSTRUCTION_IDS['c.srai'],
    INSTRUCTION_IDS['c.ldsp'],
    INSTRUCTION_IDS['c.sdsp'],
    INSTRUCTION_IDS['c.fldsp'],
    INSTRUCTION_IDS['c.fsdsp'],
    INSTRUCTION_IDS['c.addw'],
    INSTRUCTION_IDS['c.subw'],
}

INSTRUCTION_IDS_NORV64 = {
    INSTRUCTION_IDS['c.flw'],
    INSTRUCTION_IDS['c.fsw'],
    INSTRUCTION_IDS['c.flwsp'],
    INSTRUCTION_IDS['c.fswsp'],
    INSTRUCTION_IDS['c.jal'],
}

PARAM_SIZES_BITS_32 = [
    [5, 20],    # lui
    [5, 20],    # auipc
    [5, 21],    # jal
    [5, 5, 12], # jalr
    [5, 5, 13], # beq
    [5, 5, 13], # bne
    [5, 5, 13], # blt
    [5, 5, 13], # bge
    [5, 5, 13], # bltu
    [5, 5, 13], # bgeu
    [5, 5, 12], # lb
    [5, 5, 12], # lh
    [5, 5, 12], # lw
    [5, 5, 12], # lbu
    [5, 5, 12], # lhu
    [5, 5, 12], # sb
    [5, 5, 12], # sh
    [5, 5, 12], # sw
    [5, 5, 12], # addi
    [5, 5, 12], # slti
    [5, 5, 12], # sltiu
    [5, 5, 12], # xori
    [5, 5, 12], # ori
    [5, 5, 12], # andi
    [5, 5, 5],  # slli
    [5, 5, 5],  # srli
    [5, 5, 5],  # srai
    [5, 5, 5],  # add
    [5, 5, 5],  # sub
    [5, 5, 5],  # sll
    [5, 5, 5],  # slt
    [5, 5, 5],  # sltu
    [5, 5, 5],  # xor
    [5, 5, 5],  # srl
    [5, 5, 5],  # sra
    [5, 5, 5],  # or
    [5, 5, 5],  # and
    [],         # fence
    [],         # ecall
    [],         # ebreak

    [5, 5, 12], # lwu
    [5, 5, 12], # ld
    [5, 5, 12], # sd
    [5, 5, 12], # addiw
    [5, 5, 5],  # slliw
    [5, 5, 5],  # srliw
    [5, 5, 5],  # sraiw
    [5, 5, 5],  # addw
    [5, 5, 5],  # subw
    [5, 5, 5],  # sllw
    [5, 5, 5],  # srlw
    [5, 5, 5],  # sraw

    [],  # fencei

    [5, 5, 12], # csrrw
    [5, 5, 12], # csrrs
    [5, 5, 12], # csrrc
    [5, 5, 12], # csrrwi
    [5, 5, 12], # csrrsi
    [5, 5, 12], # csrrci

    [5, 5, 5], # mul
    [5, 5, 5], # mulh
    [5, 5, 5], # mulhsu
    [5, 5, 5], # mulhu
    [5, 5, 5], # div
    [5, 5, 5], # divu
    [5, 5, 5], # rem
    [5, 5, 5], # remu

    [5, 5, 5], # mulw
    [5, 5, 5], # divw
    [5, 5, 5], # divuw
    [5, 5, 5], # remw
    [5, 5, 5], # remuw

    [5, 5, 1, 1], # lr.w
    [5, 5, 5, 1, 1], # sc.w
    [5, 5, 5, 1, 1], # amoswap.w
    [5, 5, 5, 1, 1], # amoadd.w
    [5, 5, 5, 1, 1], # amoxor.w
    [5, 5, 5, 1, 1], # amoand.w
    [5, 5, 5, 1, 1], # amoor.w
    [5, 5, 5, 1, 1], # amomin.w
    [5, 5, 5, 1, 1], # amomax.w
    [5, 5, 5, 1, 1], # amominu.w
    [5, 5, 5, 1, 1], # amomaxu.w

    [5, 5, 1, 1], # lr.d
    [5, 5, 5, 1, 1], # sc.d
    [5, 5, 5, 1, 1], # amoswap.d
    [5, 5, 5, 1, 1], # amoadd.d
    [5, 5, 5, 1, 1], # amoxor.d
    [5, 5, 5, 1, 1], # amoand.d
    [5, 5, 5, 1, 1], # amoor.d
    [5, 5, 5, 1, 1], # amomin.d
    [5, 5, 5, 1, 1], # amomax.d
    [5, 5, 5, 1, 1], # amominu.d
    [5, 5, 5, 1, 1], # amomaxu.d

    [5, 5, 12], # flw
    [5, 5, 12], # fsw
    [5, 5, 5, 5, 3], # fmadd.s
    [5, 5, 5, 5, 3], # fmsub.s
    [5, 5, 5, 5, 3], # fnmsub.s
    [5, 5, 5, 5, 3], # fnmadd.s
    [5, 5, 5, 3], # fadd.s
    [5, 5, 5, 3], # fsub.s
    [5, 5, 5, 3], # fmul.s
    [5, 5, 5, 3], # fdiv.s
    [5, 5, 3], # fsqrt.s
    [5, 5, 5], # fsgnj.s
    [5, 5, 5], # fsgnjn.s
    [5, 5, 5], # fsgnjx.s
    [5, 5, 5], # fmin.s
    [5, 5, 5], # fmax.s
    [5, 5, 3], # fcvt.w.s
    [5, 5, 3], # fcvt.wu.s
    [5, 5], # fmv.x.w
    [5, 5, 5], # feq.s
    [5, 5, 5], # flt.s
    [5, 5, 5], # fle.s
    [5, 5], # fclass.s
    [5, 5, 3], # fcvt.s.w
    [5, 5, 3], # fcvt.s.wu
    [5, 5], # fmv.w.x

    [5, 5, 3], # fcvt.l.s
    [5, 5, 3], # fcvt.lu.s
    [5, 5, 3], # fcvt.s.l
    [5, 5, 3], # fcvt.s.lu

    [5, 5, 12], # fld
    [5, 5, 12], # fsd
    [5, 5, 5, 5, 3], # fmadd.d
    [5, 5, 5, 5, 3], # fmsub.d
    [5, 5, 5, 5, 3], # fnmsub.d
    [5, 5, 5, 5, 3], # fnmadd.d
    [5, 5, 5, 3], # fadd.d
    [5, 5, 5, 3], # fsub.d
    [5, 5, 5, 3], # fmul.d
    [5, 5, 5, 3], # fdiv.d
    [5, 5, 3], # fsqrt.d
    [5, 5, 5], # fsgnj.d
    [5, 5, 5], # fsgnjn.d
    [5, 5, 5], # fsgnjx.d
    [5, 5, 5], # fmin.d
    [5, 5, 5], # fmax.d
    [5, 5, 3], # fcvt.s.d
    [5, 5, 3], # fcvt.d.s
    [5, 5, 5], # feq.d
    [5, 5, 5], # flt.d
    [5, 5, 5], # fle.d
    [5, 5], # fclass.d
    [5, 5, 3], # fcvt.w.d
    [5, 5, 3], # fcvt.wu.d
    [5, 5, 3], # fcvt.d.w
    [5, 5, 3], # fcvt.d.wu

    [5, 5, 3], # fcvt.l.d
    [5, 5, 3], # fcvt.lu.d
    [5, 5], # fmv.x.d
    [5, 5, 3], # fcvt.d.l
    [5, 5, 3], # fcvt.d.lu
    [5, 5], # fmv.d.x

    [3, 10], # c.addi4spn
    [3, 3, 8], # c.fld
    # [3, 3, 5], # c.lq
    [3, 3, 7], # c.lw
    [3, 3, 7], # c.flw
    [3, 3, 7], # c.ld
    [3, 3, 8], # c.fsd
    # [3, 3, 5], # c.sq
    [3, 3, 7], # c.sw
    [3, 3, 7], # c.fsw
    [3, 3, 8], # c.sd
    [5], # c.nop
    [5, 5], # c.addi
    [12], # c.jal
    [5, 6], # c.addiw
    [5, 5], # c.li
    [10], # c.addi16sp
    [5, 18], # c.lui
    [3, 5], # c.srli
    [3], # c.srli64
    [3, 5], # c.srai
    [3], # c.srai64
    [3, 5], # c.andi
    [3, 3], # c.sub
    [3, 3], # c.xor
    [3, 3], # c.or
    [3, 3], # c.and
    [3, 3], # c.subw
    [3, 3], # c.addw
    [11], # c.j
    [3, 9], # c.beqz
    [3, 9], # c.bnez
    [5, 5], # c.slli
    [5], # c.slli64
    [5, 9], # c.fldsp
    # [5, 5], # c.lqsp
    [5, 8], # c.lwsp
    [5, 8], # c.flwsp
    [5, 9], # c.ldsp
    [5], # c.jr
    [5, 5], # c.mv
    [], # c.ebreak
    [5], # c.jalr
    [5, 5], # c.add
    [5, 9], # c.fsdsp
    # [5, 6], # c.sqsp
    [5, 8], # c.swsp
    [5, 8], # c.fswsp
    [5, 9], # c.sdsp
]

PARAM_SIZES_BITS_64 = [
    [5, 20],    # lui
    [5, 20],    # auipc
    [5, 21],    # jal
    [5, 5, 12], # jalr
    [5, 5, 13], # beq
    [5, 5, 13], # bne
    [5, 5, 13], # blt
    [5, 5, 13], # bge
    [5, 5, 13], # bltu
    [5, 5, 13], # bgeu
    [5, 5, 12], # lb
    [5, 5, 12], # lh
    [5, 5, 12], # lw
    [5, 5, 12], # lbu
    [5, 5, 12], # lhu
    [5, 5, 12], # sb
    [5, 5, 12], # sh
    [5, 5, 12], # sw
    [5, 5, 12], # addi
    [5, 5, 12], # slti
    [5, 5, 12], # sltiu
    [5, 5, 12], # xori
    [5, 5, 12], # ori
    [5, 5, 12], # andi
    [5, 5, 6],  # slli
    [5, 5, 6],  # srli
    [5, 5, 6],  # srai
    [5, 5, 5],  # add
    [5, 5, 5],  # sub
    [5, 5, 5],  # sll
    [5, 5, 5],  # slt
    [5, 5, 5],  # sltu
    [5, 5, 5],  # xor
    [5, 5, 5],  # srl
    [5, 5, 5],  # sra
    [5, 5, 5],  # or
    [5, 5, 5],  # and
    [],         # fence
    [],         # ecall
    [],         # ebreak

    [5, 5, 12], # lwu
    [5, 5, 12], # ld
    [5, 5, 12], # sd
    [5, 5, 12], # addiw
    [5, 5, 5],  # slliw
    [5, 5, 5],  # srliw
    [5, 5, 5],  # sraiw
    [5, 5, 5],  # addw
    [5, 5, 5],  # subw
    [5, 5, 5],  # sllw
    [5, 5, 5],  # srlw
    [5, 5, 5],  # sraw

    [],  # fencei

    [5, 5, 12], # csrrw
    [5, 5, 12], # csrrs
    [5, 5, 12], # csrrc
    [5, 5, 12], # csrrwi
    [5, 5, 12], # csrrsi
    [5, 5, 12], # csrrci

    [5, 5, 5], # mul
    [5, 5, 5], # mulh
    [5, 5, 5], # mulhsu
    [5, 5, 5], # mulhu
    [5, 5, 5], # div
    [5, 5, 5], # divu
    [5, 5, 5], # rem
    [5, 5, 5], # remu

    [5, 5, 5], # mulw
    [5, 5, 5], # divw
    [5, 5, 5], # divuw
    [5, 5, 5], # remw
    [5, 5, 5], # remuw

    [5, 5, 1, 1], # lr.w
    [5, 5, 5, 1, 1], # sc.w
    [5, 5, 5, 1, 1], # amoswap.w
    [5, 5, 5, 1, 1], # amoadd.w
    [5, 5, 5, 1, 1], # amoxor.w
    [5, 5, 5, 1, 1], # amoand.w
    [5, 5, 5, 1, 1], # amoor.w
    [5, 5, 5, 1, 1], # amomin.w
    [5, 5, 5, 1, 1], # amomax.w
    [5, 5, 5, 1, 1], # amominu.w
    [5, 5, 5, 1, 1], # amomaxu.w

    [5, 5, 1, 1], # lr.d
    [5, 5, 5, 1, 1], # sc.d
    [5, 5, 5, 1, 1], # amoswap.d
    [5, 5, 5, 1, 1], # amoadd.d
    [5, 5, 5, 1, 1], # amoxor.d
    [5, 5, 5, 1, 1], # amoand.d
    [5, 5, 5, 1, 1], # amoor.d
    [5, 5, 5, 1, 1], # amomin.d
    [5, 5, 5, 1, 1], # amomax.d
    [5, 5, 5, 1, 1], # amominu.d
    [5, 5, 5, 1, 1], # amomaxu.d

    [5, 5, 12], # flw
    [5, 5, 12], # fsw
    [5, 5, 5, 5, 3], # fmadd.s
    [5, 5, 5, 5, 3], # fmsub.s
    [5, 5, 5, 5, 3], # fnmsub.s
    [5, 5, 5, 5, 3], # fnmadd.s
    [5, 5, 5, 3], # fadd.s
    [5, 5, 5, 3], # fsub.s
    [5, 5, 5, 3], # fmul.s
    [5, 5, 5, 3], # fdiv.s
    [5, 5, 3], # fsqrt.s
    [5, 5, 5], # fsgnj.s
    [5, 5, 5], # fsgnjn.s
    [5, 5, 5], # fsgnjx.s
    [5, 5, 5], # fmin.s
    [5, 5, 5], # fmax.s
    [5, 5, 3], # fcvt.w.s
    [5, 5, 3], # fcvt.wu.s
    [5, 5], # fmv.x.w
    [5, 5, 5], # feq.s
    [5, 5, 5], # flt.s
    [5, 5, 5], # fle.s
    [5, 5], # fclass.s
    [5, 5, 3], # fcvt.s.w
    [5, 5, 3], # fcvt.s.wu
    [5, 5], # fmv.w.x

    [5, 5, 3], # fcvt.l.s
    [5, 5, 3], # fcvt.lu.s
    [5, 5, 3], # fcvt.s.l
    [5, 5, 3], # fcvt.s.lu

    [5, 5, 12], # fld
    [5, 5, 12], # fsd
    [5, 5, 5, 5, 3], # fmadd.d
    [5, 5, 5, 5, 3], # fmsub.d
    [5, 5, 5, 5, 3], # fnmsub.d
    [5, 5, 5, 5, 3], # fnmadd.d
    [5, 5, 5, 3], # fadd.d
    [5, 5, 5, 3], # fsub.d
    [5, 5, 5, 3], # fmul.d
    [5, 5, 5, 3], # fdiv.d
    [5, 5, 3], # fsqrt.d
    [5, 5, 5], # fsgnj.d
    [5, 5, 5], # fsgnjn.d
    [5, 5, 5], # fsgnjx.d
    [5, 5, 5], # fmin.d
    [5, 5, 5], # fmax.d
    [5, 5, 3], # fcvt.s.d
    [5, 5, 3], # fcvt.d.s
    [5, 5, 5], # feq.d
    [5, 5, 5], # flt.d
    [5, 5, 5], # fle.d
    [5, 5], # fclass.d
    [5, 5, 3], # fcvt.w.d
    [5, 5, 3], # fcvt.wu.d
    [5, 5, 3], # fcvt.d.w
    [5, 5, 3], # fcvt.d.wu

    [5, 5, 3], # fcvt.l.d
    [5, 5, 3], # fcvt.lu.d
    [5, 5], # fmv.x.d
    [5, 5, 3], # fcvt.d.l
    [5, 5, 3], # fcvt.d.lu
    [5, 5], # fmv.d.x

    [3, 10], # c.addi4spn
    [3, 3, 8], # c.fld
    # [3, 3, 5], # c.lq
    [3, 3, 7], # c.lw
    [3, 3, 7], # c.flw
    [3, 3, 7], # c.ld
    [3, 3, 8], # c.fsd
    # [3, 3, 5], # c.sq
    [3, 3, 7], # c.sw
    [3, 3, 7], # c.fsw
    [3, 3, 8], # c.sd
    [5], # c.nop
    [5, 5], # c.addi
    [12], # c.jal
    [5, 6], # c.addiw
    [5, 5], # c.li
    [10], # c.addi16sp
    [5, 18], # c.lui
    [3, 5], # c.srli
    [3], # c.srli64
    [3, 5], # c.srai
    [3], # c.srai64
    [3, 5], # c.andi
    [3, 3], # c.sub
    [3, 3], # c.xor
    [3, 3], # c.or
    [3, 3], # c.and
    [3, 3], # c.subw
    [3, 3], # c.addw
    [11], # c.j
    [3, 9], # c.beqz
    [3, 9], # c.bnez
    [5, 5], # c.slli
    [5], # c.slli64
    [5, 9], # c.fldsp
    # [5, 5], # c.lqsp
    [5, 8], # c.lwsp
    [5, 8], # c.flwsp
    [5, 9], # c.ldsp
    [5], # c.jr
    [5, 5], # c.mv
    [], # c.ebreak
    [5], # c.jalr
    [5, 5], # c.add
    [5, 9], # c.fsdsp
    # [5, 6], # c.sqsp
    [5, 8], # c.swsp
    [5, 8], # c.fswsp
    [5, 9], # c.sdsp
]


INTSTORE_INSTRUCTIONS = {
    'sb',
    'sh',
    'sw',
    'sd',
}
INTLOAD_INSTRUCTIONS = {
    'lb',
    'lh',
    'lw',
    'ld',
    'lbu',
    'lhu',
    'lwu',
    'ldu',
}

FLOATSTORE_INSTRUCTIONS = {
    'fsw',
    'fsd',
    # 'dsw',
    # 'dsd',
}
FLOATLOAD_INSTRUCTIONS = {
    'flw',
    'fld',
    # 'dlw',
    # 'dld',
}

PARAM_REGTYPE = [
# '': immediate
# x: integer reg
# f: floating point reg
# m: rounding mode
# c: compressed integer register
# cf: compressed floating-point register

    ['x', ''],       # lui
    ['x', ''],       # auipc
    ['x', ''],       # jal
    ['x', 'x', ''], # jalr
    ['x', 'x', ''], # beq
    ['x', 'x', ''], # bne
    ['x', 'x', ''], # blt
    ['x', 'x', ''], # bge
    ['x', 'x', ''], # bltu
    ['x', 'x', ''], # bgeu
    ['x', 'x', ''], # lb
    ['x', 'x', ''], # lh
    ['x', 'x', ''], # lw
    ['x', 'x', ''], # lbu
    ['x', 'x', ''], # lhu
    ['x', 'x', ''], # sb
    ['x', 'x', ''], # sh
    ['x', 'x', ''], # sw
    ['x', 'x', ''], # addi
    ['x', 'x', ''], # slti
    ['x', 'x', ''], # sltiu
    ['x', 'x', ''], # xori
    ['x', 'x', ''], # ori
    ['x', 'x', ''], # andi
    ['x', 'x', ''], # slli
    ['x', 'x', ''], # srli
    ['x', 'x', ''], # srai
    ['x', 'x', 'x'],  # add
    ['x', 'x', 'x'],  # sub
    ['x', 'x', 'x'],  # sll
    ['x', 'x', 'x'],  # slt
    ['x', 'x', 'x'],  # sltu
    ['x', 'x', 'x'],  # xor
    ['x', 'x', 'x'],  # srl
    ['x', 'x', 'x'],  # sra
    ['x', 'x', 'x'],  # or
    ['x', 'x', 'x'],  # and
    [],               # fence
    [],               # ecall
    [],               # ebreak

    ['x', 'x', ''], # lwu
    ['x', 'x', ''], # ld
    ['x', 'x', ''], # sd
    ['x', 'x', ''], # addiw
    ['x', 'x', ''], # slliw
    ['x', 'x', ''], # srliw
    ['x', 'x', ''], # sraiw
    ['x', 'x', 'x'], # addw
    ['x', 'x', 'x'], # subw
    ['x', 'x', 'x'], # sllw
    ['x', 'x', 'x'], # srlw
    ['x', 'x', 'x'], # sraw

    [], # fencei

    ['x', 'x', ''], # csrrw
    ['x', 'x', ''], # csrrs
    ['x', 'x', ''], # csrrc
    ['x', '', ''], # csrrwi
    ['x', '', ''], # csrrsi
    ['x', '', ''], # csrrci

    ['x', 'x', 'x'], # mul
    ['x', 'x', 'x'], # mulh
    ['x', 'x', 'x'], # mulhsu
    ['x', 'x', 'x'], # mulhu
    ['x', 'x', 'x'], # div
    ['x', 'x', 'x'], # divu
    ['x', 'x', 'x'], # rem
    ['x', 'x', 'x'], # remu

    ['x', 'x', 'x'], # mulw
    ['x', 'x', 'x'], # divw
    ['x', 'x', 'x'], # divuw
    ['x', 'x', 'x'], # remw
    ['x', 'x', 'x'], # remuw

    ['x', 'x', '', ''],      # lr.w
    ['x', 'x', 'x', '', ''], # sc.w
    ['x', 'x', 'x', '', ''], # amoswap.w
    ['x', 'x', 'x', '', ''], # amoadd.w
    ['x', 'x', 'x', '', ''], # amoxor.w
    ['x', 'x', 'x', '', ''], # amoand.w
    ['x', 'x', 'x', '', ''], # amoor.w
    ['x', 'x', 'x', '', ''], # amomin.w
    ['x', 'x', 'x', '', ''], # amomax.w
    ['x', 'x', 'x', '', ''], # amominu.w
    ['x', 'x', 'x', '', ''], # amomaxu.w

    ['x', 'x', '', ''],      # lr.d
    ['x', 'x', 'x', '', ''], # sc.d
    ['x', 'x', 'x', '', ''], # amoswap.d
    ['x', 'x', 'x', '', ''], # amoadd.d
    ['x', 'x', 'x', '', ''], # amoxor.d
    ['x', 'x', 'x', '', ''], # amoand.d
    ['x', 'x', 'x', '', ''], # amoor.d
    ['x', 'x', 'x', '', ''], # amomin.d
    ['x', 'x', 'x', '', ''], # amomax.d
    ['x', 'x', 'x', '', ''], # amominu.d
    ['x', 'x', 'x', '', ''], # amomaxu.d

    ['f', 'x', ''], # flw
    ['f', 'x', ''], # fsw
    ['f', 'f', 'f', 'f', 'm'], # fmadd.s
    ['f', 'f', 'f', 'f', 'm'], # fmsub.s
    ['f', 'f', 'f', 'f', 'm'], # fnmsub.s
    ['f', 'f', 'f', 'f', 'm'], # fnmadd.s
    ['f', 'f', 'f', 'm'], # fadd.s
    ['f', 'f', 'f', 'm'], # fsub.s
    ['f', 'f', 'f', 'm'], # fmul.s
    ['f', 'f', 'f', 'm'], # fdiv.s
    ['f', 'f', 'm'], # fsqrt.s
    ['f', 'f', 'f'], # fsgnj.s
    ['f', 'f', 'f'], # fsgnjn.s
    ['f', 'f', 'f'], # fsgnjx.s
    ['f', 'f', 'f'], # fmin.s
    ['f', 'f', 'f'], # fmax.s
    ['x', 'f', 'm'], # fcvt.w.s
    ['x', 'f', 'm'], # fcvt.wu.s
    ['x', 'f'], # fmv.x.w
    ['x', 'f', 'f'], # feq.s
    ['x', 'f', 'f'], # flt.s
    ['x', 'f', 'f'], # fle.s
    ['x', 'f'], # fclass.s
    ['f', 'x', 'm'], # fcvt.s.w
    ['f', 'x', 'm'], # fcvt.s.wu
    ['f', 'x'], # fmv.w.x

    ['x', 'f', 'm'], # fcvt.l.s
    ['x', 'f', 'm'], # fcvt.lu.s
    ['f', 'x', 'm'], # fcvt.s.l
    ['f', 'x', 'm'], # fcvt.s.lu

    ['f', 'x', ''], # fld
    ['f', 'x', ''], # fsd
    ['f', 'f', 'f', 'f', 'm'], # fmadd.d
    ['f', 'f', 'f', 'f', 'm'], # fmsub.d
    ['f', 'f', 'f', 'f', 'm'], # fnmsub.d
    ['f', 'f', 'f', 'f', 'm'], # fnmadd.d
    ['f', 'f', 'f', 'm'], # fadd.d
    ['f', 'f', 'f', 'm'], # fsub.d
    ['f', 'f', 'f', 'm'], # fmul.d
    ['f', 'f', 'f', 'm'], # fdiv.d
    ['f', 'f', 'm'], # fsqrt.d
    ['f', 'f', 'f'], # fsgnj.d
    ['f', 'f', 'f'], # fsgnjn.d
    ['f', 'f', 'f'], # fsgnjx.d
    ['f', 'f', 'f'], # fmin.d
    ['f', 'f', 'f'], # fmax.d
    ['f', 'f', 'm'], # fcvt.s.d
    ['f', 'f', 'm'], # fcvt.d.s
    ['x', 'f', 'f'], # feq.d
    ['x', 'f', 'f'], # flt.d
    ['x', 'f', 'f'], # fle.d
    ['x', 'f'], # fclass.d
    ['x', 'f', 'm'], # fcvt.w.d
    ['x', 'f', 'm'], # fcvt.wu.d
    ['f', 'x', 'm'], # fcvt.d.w
    ['f', 'x', 'm'], # fcvt.d.wu

    ['x', 'f', 'm'], # fcvt.l.d
    ['x', 'f', 'm'], # fcvt.lu.d
    ['x', 'f'], # fmv.x.d
    ['f', 'x', 'm'], # fcvt.d.l
    ['f', 'x', 'm'], # fcvt.d.lu
    ['f', 'x'], # fmv.d.x

    ['c', ''], # c.addi4spn
    ['cf', 'c', ''], # c.fld
    # ['c', 'c', ''], # c.lq
    ['c', 'c', ''], # c.lw
    ['cf', 'c', ''], # c.flw
    ['c', 'c', ''], # c.ld
    ['cf', 'c', ''], # c.fsd
    # ['c', 'c', ''], # c.sq
    ['c', 'c', ''], # c.sw
    ['cf', 'c', ''], # c.fsw
    ['c', 'c', ''], # c.sd
    [''], # c.nop
    ['x', ''], # c.addi
    [''], # c.jal
    ['x', ''], # c.addiw
    ['x', ''], # c.li
    [''], # c.addi16sp
    ['x', ''], # c.lui
    ['c', ''], # c.srli
    ['c'], # c.srli64
    ['c', ''], # c.srai
    ['c'], # c.srai64
    ['c', ''], # c.andi
    ['c', 'c'], # c.sub
    ['c', 'c'], # c.xor
    ['c', 'c'], # c.or
    ['c', 'c'], # c.and
    ['c', 'c'], # c.subw
    ['c', 'c'], # c.addw
    [''], # c.j
    ['c', ''], # c.beqz
    ['c', ''], # c.bnez
    ['x', ''], # c.slli
    ['x'], # c.slli64
    ['f', ''], # c.fldsp
    # ['x', ''], # c.lqsp
    ['x', ''], # c.lwsp
    ['x', ''], # c.flwsp
    ['x', ''], # c.ldsp
    ['x'], # c.jr
    ['x', 'x'], # c.mv
    [], # c.ebreak
    ['x'], # c.jalr
    ['x', 'x'], # c.add
    ['f', ''], # c.fsdsp
    # ['x', ''], # c.sqsp
    ['x', ''], # c.swsp
    ['f', ''], # c.fswsp
    ['x', ''], # c.sdsp
]

PARAM_IS_SIGNED = [
    [False, False],        # lui
    [False, False],        # auipc
    [False, True],         # jal
    [False, False, True],  # jalr
    [False, False, True],  # beq
    [False, False, True],  # bne
    [False, False, True],  # blt
    [False, False, True],  # bge
    [False, False, True],  # bltu
    [False, False, True],  # bgeu
    [False, False, True],  # lb
    [False, False, True],  # lh
    [False, False, True],  # lw
    [False, False, True],  # lbu
    [False, False, True],  # lhu
    [False, False, True],  # sb
    [False, False, True],  # sh
    [False, False, True],  # sw
    [False, False, True],  # addi
    [False, False, True],  # slti
    [False, False, True],  # sltiu
    [False, False, True],  # xori
    [False, False, True],  # ori
    [False, False, True],  # andi
    [False, False, False], # slli
    [False, False, False], # srli
    [False, False, False], # srai
    [False, False, False], # add
    [False, False, False], # sub
    [False, False, False], # sll
    [False, False, False], # slt
    [False, False, False], # sltu
    [False, False, False], # xor
    [False, False, False], # srl
    [False, False, False], # sra
    [False, False, False], # or
    [False, False, False], # and
    [],                    # fence
    [],                    # ecall
    [],                    # ebreak

    [False, False, True], # lwu
    [False, False, True], # ld
    [False, False, True], # sd
    [False, False, True],  # addiw
    [False, False, False], # slliw
    [False, False, False], # srliw
    [False, False, False], # sraiw
    [False, False, False], # addw
    [False, False, False], # subw
    [False, False, False], # sllw
    [False, False, False], # srlw
    [False, False, False], # sraw

    [], # fencei

    [False, False, False], # csrrw
    [False, False, False], # csrrs
    [False, False, False], # csrrc
    [False, False, False], # csrrwi
    [False, False, False], # csrrsi
    [False, False, False], # csrrci

    [False, False, False], # mul
    [False, False, False], # mulh
    [False, False, False], # mulhsu
    [False, False, False], # mulhu
    [False, False, False], # div
    [False, False, False], # divu
    [False, False, False], # rem
    [False, False, False], # remu

    [False, False, False], # mulw
    [False, False, False], # divw
    [False, False, False], # divuw
    [False, False, False], # remw
    [False, False, False], # remuw

    [False, False, False, False], # lr.w
    [False, False, False, False, False], # sc.w
    [False, False, False, False, False], # amoswap.w
    [False, False, False, False, False], # amoadd.w
    [False, False, False, False, False], # amoxor.w
    [False, False, False, False, False], # amoand.w
    [False, False, False, False, False], # amoor.w
    [False, False, False, False, False], # amomin.w
    [False, False, False, False, False], # amomax.w
    [False, False, False, False, False], # amominu.w
    [False, False, False, False, False], # amomaxu.w

    [False, False, False, False], # lr.d
    [False, False, False, False, False], # sc.d
    [False, False, False, False, False], # amoswap.d
    [False, False, False, False, False], # amoadd.d
    [False, False, False, False, False], # amoxor.d
    [False, False, False, False, False], # amoand.d
    [False, False, False, False, False], # amoor.d
    [False, False, False, False, False], # amomin.d
    [False, False, False, False, False], # amomax.d
    [False, False, False, False, False], # amominu.d
    [False, False, False, False, False], # amomaxu.d

    [False, False, True], # flw
    [False, False, True], # fsw
    [False, False, False, False, False], # fmadd.s
    [False, False, False, False, False], # fmsub.s
    [False, False, False, False, False], # fnmsub.s
    [False, False, False, False, False], # fnmadd.s
    [False, False, False, False], # fadd.s
    [False, False, False, False], # fsub.s
    [False, False, False, False], # fmul.s
    [False, False, False, False], # fdiv.s
    [False, False, False], # fsqrt.s
    [False, False, False], # fsgnj.s
    [False, False, False], # fsgnjn.s
    [False, False, False], # fsgnjx.s
    [False, False, False], # fmin.s
    [False, False, False], # fmax.s
    [False, False, False], # fcvt.w.s
    [False, False, False], # fcvt.wu.s
    [False, False], # fmv.x.w
    [False, False, False], # feq.s
    [False, False, False], # flt.s
    [False, False, False], # fle.s
    [False, False], # fclass.s
    [False, False, False], # fcvt.s.w
    [False, False, False], # fcvt.s.wu
    [False, False], # fmv.w.x

    [False, False, False], # fcvt.l.s
    [False, False, False], # fcvt.lu.s
    [False, False, False], # fcvt.s.l
    [False, False, False], # fcvt.s.lu

    [False, False, True], # fld
    [False, False, True], # fsd
    [False, False, False, False, False], # fmadd.d
    [False, False, False, False, False], # fmsub.d
    [False, False, False, False, False], # fnmsub.d
    [False, False, False, False, False], # fnmadd.d
    [False, False, False, False], # fadd.d
    [False, False, False, False], # fsub.d
    [False, False, False, False], # fmul.d
    [False, False, False, False], # fdiv.d
    [False, False, False], # fsqrt.d
    [False, False, False], # fsgnj.d
    [False, False, False], # fsgnjn.d
    [False, False, False], # fsgnjx.d
    [False, False, False], # fmin.d
    [False, False, False], # fmax.d
    [False, False, False], # fcvt.s.d
    [False, False, False], # fcvt.d.s
    [False, False, False], # feq.d
    [False, False, False], # flt.d
    [False, False, False], # fle.d
    [False, False], # fclass.d
    [False, False, False], # fcvt.w.d
    [False, False, False], # fcvt.wu.d
    [False, False, False], # fcvt.d.w
    [False, False, False], # fcvt.d.wu

    [False, False, False], # fcvt.l.d
    [False, False, False], # fcvt.lu.d
    [False, False], # fmv.x.d
    [False, False, False], # fcvt.d.l
    [False, False, False], # fcvt.d.lu
    [False, False], # fmv.d.x

    [False, False], # c.addi4spn
    [False, False, False], # c.fld
    # [False, False, False], # c.lq
    [False, False, False], # c.lw
    [False, False, False], # c.flw
    [False, False, False], # c.ld
    [False, False, False], # c.fsd
    # [False, False, False], # c.sq
    [False, False, False], # c.sw
    [False, False, False], # c.fsw
    [False, False, False], # c.sd
    [True], # c.nop
    [False, True], # c.addi
    [True], # c.jal
    [False, True], # c.addiw
    [False, True], # c.li
    [True], # c.addi16sp
    [False, False], # c.lui
    [False, False], # c.srli
    [False], # c.srli64
    [False, False], # c.srai
    [False], # c.srai64
    [False, True], # c.andi
    [False, False], # c.sub
    [False, False], # c.xor
    [False, False], # c.or
    [False, False], # c.and
    [False, False], # c.subw
    [False, False], # c.addw
    [True], # c.j
    [False, True], # c.beqz
    [False, True], # c.bnez
    [False, False], # c.slli
    [False], # c.slli64
    [False, False], # c.fldsp
    # [False, False], # c.lqsp
    [False, False], # c.lwsp
    [False, False], # c.flwsp
    [False, False], # c.ldsp
    [False], # c.jr
    [False, False], # c.mv
    [], # c.ebreak
    [False], # c.jalr
    [False, False], # c.add
    [False, False], # c.fsdsp
    # [False, False], # c.sqsp
    [False, False], # c.swsp
    [False, False], # c.fswsp
    [False, False], # c.sdsp
]
