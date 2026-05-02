# Reduces a single failing cva6_upstream program to its smallest still-failing
# prefix and writes both `app_buggy.elf` (still triggers the upstream RTL
# tohost=0x7FFFFFFF timeout) and `app_ok.elf` (one instruction shorter, runs
# to CASCADE_STOP cleanly), together with their disassemblies.
#
# Reuses cascade.reduce.reduce_program — the existing oracle (is_mismatch)
# routes through runtest_simulator, which for *_upstream designs calls
# run_upstream_verilator_with_regcheck. That returns is_success=False on the
# tohost-failure path, so the binary search converges on the offending
# instruction without any oracle changes.
#
# Caveat: for some upstream-cva6 truncations Spike itself wedges (the same
# pathological sequence that hangs CVA6 also makes Spike's debug-cmd loop
# never reach the next `until pc` target). We monkey-patch is_mismatch to
# treat that as "still failing" so the binary search keeps narrowing in.

from cascade import reduce as _reduce_mod
from cascade.reduce import reduce_program
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed

import os

_orig_is_mismatch = _reduce_mod.is_mismatch


def _is_mismatch_robust(*args, **kwargs):
    try:
        return _orig_is_mismatch(*args, **kwargs)
    except Exception as e:
        msg = str(e)
        if 'Spike timeout' in msg or 'timed out' in msg.lower():
            print('[reduce-upstream] Spike wedged on this truncation -> treating as still-failing')
            return True
        raise


_reduce_mod.is_mismatch = _is_mismatch_robust


if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    design_name = 'cva6_upstream'
    descriptor = (672243, design_name, 171, 49, False)

    calibrate_spikespeed()
    profile_get_medeleg_mask(design_name)

    reduce_program(*descriptor, find_pillars=False, check_pc_spike_again=False)

else:
    raise Exception("This module must be at the toplevel.")
