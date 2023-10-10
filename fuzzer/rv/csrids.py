import enum

class CSR_IDS(enum.IntEnum):
    ###
    # U-mode CSRs
    ###

    USTATUS    = 0x000 # Removed in the new spec
    UIE        = 0x004 # Removed in the new spec
    UTVEC      = 0x005 # Removed in the new spec

    USCRATCH   = 0x040 # Removed in the new spec
    UEPC       = 0x041 # Removed in the new spec
    UCAUSE     = 0x042 # Removed in the new spec
    UTVAL      = 0x043 # Removed in the new spec
    UIP        = 0x044 # Removed in the new spec

    FFLAGS     = 0x001 # Floating-point only
    FRM        = 0x002 # Floating-point only
    FCSR       = 0x003 # Floating-point only

    CYCLE        = 0xC00 # The output value should not be trusted
    TIME         = 0xC01 # The output value should not be trusted
    INSTRET      = 0xC02
    HPMCOUNTER3  = 0xC03
    HPMCOUNTER4  = 0xC04
    HPMCOUNTER5  = 0xC05
    HPMCOUNTER6  = 0xC06
    HPMCOUNTER7  = 0xC07
    HPMCOUNTER8  = 0xC08
    HPMCOUNTER9  = 0xC09
    HPMCOUNTER10 = 0xC0A
    HPMCOUNTER11 = 0xC0B
    HPMCOUNTER12 = 0xC0C
    HPMCOUNTER13 = 0xC0D
    HPMCOUNTER14 = 0xC0E
    HPMCOUNTER15 = 0xC0F
    HPMCOUNTER16 = 0xC10
    HPMCOUNTER17 = 0xC11
    HPMCOUNTER18 = 0xC12
    HPMCOUNTER19 = 0xC13
    HPMCOUNTER20 = 0xC14
    HPMCOUNTER21 = 0xC15
    HPMCOUNTER22 = 0xC16
    HPMCOUNTER23 = 0xC17
    HPMCOUNTER24 = 0xC18
    HPMCOUNTER25 = 0xC19
    HPMCOUNTER26 = 0xC1A
    HPMCOUNTER27 = 0xC1B
    HPMCOUNTER28 = 0xC1C
    HPMCOUNTER29 = 0xC1D
    HPMCOUNTER30 = 0xC1E
    HPMCOUNTER31 = 0xC1F

    CYCLEH        = 0xC80 # RV32I only
    TIMEH         = 0xC81 # RV32I only
    INSTRETH      = 0xC82 # RV32I only
    HPMCOUNTERH3  = 0xC83 # RV32I only
    HPMCOUNTERH4  = 0xC84 # RV32I only
    HPMCOUNTERH5  = 0xC85 # RV32I only
    HPMCOUNTERH6  = 0xC86 # RV32I only
    HPMCOUNTERH7  = 0xC87 # RV32I only
    HPMCOUNTERH8  = 0xC88 # RV32I only
    HPMCOUNTERH9  = 0xC89 # RV32I only
    HPMCOUNTERH10 = 0xC8A # RV32I only
    HPMCOUNTERH11 = 0xC8B # RV32I only
    HPMCOUNTERH12 = 0xC8C # RV32I only
    HPMCOUNTERH13 = 0xC8D # RV32I only
    HPMCOUNTERH14 = 0xC8E # RV32I only
    HPMCOUNTERH15 = 0xC8F # RV32I only
    HPMCOUNTERH16 = 0xC90 # RV32I only
    HPMCOUNTERH17 = 0xC91 # RV32I only
    HPMCOUNTERH18 = 0xC92 # RV32I only
    HPMCOUNTERH19 = 0xC93 # RV32I only
    HPMCOUNTERH20 = 0xC94 # RV32I only
    HPMCOUNTERH21 = 0xC95 # RV32I only
    HPMCOUNTERH22 = 0xC96 # RV32I only
    HPMCOUNTERH23 = 0xC97 # RV32I only
    HPMCOUNTERH24 = 0xC98 # RV32I only
    HPMCOUNTERH25 = 0xC99 # RV32I only
    HPMCOUNTERH26 = 0xC9A # RV32I only
    HPMCOUNTERH27 = 0xC9B # RV32I only
    HPMCOUNTERH28 = 0xC9C # RV32I only
    HPMCOUNTERH29 = 0xC9D # RV32I only
    HPMCOUNTERH30 = 0xC9E # RV32I only
    HPMCOUNTERH31 = 0xC9F # RV32I only

    ###
    # S-mode CSRs
    ###

    SSTATUS    = 0x100
    SEDELEG    = 0x102
    SIDELEG    = 0x103
    SIE        = 0x104
    STVEC      = 0x105
    SCOUNTEREN = 0x106

    SENCFG     = 0x10A

    SSCRATCH   = 0x140
    SEPC       = 0x141
    SCAUSE     = 0x142
    STVAL      = 0x143
    SIP        = 0x144

    SATP       = 0x180

    SCONTEXT   = 0x5A8

    ###
    # M-mode CSRs
    ###

    MVENDORID  = 0xF11
    MARCHID    = 0xF12
    MIMPID     = 0xF13
    MHARTID    = 0xF14
    MCONFIGPTR = 0xF15

    MSTATUS    = 0x300
    MISA       = 0x301
    MEDELEG    = 0x302
    MIDELEG    = 0x303
    MIE        = 0x304
    MTVEC      = 0x305
    MCOUNTEREN = 0x306
    MSTATUSH   = 0x310

    MSCRATCH   = 0x340
    MEPC       = 0x341
    MCAUSE     = 0x342
    MTVAL      = 0x343 # The output value should not be trusted
    MIP        = 0x344
    MTINST     = 0x34A
    MTVAL2     = 0x34B # The output value should not be trusted

    MENVCFG    = 0x30A
    MENVCFGH   = 0x31A
    MSECCFG    = 0x747
    MSECCFGH   = 0x757

    PMPCFG0    = 0x3A0 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG1    = 0x3A1 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG2    = 0x3A2 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG3    = 0x3A3 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG4    = 0x3A4 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG5    = 0x3A5 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG6    = 0x3A6 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG7    = 0x3A7 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG8    = 0x3A8 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFG9    = 0x3A9 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFGA    = 0x3AA # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFGB    = 0x3AB # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFGC    = 0x3AC # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFGD    = 0x3AD # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFGE    = 0x3AE # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPCFGF    = 0x3AF # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12

    PMPADDR0   = 0x3B0 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1   = 0x3B1 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2   = 0x3B2 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3   = 0x3B3 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR4   = 0x3B4 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR5   = 0x3B5 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR6   = 0x3B6 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR7   = 0x3B7 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR8   = 0x3B8 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR9   = 0x3B9 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDRA   = 0x3BA # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDRB   = 0x3BB # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDRC   = 0x3BC # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDRD   = 0x3BD # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDRE   = 0x3BE # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDRF   = 0x3BF # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR10  = 0x3C0 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR11  = 0x3C1 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR12  = 0x3C2 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR13  = 0x3C3 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR14  = 0x3C4 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR15  = 0x3C5 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR16  = 0x3C6 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR17  = 0x3C7 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR18  = 0x3C8 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR19  = 0x3C9 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1A  = 0x3CA # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1B  = 0x3CB # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1C  = 0x3CC # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1D  = 0x3CD # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1E  = 0x3CE # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR1F  = 0x3CF # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR20  = 0x3D0 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR21  = 0x3D1 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR22  = 0x3D2 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR23  = 0x3D3 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR24  = 0x3D4 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR25  = 0x3D5 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR26  = 0x3D6 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR27  = 0x3D7 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR28  = 0x3D8 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR29  = 0x3D9 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2A  = 0x3DA # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2B  = 0x3DB # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2C  = 0x3DC # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2D  = 0x3DD # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2E  = 0x3DE # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR2F  = 0x3DF # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR30  = 0x3E0 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR31  = 0x3E1 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR32  = 0x3E2 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR33  = 0x3E3 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR34  = 0x3E4 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR35  = 0x3E5 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR36  = 0x3E6 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR37  = 0x3E7 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR38  = 0x3E8 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR39  = 0x3E9 # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3A  = 0x3EA # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3B  = 0x3EB # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3C  = 0x3EC # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3D  = 0x3ED # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3E  = 0x3EE # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12
    PMPADDR3F  = 0x3EF # WARNING: Addresses and number change for different spec versions. Here the most recent 1.12

    MCYCLE         = 0xB00 # The output value should not be trusted
    MINSTRET       = 0xB02
    MHPMCOUNTER3   = 0xB03
    MHPMCOUNTER4   = 0xB04
    MHPMCOUNTER5   = 0xB05
    MHPMCOUNTER6   = 0xB06
    MHPMCOUNTER7   = 0xB07
    MHPMCOUNTER8   = 0xB08
    MHPMCOUNTER9   = 0xB09
    MHPMCOUNTER10  = 0xB0A
    MHPMCOUNTER11  = 0xB0B
    MHPMCOUNTER12  = 0xB0C
    MHPMCOUNTER13  = 0xB0D
    MHPMCOUNTER14  = 0xB0E
    MHPMCOUNTER15  = 0xB0F
    MHPMCOUNTER16  = 0xB10
    MHPMCOUNTER17  = 0xB11
    MHPMCOUNTER18  = 0xB12
    MHPMCOUNTER19  = 0xB13
    MHPMCOUNTER20  = 0xB14
    MHPMCOUNTER21  = 0xB15
    MHPMCOUNTER22  = 0xB16
    MHPMCOUNTER23  = 0xB17
    MHPMCOUNTER24  = 0xB18
    MHPMCOUNTER25  = 0xB19
    MHPMCOUNTER26  = 0xB1A
    MHPMCOUNTER27  = 0xB1B
    MHPMCOUNTER28  = 0xB1C
    MHPMCOUNTER29  = 0xB1D
    MHPMCOUNTER30  = 0xB1E
    MHPMCOUNTER31  = 0xB1F
    MCYCLEH        = 0xB80
    MINSTRETH      = 0xB82
    MHPMCOUNTERH3  = 0xB83 # RV32I only
    MHPMCOUNTERH4  = 0xB84 # RV32I only
    MHPMCOUNTERH5  = 0xB85 # RV32I only
    MHPMCOUNTERH6  = 0xB86 # RV32I only
    MHPMCOUNTERH7  = 0xB87 # RV32I only
    MHPMCOUNTERH8  = 0xB88 # RV32I only
    MHPMCOUNTERH9  = 0xB89 # RV32I only
    MHPMCOUNTERH10 = 0xB8A # RV32I only
    MHPMCOUNTERH11 = 0xB8B # RV32I only
    MHPMCOUNTERH12 = 0xB8C # RV32I only
    MHPMCOUNTERH13 = 0xB8D # RV32I only
    MHPMCOUNTERH14 = 0xB8E # RV32I only
    MHPMCOUNTERH15 = 0xB8F # RV32I only
    MHPMCOUNTERH16 = 0xB90 # RV32I only
    MHPMCOUNTERH17 = 0xB91 # RV32I only
    MHPMCOUNTERH18 = 0xB92 # RV32I only
    MHPMCOUNTERH19 = 0xB93 # RV32I only
    MHPMCOUNTERH20 = 0xB94 # RV32I only
    MHPMCOUNTERH21 = 0xB95 # RV32I only
    MHPMCOUNTERH22 = 0xB96 # RV32I only
    MHPMCOUNTERH23 = 0xB97 # RV32I only
    MHPMCOUNTERH24 = 0xB98 # RV32I only
    MHPMCOUNTERH25 = 0xB99 # RV32I only
    MHPMCOUNTERH26 = 0xB9A # RV32I only
    MHPMCOUNTERH27 = 0xB9B # RV32I only
    MHPMCOUNTERH28 = 0xB9C # RV32I only
    MHPMCOUNTERH29 = 0xB9D # RV32I only
    MHPMCOUNTERH30 = 0xB9E # RV32I only
    MHPMCOUNTERH31 = 0xB9F # RV32I only

    MCOUNTINHIBIT = 0x320 # RV32I only
    MHPMEVENT3    = 0x323 # RV32I only
    MHPMEVENT4    = 0x324 # RV32I only
    MHPMEVENT5    = 0x325 # RV32I only
    MHPMEVENT6    = 0x326 # RV32I only
    MHPMEVENT7    = 0x327 # RV32I only
    MHPMEVENT8    = 0x328 # RV32I only
    MHPMEVENT9    = 0x329 # RV32I only
    MHPMEVENT10   = 0x32A # RV32I only
    MHPMEVENT11   = 0x32B # RV32I only
    MHPMEVENT12   = 0x32C # RV32I only
    MHPMEVENT13   = 0x32D # RV32I only
    MHPMEVENT14   = 0x32E # RV32I only
    MHPMEVENT15   = 0x32F # RV32I only
    MHPMEVENT16   = 0x330 # RV32I only
    MHPMEVENT17   = 0x331 # RV32I only
    MHPMEVENT18   = 0x332 # RV32I only
    MHPMEVENT19   = 0x333 # RV32I only
    MHPMEVENT20   = 0x334 # RV32I only
    MHPMEVENT21   = 0x335 # RV32I only
    MHPMEVENT22   = 0x336 # RV32I only
    MHPMEVENT23   = 0x337 # RV32I only
    MHPMEVENT24   = 0x338 # RV32I only
    MHPMEVENT25   = 0x339 # RV32I only
    MHPMEVENT26   = 0x33A # RV32I only
    MHPMEVENT27   = 0x33B # RV32I only
    MHPMEVENT28   = 0x33C # RV32I only
    MHPMEVENT29   = 0x33D # RV32I only
    MHPMEVENT30   = 0x33E # RV32I only
    MHPMEVENT31   = 0x33F # RV32I only

    TSELECT  = 0x7A0
    TDATA1   = 0x7A1
    TDATA2   = 0x7A2
    TDATA3   = 0x7A3
    MCONTEXT = 0x7A3

