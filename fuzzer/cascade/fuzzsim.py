# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script is responsible for running the RTL simulations from the fuzzer.

from params.fuzzparams import MAX_NUM_PICKABLE_REGS, MAX_NUM_PICKABLE_FLOATING_REGS
from cascade.util import IntRegIndivState
from common.sim.modelsim import get_next_worker_id
from params.runparams import DO_ASSERT, PATH_TO_TMP
from common.sim.commonsim import setup_sim_env
from common import designcfgs
import itertools
import os
import subprocess
import sys
from enum import Enum

# Either Verilator or Modelsim
class SimulatorEnum(Enum):
    VERILATOR = 1
    MODELSIM = 2

# The maximum number of cycles that we allow per run is MAX_CYCLES_PER_INSTR * num_instrs + SETUP_CYCLES.
MAX_CYCLES_PER_INSTR = 30
SETUP_CYCLES = 1000 # Without this, we had issues with BOOM with very short programs (typically <20 instructions) not being able to finish in time.

# @param get_rfuzz_coverage_mask if True, then return a pair (is_stop_successful: bool, rfuzz_coverage_mask: int)
# Return a pair (is_stop_successful: bool, reg_vals: int list of length <= MAX_NUM_PICKABLE_REGS-1 or None if is_stop_successful is False)
def runsim_verilator(design_name, simlen, elfpath, num_int_regs: int = MAX_NUM_PICKABLE_REGS-1, num_float_regs: int = MAX_NUM_PICKABLE_FLOATING_REGS, coveragepath = None, get_rfuzz_coverage_mask = False):
    if DO_ASSERT:
        assert coveragepath is None or not get_rfuzz_coverage_mask

    design_cfg       = designcfgs.get_design_cfg(design_name)
    cascadedir       = designcfgs.get_design_cascade_path(design_name)
    builddir         = os.path.join(cascadedir,'build')

    my_env = setup_sim_env(elfpath, '/dev/null', '/dev/null', simlen, cascadedir, coveragepath, False)

    simdir               = f"run_{'coverage' if coveragepath else 'rfuzz' if get_rfuzz_coverage_mask else 'vanilla'}_notrace_0.1"
    verilatordir         = 'default-verilator'
    verilator_executable = 'V%s' % design_cfg['toplevel']
    sim_executable_path  = os.path.abspath(os.path.join(builddir, simdir, verilatordir, verilator_executable))

    # Run Verilator
    exec_out = subprocess.run([sim_executable_path], check=True, text=True, capture_output=True, env=my_env)
    outlines = list(filter(lambda l: 'Writing ELF word to' not in l, exec_out.stdout.split('\n')))

    # Check stop success
    is_stop_successful = 'Found a stop request.' in exec_out.stdout
    if not is_stop_successful:
        return False, None

    # Retrieve the register values
    ret_intregs = []
    ret_floatregs = []
    curr_index = 0
    for reg_id in range(1, num_int_regs+1):
        for row_id in itertools.count(curr_index):
            if len(outlines[row_id]) >= 19 and outlines[row_id][:19] == f"Dump of reg x{reg_id:02}: 0x":
                ret_intregs.append(int(outlines[row_id][19:35], 16))
                curr_index = row_id + 1
                break
    if designcfgs.design_has_float_support(design_name):
        for fp_reg_id in range(num_float_regs):
            for row_id in itertools.count(curr_index):
                if row_id >= len(outlines):
                    # This happens if the FPU is disabled in the final block and the final permission level does not permit enabling it.
                    ret_floatregs.append(None)
                    curr_index = row_id + 1
                    break
                if len(outlines[row_id]) >= 19 and outlines[row_id][:19] == f"Dump of reg f{fp_reg_id:02}: 0x":
                    ret_floatregs.append(int(outlines[row_id][19:35], 16))
                    curr_index = row_id + 1
                    break
    if get_rfuzz_coverage_mask:
        for row_id in range(curr_index, len(outlines)):
            # print('outlines[row_id]', outlines[row_id])
            if len(outlines[row_id]) >= 21 and outlines[row_id][:21] == f"RFUZZ coverage mask: ":
                rfuzz_coverage_mask = int(outlines[row_id][22:], 16)
                return True, rfuzz_coverage_mask
        raise Exception("Could not find the RFUZZ coverage mask.")
    return True, (ret_intregs, ret_floatregs)


