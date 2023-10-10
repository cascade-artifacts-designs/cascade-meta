# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This utility defines which workaround should be disabled.
# This allows, for example, to measure time to bug detection.
# Some bugs must be reintroduced in hw and cannot simply be reintroduced as a non-workaround in the fuzzer.

__NO_INTERACTION_MINSTRET = False
def is_no_interaction_minstret(design_name):
    return __NO_INTERACTION_MINSTRET or 'cva6' in design_name

###
# BOOM
###

__TOLERATE_BOOM_MINSTRET = False
def is_tolerate_boom_minstret():
    return __TOLERATE_BOOM_MINSTRET
if __TOLERATE_BOOM_MINSTRET:
    print('WARNING: Tolerating one bug: __TOLERATE_BOOM_MINSTRET')

###
# Rocket
###

__TOLERATE_ROCKET_MINSTRET = False
def is_tolerate_rocket_minstret():
    return __TOLERATE_ROCKET_MINSTRET
if __TOLERATE_ROCKET_MINSTRET:
    print('WARNING: Tolerating one bug: __TOLERATE_ROCKET_MINSTRET')

###
# CVA6
###

# This specific one is not used because we use cva6-c1 where the bug is reinjected
__TOLERATE_CVA6_FMULD_RDN = False
def is_tolerate_cva6_fmuld_rdn():
    return __TOLERATE_CVA6_FMULD_RDN
if __TOLERATE_CVA6_FMULD_RDN:
    print('WARNING: Tolerating one bug: __TOLERATE_CVA6_FMULD_RDN')

__TOLERATE_CVA6_SINGLE_PRECISION = False
def is_tolerate_cva6_single_precision():
    return __TOLERATE_CVA6_SINGLE_PRECISION
if __TOLERATE_CVA6_SINGLE_PRECISION:
    print('WARNING: Tolerating one bug: __TOLERATE_CVA6_SINGLE_PRECISION')

__TOLERATE_CVA6_DIVISION = False
def is_tolerate_cva6_division():
    return __TOLERATE_CVA6_DIVISION
if __TOLERATE_CVA6_DIVISION:
    print('WARNING: Tolerating one bug: __TOLERATE_CVA6_DIVISION')

__TOLERATE_CVA6_FDIVS_FLAGS = False
def is_tolerate_cva6_fdivs_flags():
    return __TOLERATE_CVA6_FDIVS_FLAGS
if __TOLERATE_CVA6_FDIVS_FLAGS:
    print('WARNING: Tolerating one bug: __TOLERATE_CVA6_FDIVS_FLAGS')

__TOLERATE_CVA6_MHPMCOUNTER = False
def is_tolerate_cva6_mhpmcounter():
    return __TOLERATE_CVA6_MHPMCOUNTER
if __TOLERATE_CVA6_MHPMCOUNTER:
    print('WARNING: Tolerating one bug: __TOLERATE_CVA6_MHPMCOUNTER')

__TOLERATE_CVA6_MHPMEVENT31 = False
def is_tolerate_cva6_mhpmevent31():
    return __TOLERATE_CVA6_MHPMEVENT31
if __TOLERATE_CVA6_MHPMEVENT31:
    print('WARNING: Tolerating one bug: __TOLERATE_CVA6_MHPMEVENT31')

###
# Kronos
###

__TOLERATE_KRONOS_READBADCSR = False
def is_tolerate_kronos_readbadcsr():
    return __TOLERATE_KRONOS_READBADCSR
if __TOLERATE_KRONOS_READBADCSR:
    print('WARNING: Tolerating one bug: __TOLERATE_KRONOS_READBADCSR')

__TOLERATE_KRONOS_MINSTRET = False
def is_tolerate_kronos_minstret():
    return __TOLERATE_KRONOS_MINSTRET
if __TOLERATE_KRONOS_MINSTRET:
    print('WARNING: Tolerating one bug: __TOLERATE_KRONOS_MINSTRET')

__TOLERATE_KRONOS_FENCE = False
def is_tolerate_kronos_fence():
    return __TOLERATE_KRONOS_FENCE
if __TOLERATE_KRONOS_FENCE:
    print('WARNING: Tolerating one bug: __TOLERATE_KRONOS_FENCE')


###
# Picorv32
###

__TOLERATE_PICORV32_READNONIMPLCSR = False
def is_tolerate_picorv32_readnonimplcsr():
    return __TOLERATE_PICORV32_READNONIMPLCSR
if __TOLERATE_PICORV32_READNONIMPLCSR:
    print('WARNING: Tolerating one bug: __TOLERATE_PICORV32_READNONIMPLCSR')