INTERESTING_CSRS_INACCESSIBLE_FROM_SUPERVISOR = [
    CSR_IDS.MVENDORID,
    CSR_IDS.MARCHID,
    CSR_IDS.MIMPID,
    CSR_IDS.MHARTID,
    CSR_IDS.MCONFIGPTR,
    CSR_IDS.MSTATUS,
    CSR_IDS.MISA,
    CSR_IDS.MEDELEG,
    CSR_IDS.MIDELEG,
    CSR_IDS.MIE,
    CSR_IDS.MTVEC,
    CSR_IDS.MCOUNTEREN,
    CSR_IDS.MSTATUSH,
    CSR_IDS.MSCRATCH,
    CSR_IDS.MEPC,
    CSR_IDS.MCAUSE,
    CSR_IDS.MTVAL,
    CSR_IDS.MIP,
    CSR_IDS.MTINST,
    CSR_IDS.MTVAL2,
    CSR_IDS.MENVCFG,
    CSR_IDS.MENVCFGH,
    CSR_IDS.MSECCFG,
    CSR_IDS.MSECCFGH,
    CSR_IDS.PMPCFG0,
    CSR_IDS.PMPADDR0,
    CSR_IDS.MCYCLE,
    CSR_IDS.MINSTRET,
    CSR_IDS.MCYCLEH,
    CSR_IDS.MINSTRETH,
    CSR_IDS.MHPMCOUNTERH3,
    CSR_IDS.MCOUNTINHIBIT,
    CSR_IDS.MHPMEVENT3,
    CSR_IDS.TSELECT,
    CSR_IDS.TDATA1,
    CSR_IDS.TDATA2,
    CSR_IDS.TDATA3,
    CSR_IDS.MCONTEXT
]