# Return a pair (is_stop_successful: bool, reg_vals: int list of length <= MAX_NUM_PICKABLE_REGS-1 or None if is_stop_successful is False)
def runsim_modelsim(design_name, simlen, elfpath, num_int_regs: int = MAX_NUM_PICKABLE_REGS-1, num_float_regs: int = MAX_NUM_PICKABLE_FLOATING_REGS, coveragepath = None):
    cascadedir       = designcfgs.get_design_cascade_path(design_name)

    my_env = setup_sim_env(elfpath, '/dev/null', '/dev/null', simlen, cascadedir, coveragepath, False)
    # Run the simulation on the same worker id as the core used for this worker. This may not be absolutely optimal.
    curr_coreid = get_next_worker_id()
    my_env["FUZZCOREID"] = str(curr_coreid)
    my_env["MODELSIM_NOQUIT"] = '0'

    # Check whether the library exists.
    tracestr = 'notrace'
    workdir  = designcfgs.get_design_worklib_path(design_name, False, curr_coreid)[-1]
    if not os.path.exists(workdir):
        print("Error: Need {} to run this experiment. Design is {}.\n"
              "Please run 'make build_{}_{}_modelsim' to build the the modelsim library.\n"
              "Also be in the cascade dir so the path is right.\n".format(workdir, design_name, 'vanilla', tracestr, cascadedir))
        sys.exit(1)
    cmdline=['make', '-C', cascadedir, f"rerun_vanilla_{tracestr}_modelsim"]

    # We expect the simulation to take at most 4*simlen + 20 seconds.
    exec_out = subprocess.run(cmdline, cwd=workdir, check=True, text=True, capture_output=True, env=my_env, timeout=min(4*simlen + 20, 1800))

    outlines = exec_out.stdout.split('\n')
    outlines = list(map(lambda l: l[2:], filter(lambda l: 'Writing ELF word to SRAM addr' not in l, outlines))) # Remove the initial `# ` from Modelsim

    # Check stop success
    is_stop_successful = 'Found a stop request.' in exec_out.stdout
    if not is_stop_successful:
        # print('Stop not successful in runsim_modelsim', exec_out.stdout)
        return False, None

    if num_int_regs == 0 and num_float_regs == 0:
        return True, None

    # Retrieve the register values
    ret_intregs = []
    ret_floatregs = []
    curr_index = 0
    for reg_id in range(1, num_int_regs+1):
        for row_id in itertools.count(curr_index):
            if len(outlines[row_id]) >= 19 and outlines[row_id][:19] == f"Dump of reg x{reg_id:02}: 0x" or outlines[row_id][:19] == f"Dump of reg x{reg_id: 2}: 0x":
                ret_intregs.append(int(outlines[row_id][19:35], 16))
                curr_index = row_id + 1
                break

    if designcfgs.design_has_float_support(design_name):
        for fp_reg_id in range(num_float_regs):
            # print('Curr index', curr_index)
            # print('fp_reg_id', fp_reg_id)
            for row_id in itertools.count(curr_index):
                # print('Candidate:', outlines[row_id])
                if row_id >= len(outlines):
                    # This happens if the FPU is disabled in the final block and the final permission level does not permit enabling it.
                    ret_floatregs.append(None)
                    curr_index = row_id + 1
                    break
                if len(outlines[row_id]) >= 19 and outlines[row_id][:19] == f"Dump of reg f{fp_reg_id:02}: 0x" or outlines[row_id][:19] == f"Dump of reg f{fp_reg_id: 2}: 0x":
                    # print('Floating outline found:', outlines[row_id])
                    ret_floatregs.append(int(outlines[row_id][19:35], 16))
                    curr_index = row_id + 1
                    break
    return True, (ret_intregs, ret_floatregs)