__TOLERATE_PICORV32_MISSINGMANDATORYCSRS = False
def is_tolerate_picorv32_missingmandatorycsrs():
    return __TOLERATE_PICORV32_MISSINGMANDATORYCSRS
if __TOLERATE_PICORV32_MISSINGMANDATORYCSRS:
    print('WARNING: Tolerating one bug: __TOLERATE_PICORV32_MISSINGMANDATORYCSRS')

__TOLERATE_PICORV32_FENCE = False
def is_tolerate_picorv32_fence():
    return __TOLERATE_PICORV32_FENCE
if __TOLERATE_PICORV32_FENCE:
    print('WARNING: Tolerating one bug: __TOLERATE_PICORV32_FENCE')

__TOLERATE_PICORV32_WRITEHPM = False
def is_tolerate_picorv32_writehpm():
    return __TOLERATE_PICORV32_WRITEHPM
if __TOLERATE_PICORV32_WRITEHPM:
    print('WARNING: Tolerating one bug: __TOLERATE_PICORV32_WRITEHPM')

__TOLERATE_PICORV32_READHPM_NOCSRRS = False
def is_tolerate_picorv32_readhpm_nocsrrs():
    return __TOLERATE_PICORV32_READHPM_NOCSRRS
if __TOLERATE_PICORV32_READHPM_NOCSRRS:
    print('WARNING: Tolerating one bug: __TOLERATE_PICORV32_READHPM_NOCSRRS')

###
# VexRiscv
###

# This prevents detecting the other bugs when using the pre-fpu-fix Vexriscv version.
__FORBID_VEXRISCV_CSRS = False
def is_forbid_vexriscv_csrs():
    return __FORBID_VEXRISCV_CSRS
if __FORBID_VEXRISCV_CSRS:
    print('WARNING: Forbidding one bug: __FORBID_VEXRISCV_CSRS')



__TOLERATE_VEXRISCV_MINSTRET = False
def is_tolerate_vexriscv_minstret():
    return __TOLERATE_VEXRISCV_MINSTRET
if __TOLERATE_VEXRISCV_MINSTRET:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_MINSTRET')

__TOLERATE_VEXRISCV_IMPRECISE_FCVT = False
def is_tolerate_vexriscv_imprecise_fcvt():
    return __TOLERATE_VEXRISCV_IMPRECISE_FCVT
if __TOLERATE_VEXRISCV_IMPRECISE_FCVT:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_IMPRECISE_FCVT')

__TOLERATE_VEXRISCV_FMIN = False
def is_tolerate_vexriscv_fmin():
    return __TOLERATE_VEXRISCV_FMIN
if __TOLERATE_VEXRISCV_FMIN:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_FMIN')

__TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT = False
def is_tolerate_vexriscv_double_to_float():
    return __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT
if __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT')

__TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION = False
def is_tolerate_vexriscv_dependent_single_precision():
    return __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION
if __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION')

__TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1 = False
def is_tolerate_vexriscv_dependent_fle_feq_ret1():
    return __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1
if __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1')

__TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0 = False
def is_tolerate_vexriscv_dependent_flt_ret0():
    return __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0
if __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0')

__TOLERATE_VEXRISCV_SQRT = False
def is_tolerate_vexriscv_sqrt():
    return __TOLERATE_VEXRISCV_SQRT
if __TOLERATE_VEXRISCV_SQRT:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_SQRT')

__TOLERATE_VEXRISCV_MULDIV_CONVERSION = False
def is_tolerate_vexriscv_muldiv_conversion():
    return __TOLERATE_VEXRISCV_MULDIV_CONVERSION
if __TOLERATE_VEXRISCV_MULDIV_CONVERSION:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_MULDIV_CONVERSION')

__TOLERATE_VEXRISCV_FPU_DISABLED = False
def is_tolerate_vexriscv_fpu_disabled():
    return __TOLERATE_VEXRISCV_FPU_DISABLED
if __TOLERATE_VEXRISCV_FPU_DISABLED:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_FPU_DISABLED')

__TOLERATE_VEXRISCV_FPU_LEAK = False
def is_tolerate_vexriscv_fpu_leak():
    return __TOLERATE_VEXRISCV_FPU_LEAK
if __TOLERATE_VEXRISCV_FPU_LEAK:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_FPU_LEAK')

__TOLERATE_VEXRISCV_MHPMCOUNTERN = False
def is_tolerate_vexriscv_mhpmcountern():
    return __TOLERATE_VEXRISCV_MHPMCOUNTERN