INTERESTING_CSRS_INACCESSIBLE_FROM_USER = [
    CSR_IDS.MVENDORID,
    CSR_IDS.MARCHID,
    CSR_IDS.MIMPID,
    CSR_IDS.MHARTID,
    CSR_IDS.MCONFIGPTR,
    CSR_IDS.MSTATUS,
    CSR_IDS.MISA,
    CSR_IDS.MEDELEG,
    CSR_IDS.MIDELEG,
    CSR_IDS.MIE,
    CSR_IDS.MTVEC,
    CSR_IDS.MCOUNTEREN,
    CSR_IDS.MSTATUSH,
    CSR_IDS.MSCRATCH,
    CSR_IDS.MEPC,
    CSR_IDS.MCAUSE,
    CSR_IDS.MTVAL,
    CSR_IDS.MIP,
    CSR_IDS.MTINST,
    CSR_IDS.MTVAL2,
    CSR_IDS.MENVCFG,
    CSR_IDS.MENVCFGH,
    CSR_IDS.MSECCFG,
    CSR_IDS.MSECCFGH,
    CSR_IDS.PMPCFG0,
    CSR_IDS.PMPADDR0,
    CSR_IDS.MCYCLE,
    CSR_IDS.MINSTRET,
    CSR_IDS.MCYCLEH,
    CSR_IDS.MINSTRETH,
    CSR_IDS.MHPMCOUNTERH3,
    CSR_IDS.MCOUNTINHIBIT,
    CSR_IDS.MHPMEVENT3,
    CSR_IDS.TSELECT,
    CSR_IDS.TDATA1,
    CSR_IDS.TDATA2,
    CSR_IDS.TDATA3,
    CSR_IDS.MCONTEXT,
    CSR_IDS.SSTATUS,
    CSR_IDS.SEDELEG,
    CSR_IDS.SIDELEG,
    CSR_IDS.SIE,
    CSR_IDS.STVEC,
    CSR_IDS.SCOUNTEREN,
    CSR_IDS.SENCFG,
    CSR_IDS.SSCRATCH,
    CSR_IDS.SEPC,
    CSR_IDS.SCAUSE,
    CSR_IDS.STVAL,
    CSR_IDS.SIP,
    CSR_IDS.SATP,
    CSR_IDS.SCONTEXT
]