# Runs the test and checks for matching.
# @param expected_regvals a pair of iterables of expected int regvals, and float regvals.
# @param override_num_instrs if not None, then use this value instead of the number of instructions in fuzzerstate.instr_objs_seq. Used when pruning to shorten a bit the timeout.
# @return (is_success: bool, msg: str)
def runtest_simulator(fuzzerstate, elfpath: str, expected_regvals: tuple, override_num_instrs: int = None, simulator=SimulatorEnum.VERILATOR):
    expected_intregvals, expected_floatregvals = expected_regvals
    del expected_regvals

    if DO_ASSERT:
        assert len(expected_intregvals) >= fuzzerstate.num_pickable_regs-1
        if fuzzerstate.design_has_fpu:
            assert len(expected_floatregvals) == fuzzerstate.num_pickable_floating_regs
    num_instrs = override_num_instrs if override_num_instrs is not None else len(list(itertools.chain.from_iterable(fuzzerstate.instr_objs_seq)))
    if simulator == SimulatorEnum.VERILATOR:
        is_stop_successful, received_regvals = runsim_verilator(fuzzerstate.design_name, num_instrs*MAX_CYCLES_PER_INSTR + SETUP_CYCLES, elfpath, fuzzerstate.num_pickable_regs-1, fuzzerstate.num_pickable_floating_regs)
    elif simulator == SimulatorEnum.MODELSIM:
        is_stop_successful, received_regvals = runsim_modelsim(fuzzerstate.design_name, num_instrs*MAX_CYCLES_PER_INSTR + SETUP_CYCLES, elfpath, fuzzerstate.num_pickable_regs-1, fuzzerstate.num_pickable_floating_regs)
    else:
        raise NotImplementedError(f"Unknown simulator {simulator}")

    # Check successful stop
    if not is_stop_successful:
        return False, f"Timeout for params: memsize: `{fuzzerstate.memsize}`, design_name: `{fuzzerstate.design_name}`, randseed: `{fuzzerstate.randseed}`, nmax_bbs: `{fuzzerstate.nmax_bbs}`, authorize_privileges: `{fuzzerstate.authorize_privileges}` -- ({fuzzerstate.memsize}, {fuzzerstate.design_name}, {fuzzerstate.randseed}, {fuzzerstate.nmax_bbs}, {fuzzerstate.authorize_privileges})"

    # Check that we retrieved the regs correctly
    if received_regvals is None:
        raise Exception(f"Missing all regs for params: memsize: `{fuzzerstate.memsize}`, design_name: `{fuzzerstate.design_name}`, randseed: `{fuzzerstate.randseed}`, nmax_bbs: `{fuzzerstate.nmax_bbs}`, authorize_privileges: `{fuzzerstate.authorize_privileges}` -- ({fuzzerstate.memsize}, {fuzzerstate.design_name}, {fuzzerstate.randseed}, {fuzzerstate.nmax_bbs}, {fuzzerstate.authorize_privileges})")

    received_intregvals, received_floatregvals = received_regvals
    del received_regvals

    if DO_ASSERT:
        assert len(received_intregvals) >= fuzzerstate.num_pickable_regs-1
        if fuzzerstate.design_has_fpu:
            assert len(received_floatregvals) == fuzzerstate.num_pickable_floating_regs, f"Wanted {fuzzerstate.num_pickable_floating_regs} floating regs. Got {len(received_floatregvals)}."

    # Compare the expected vs. received registers
    reg_mismatch = False
    freg_mismatch = False
    ret_str_list_regmismatch = []

    # Debug int regs
    debug_regs_info = []
    debug_regs = ["zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2", \
                    "s0", "s1", "a0", "a1", "a2", "a3", "a4", "a5", \
                    "a6", "a7", "s2", "s3", "s4", "s5", "s6", "s7", \
                    "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6"]

    for reg_id in range(fuzzerstate.num_pickable_regs-1):
        if expected_intregvals[reg_id] != received_intregvals[reg_id] and fuzzerstate.intregpickstate.get_regstate(reg_id+1) in (IntRegIndivState.FREE, IntRegIndivState.CONSUMED):
            reg_mismatch = True
            ret_str_list_regmismatch.append(f"Register mismatch (x{reg_id+1}) for params: memsize: `{fuzzerstate.memsize}`, design_name: `{fuzzerstate.design_name}`, randseed: `{fuzzerstate.randseed}`, nmax_bbs: `{fuzzerstate.nmax_bbs}`, authorize_privileges: `{fuzzerstate.authorize_privileges}`. State: {fuzzerstate.intregpickstate.get_regstate(reg_id+1)}. Expected `{hex(expected_intregvals[reg_id])}`, got `{hex(received_intregvals[reg_id])}`.")
        
        # Debug
        debug_regs_info.append(
                f"Debug ({debug_regs[reg_id+1]:<2}):\t Expected: {hex(expected_intregvals[reg_id]):<20}  Got: {hex(received_intregvals[reg_id]):<20}\n".replace(
                f"{hex(received_intregvals[reg_id]):<20}", 
                f"\033[91m{hex(received_intregvals[reg_id]):<20}\033[0m" if expected_intregvals[reg_id] != received_intregvals[reg_id] else f"{hex(received_intregvals[reg_id]):<20}")
            )

    # Debug fregs
    debug_fregs_info = []
    debug_fregs = ["ft0", "ft1", "ft2", "ft3", "ft4", "ft5", "ft6", "ft7", \
                   "fs0", "fs1", "fa0", "fa1", "fa2", "fa3", "fa4", "fa5", \
                   "fa6", "fa7", "fs2", "fs3", "fs4", "fs5", "fs6", "fs7", \
                   "fs8", "fs9", "fs10", "fs11", "ft8", "ft9", "ft10", "ft11"]

    if fuzzerstate.design_has_fpu:
        for fp_reg_id in range(fuzzerstate.num_pickable_floating_regs):
            # received_floatregvals[fp_reg_id] can be None if the FPU is disabled in the final block and the final permission level does not permit enabling it.
            if expected_floatregvals[fp_reg_id] != received_floatregvals[fp_reg_id] and received_floatregvals[fp_reg_id] is not None:
                freg_mismatch = True
                ret_str_list_regmismatch.append(f"Register mismatch (f{fp_reg_id}) for params: memsize: `{fuzzerstate.memsize}`, design_name: `{fuzzerstate.design_name}`, randseed: `{fuzzerstate.randseed}`, nmax_bbs: `{fuzzerstate.nmax_bbs}`, authorize_privileges: `{fuzzerstate.authorize_privileges}`. Expected `{hex(expected_floatregvals[fp_reg_id])}`, got `{hex(received_floatregvals[fp_reg_id])}`.")
        
            # Debug
            if received_floatregvals[fp_reg_id] is not None:
                debug_fregs_info.append(
                        f"Debug ({debug_fregs[fp_reg_id]:<2}):\t Expected: {hex(expected_floatregvals[fp_reg_id]):<20}  Got: {hex(received_floatregvals[fp_reg_id]):<20}\n".replace(
                        f"{hex(received_floatregvals[fp_reg_id]):<20}", 
                        f"\033[91m{hex(received_floatregvals[fp_reg_id]):<20}\033[0m" if expected_floatregvals[fp_reg_id] != received_floatregvals[fp_reg_id] else f"{hex(received_floatregvals[fp_reg_id]):<20}")
                    )
    # print mismatch int regs info
    if  reg_mismatch:
        for infos in debug_regs_info:
            print(infos, end="")
    # print mismatch float regs info
    if  freg_mismatch:
        for infos in debug_fregs_info:
            print(infos, end="")

    del debug_regs_info
    del debug_fregs_info

    return not (reg_mismatch or freg_mismatch), '\n  '.join(ret_str_list_regmismatch)