if __TOLERATE_VEXRISCV_MHPMCOUNTERN:
    print('WARNING: Tolerating one bug: __TOLERATE_VEXRISCV_MHPMCOUNTERN')


# Toleration function for timing the reduction
def tolerate_bug_for_eval_reduction(design_name: str , is_activate: bool = True):
    global __TOLERATE_BOOM_MINSTRET
    global __TOLERATE_ROCKET_MINSTRET
    global __TOLERATE_CVA6_MHPMCOUNTER
    global __TOLERATE_CVA6_FDIVS_FLAGS
    global __TOLERATE_KRONOS_MINSTRET
    global __TOLERATE_PICORV32_FENCE
    global __TOLERATE_VEXRISCV_MINSTRET
    if design_name == 'boom':
        __TOLERATE_BOOM_MINSTRET = is_activate
        print(f"WARNING: Tolerating one bug for evaluating reduction (activate: {is_activate}): __TOLERATE_BOOM_MINSTRET")
    elif design_name == 'rocket':
        __TOLERATE_ROCKET_MINSTRET = is_activate
        print(f"WARNING: Tolerating one bug for evaluating reduction (activate: {is_activate}): __TOLERATE_ROCKET_MINSTRET")
    elif design_name == 'cva6':
        __TOLERATE_CVA6_MHPMCOUNTER = is_activate
        # __TOLERATE_CVA6_FDIVS_FLAGS = is_activate
        print(f"WARNING: Tolerating one bug for evaluating reduction (activate: {is_activate}): __TOLERATE_CVA6_MHPMCOUNTER")
    elif design_name == 'kronos':
        __TOLERATE_KRONOS_MINSTRET = is_activate
        print(f"WARNING: Tolerating one bug for evaluating reduction (activate: {is_activate}): __TOLERATE_KRONOS_MINSTRET")
    elif design_name == 'picorv32':
        __TOLERATE_PICORV32_FENCE = is_activate
        print(f"WARNING: Tolerating one bug for evaluating reduction (activate: {is_activate}): __TOLERATE_PICORV32_FENCE")
    elif design_name == 'vexriscv':
        __TOLERATE_VEXRISCV_MINSTRET = is_activate
        print(f"WARNING: Tolerating one bug for evaluating reduction (activate: {is_activate}): __TOLERATE_VEXRISCV_MINSTRET")
    else:
        raise Exception('Unknown design name in __tolerate_bug_for_eval_reduction: ' + design_name)