# Runs the test in the goal of collecting coverage.
# Returns nothing
def runtest_modelsim(fuzzerstate, elfpath: str, coveragepath: str):
    num_instrs = len(list(itertools.chain.from_iterable(fuzzerstate.instr_objs_seq)))
    is_stop_successful, _ = runsim_modelsim(fuzzerstate.design_name, num_instrs*MAX_CYCLES_PER_INSTR + SETUP_CYCLES, elfpath, 1, 0, coveragepath)
    # Check successful stop
    if not is_stop_successful:
        raise Exception(f"Timeout during modelsim testing of design `{fuzzerstate.design_name}` for tuple ({fuzzerstate.memsize}, {fuzzerstate.design_name}, {fuzzerstate.randseed}, {fuzzerstate.nmax_bbs}, {fuzzerstate.authorize_privileges}).")

# Runs the test and checks for a single dumped register.
# @return the value of the dumped register
def runtest_verilator_forprofiling(fuzzerstate, elfpath: str, expected_fuzzerstate_len_fordebug: int):
    if DO_ASSERT:
        assert len(fuzzerstate.instr_objs_seq) == expected_fuzzerstate_len_fordebug, f"Unexpected length of fuzzerstate: {len(fuzzerstate.instr_objs_seq)}"
    is_stop_successful, received_regvals = runsim_verilator(fuzzerstate.design_name, len(fuzzerstate.instr_objs_seq[0])*MAX_CYCLES_PER_INSTR + SETUP_CYCLES, elfpath, 1, 0)
    # Check successful stop
    if not is_stop_successful:
        raise Exception(f"Timeout during profiling of design `{fuzzerstate.design_name}`.")
    # Check that we retrieved the regs correctly
    if received_regvals is None:
        raise Exception(f"Missing all regs for params: memsize: `{fuzzerstate.memsize}`, design_name: `{fuzzerstate.design_name}`, randseed: `{fuzzerstate.randseed}`, nmax_bbs: `{fuzzerstate.nmax_bbs}`, authorize_privileges: `{fuzzerstate.authorize_privileges}`")
    received_intregvals, received_floatregvals = received_regvals
    del received_regvals
    if DO_ASSERT:
        assert len(received_intregvals) == 1
        assert len(received_floatregvals) == 0
    return received_intregvals[0]

# Runs the test in the goal of collecting RFUZZ coverage.
# Returns the Verilator coverage mask
def runtest_verilator_forrfuzz(fuzzerstate, elfpath: str):
    num_instrs = len(list(itertools.chain.from_iterable(fuzzerstate.instr_objs_seq)))
    is_stop_successful, rfuzz_coverage_mask = runsim_verilator(fuzzerstate.design_name, num_instrs*MAX_CYCLES_PER_INSTR + SETUP_CYCLES, elfpath, 1, 0, get_rfuzz_coverage_mask=True)
    # Check successful stop
    if not is_stop_successful:
        raise Exception(f"Timeout during rfuzz coverage testing of design `{fuzzerstate.design_name}` for tuple ({fuzzerstate.memsize}, {fuzzerstate.design_name}, {fuzzerstate.randseed}, {fuzzerstate.nmax_bbs}, {fuzzerstate.authorize_privileges}).")
    return rfuzz_coverage_mask

# Runs the test in the goal of collecting modelsim coverage.
# Returns nothing
def runtest_modelsim_forcoverage(fuzzerstate, elfpath: str, coveragepath: str):
    num_instrs = len(list(itertools.chain.from_iterable(fuzzerstate.instr_objs_seq)))
    is_stop_successful, _ = runsim_modelsim(fuzzerstate.design_name, num_instrs*MAX_CYCLES_PER_INSTR + SETUP_CYCLES, elfpath, 1, 0, coveragepath)
    # Check successful stop
    if not is_stop_successful:
        raise Exception(f"Timeout during modelsim testing of design `{fuzzerstate.design_name}` for tuple ({fuzzerstate.memsize}, {fuzzerstate.design_name}, {fuzzerstate.randseed}, {fuzzerstate.nmax_bbs}, {fuzzerstate.authorize_privileges}).")