# Toleration function for timing the reduction
# Design name is simply used for sanity checking
# @param is_activate: if false, then de-tolerate the bug
def tolerate_bug_for_bug_timing(design_name: str, bug_name: str, is_activate: bool):
    global __TOLERATE_PICORV32_READNONIMPLCSR
    global __TOLERATE_PICORV32_MISSINGMANDATORYCSRS
    global __TOLERATE_PICORV32_WRITEHPM
    global __TOLERATE_PICORV32_READHPM_NOCSRRS
    global __TOLERATE_PICORV32_FENCE    
    global __TOLERATE_VEXRISCV_IMPRECISE_FCVT
    global __TOLERATE_VEXRISCV_FMIN
    global __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT
    global __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION
    global __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1
    global __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0
    global __TOLERATE_VEXRISCV_SQRT
    global __TOLERATE_VEXRISCV_MULDIV_CONVERSION
    global __TOLERATE_VEXRISCV_FPU_DISABLED
    global __TOLERATE_VEXRISCV_FPU_LEAK
    global __TOLERATE_VEXRISCV_MHPMCOUNTERN
    global __TOLERATE_VEXRISCV_MINSTRET
    global __TOLERATE_KRONOS_READBADCSR
    global __TOLERATE_KRONOS_MINSTRET
    global __TOLERATE_KRONOS_FENCE
    global __TOLERATE_CVA6_FMULD_RDN
    global __TOLERATE_CVA6_FDIVS_FLAGS
    global __TOLERATE_CVA6_MHPMCOUNTER
    global __TOLERATE_CVA6_MHPMEVENT31
    global __TOLERATE_BOOM_MINSTRET
    global __TOLERATE_ROCKET_MINSTRET
    global __TOLERATE_CVA6_SINGLE_PRECISION
    global __TOLERATE_CVA6_DIVISION

    # Picorv32

    if bug_name == 'p1':
        assert design_name == 'picorv32', 'Bug p1 is only for picorv32'
        __TOLERATE_PICORV32_READNONIMPLCSR = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_PICORV32_READNONIMPLCSR')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_PICORV32_READNONIMPLCSR')
    elif bug_name == 'p2':
        assert design_name == 'picorv32', 'Bug p2 is only for picorv32'
        __TOLERATE_PICORV32_MISSINGMANDATORYCSRS = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_PICORV32_MISSINGMANDATORYCSRS')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_PICORV32_MISSINGMANDATORYCSRS')
    elif bug_name == 'p3':
        assert design_name == 'picorv32', 'Bug p3 is only for picorv32'
        __TOLERATE_PICORV32_WRITEHPM = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_PICORV32_WRITEHPM')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_PICORV32_WRITEHPM')
    elif bug_name == 'p4':
        assert design_name == 'picorv32', 'Bug p4 is only for picorv32'
        __TOLERATE_PICORV32_READHPM_NOCSRRS = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_PICORV32_READHPM_NOCSRRS')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_PICORV32_READHPM_NOCSRRS')
    elif bug_name == 'p5':
        assert design_name == 'picorv32-p5', 'Bug p5 is only for picorv32-p5'
    elif bug_name == 'p6':
        assert design_name == 'picorv32', 'Bug p6 is only for picorv32'
        __TOLERATE_PICORV32_FENCE = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_PICORV32_FENCE')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_PICORV32_FENCE')

    # Vexriscv

    elif bug_name == 'v1':
        assert design_name == 'vexriscv-v1-7', 'Bug v1 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_IMPRECISE_FCVT = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_IMPRECISE_FCVT')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_IMPRECISE_FCVT')
    elif bug_name == 'v2':
        assert design_name == 'vexriscv-v1-7', 'Bug v2 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_FMIN = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_FMIN')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_FMIN')
    elif bug_name == 'v3':
        assert design_name == 'vexriscv-v1-7', 'Bug v3 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT')
    elif bug_name == 'v4':
        assert design_name == 'vexriscv-v1-7', 'Bug v4 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION')
    elif bug_name == 'v5':
        assert design_name == 'vexriscv-v1-7', 'Bug v5 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1 = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_FLE_FEQ_RET1')
    elif bug_name == 'v6':
        assert design_name == 'vexriscv-v1-7', 'Bug v6 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0 = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_FLT_RET0')
    elif bug_name == 'v7':
        assert design_name == 'vexriscv-v1-7', 'Bug v7 is only for vexriscv-v1-7'
        __TOLERATE_VEXRISCV_SQRT = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_SQRT')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_SQRT')
    elif bug_name == 'v8':
        assert design_name == 'vexriscv-v8-9-v15', 'Bug v8 is only for vexriscv-v8-9-v15'
        __TOLERATE_VEXRISCV_IMPRECISE_FCVT = is_activate
        __TOLERATE_VEXRISCV_FMIN = is_activate
        __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT = is_activate
        __TOLERATE_VEXRISCV_SQRT = is_activate
        __TOLERATE_VEXRISCV_MULDIV_CONVERSION = is_activate
        __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: v8-bundle')
        else:
            print('INFO: De-tolerating one bug for timing: v8-bundle')
    elif bug_name == 'v9':
        assert design_name == 'vexriscv-v8-9-v15', 'Bug v9 is only for vexriscv-v8-9-v15'
        __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION = is_activate
        __TOLERATE_VEXRISCV_IMPRECISE_FCVT = is_activate
        __TOLERATE_VEXRISCV_FMIN = is_activate
        __TOLERATE_VEXRISCV_DOUBLE_TO_FLOAT = is_activate
        __TOLERATE_VEXRISCV_SQRT = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: v9-bundle')
        else:
            print('INFO: De-tolerating one bug for timing: v9-bundle')
    elif bug_name == 'v10':
        assert design_name == 'vexriscv-v10-11', 'Bug v10 is only for vexriscv-v10-11'
        __TOLERATE_VEXRISCV_FPU_DISABLED = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_FPU_DISABLED')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_FPU_DISABLED')
    elif bug_name == 'v11':
        assert design_name == 'vexriscv-v10-11', 'Bug v11 is only for vexriscv-v10-11'
        __TOLERATE_VEXRISCV_FPU_LEAK = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_FPU_LEAK')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_FPU_LEAK')
    # elif bug_name == 'v12':
    #     assert design_name == 'vexriscv-v12', 'Bug v12 is only for vexriscv-v12'
    #     __TOLERATE_VEXRISCV_MHPMCOUNTERN = is_activate
    #     if is_activate:
    #         print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_MHPMCOUNTERN')
    #     else:
    #         print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_MHPMCOUNTERN')
    elif bug_name == 'v12':
        assert design_name == 'vexriscv-v13', 'Bug v12 is only for vexriscv-v13'
    elif bug_name == 'v13':
        assert design_name == 'vexriscv', 'Bug v13 is only for vexriscv-v14'
        __TOLERATE_VEXRISCV_MINSTRET = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_MINSTRET')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_MINSTRET')
    elif bug_name == 'v14':
        assert design_name == 'vexriscv-v8-9-v15', 'Bug v14 is only for vexriscv-v8-9-v15'
        __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_VEXRISCV_DEPENDENT_SINGLE_PRECISION')

    # Kronos

    elif bug_name == 'k1':
        assert design_name == 'kronos-k1', 'Bug k1 is only for kronos-k1'
    elif bug_name == 'k2':
        assert design_name == 'kronos-k2', 'Bug k2 is only for kronos-k2'
    elif bug_name == 'k3':
        assert design_name == 'kronos', 'Bug k3 is only for kronos'
        __TOLERATE_KRONOS_READBADCSR = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_KRONOS_READBADCSR')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_KRONOS_READBADCSR')
    elif bug_name == 'k4':
        assert design_name == 'kronos', 'Bug k4 is only for kronos'
        __TOLERATE_KRONOS_MINSTRET = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_KRONOS_MINSTRET')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_KRONOS_MINSTRET')
    elif bug_name == 'k5':
        assert design_name == 'kronos', 'Bug k5 is only for kronos'
        __TOLERATE_KRONOS_FENCE = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_KRONOS_FENCE')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_KRONOS_FENCE')

    # CVA6

    elif bug_name == 'c1':
        assert design_name == 'cva6-c1', 'Bug c1 is only for cva6-c1'
        __TOLERATE_CVA6_FMULD_RDN = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_FMULD_RDN')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_FMULD_RDN')
    elif bug_name == 'c2':
        assert design_name == 'cva6', f"Bug {bug_name} is only for cva6"
        __TOLERATE_CVA6_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
    elif bug_name == 'c3':
        assert design_name == 'cva6', f"Bug {bug_name} is only for cva6"
        __TOLERATE_CVA6_DIVISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_DIVISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_DIVISION')
    elif bug_name == 'c4':
        assert design_name == 'cva6', f"Bug {bug_name} is only for cva6"
        __TOLERATE_CVA6_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
    elif bug_name == 'c5':
        assert design_name == 'cva6', f"Bug {bug_name} is only for cva6"
        __TOLERATE_CVA6_DIVISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_DIVISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_DIVISION')
    elif bug_name == 'c6':
        assert design_name == 'cva6', f"Bug {bug_name} is only for cva6"
        __TOLERATE_CVA6_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
    elif bug_name == 'c7':
        assert design_name == 'cva6', f"Bug {bug_name} is only for cva6"
        __TOLERATE_CVA6_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
    elif bug_name == 'c8':
        assert design_name == 'cva6', 'Bug c8 is only for cva6'
        __TOLERATE_CVA6_MHPMCOUNTER = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_MHPMCOUNTER')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_MHPMCOUNTER')
    elif bug_name == 'c9':
        assert design_name == 'cva6', 'Bug c9 is only for cva6'
        __TOLERATE_CVA6_MHPMEVENT31 = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_MHPMEVENT31')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_MHPMEVENT31')
    elif bug_name == 'c10':
        assert design_name == 'cva6', 'Bug c9 is only for cva6'
        __TOLERATE_CVA6_SINGLE_PRECISION = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_CVA6_SINGLE_PRECISION')

    # BOOM

    elif bug_name == 'b1':
        assert design_name == 'boom-b1', 'Bug b1 is only for boom-b1'
    elif bug_name == 'b2':
        assert design_name == 'boom', 'Bug b2 is only for boom'
        __TOLERATE_BOOM_MINSTRET = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_BOOM_MINSTRET')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_BOOM_MINSTRET')

    # Rocket

    elif bug_name == 'r1':
        assert design_name == 'rocket', 'Bug r1 is only for rocket'
        __TOLERATE_ROCKET_MINSTRET = is_activate
        if is_activate:
            print('WARNING: Tolerating one bug for timing: __TOLERATE_ROCKET_MINSTRET')
        else:
            print('INFO: De-tolerating one bug for timing: __TOLERATE_ROCKET_MINSTRET')

    # Yosys

    elif bug_name == 'y1':
        assert design_name == 'cva6-y1', 'Bug y1 is only for cva6-y1'

    # Other

    else:
        raise NotImplementedError(f'Unknown bug `{bug_name}`')
