# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Compare the execution of two ELFs on spike

from common.designcfgs import get_design_march_flags_nocompressed, is_design_32bit
from common.spike import SPIKE_STARTADDR, FPREG_ABINAMES, get_spike_timeout_seconds
from params.runparams import DO_ASSERT, NO_REMOVE_TMPFILES, PATH_TO_TMP
from cascade.basicblock import gen_basicblocks
from cascade.cfinstructionclasses import JALInstruction, RegImmInstruction
from cascade.fuzzsim import SimulatorEnum, runtest_simulator
from cascade.spikeresolution import gen_elf_from_bbs, gen_regdump_reqs_reduced, gen_ctx_regdump_reqs, run_trace_regs_at_pc_locs, spike_resolution, run_trace_all_pcs
from cascade.contextreplay import SavedContext, gen_context_setter
from cascade.privilegestate import PrivilegeStateEnum
from cascade.reduce import _save_ctx_and_jump_to_pillar_specific_instr
from cascade.debug.debugreduce import _gen_spike_dbgcmd_file_for_full_trace, parse_full_trace, compare_parsed_traces, NUM_ELEMS_PER_INSTR, INTREG_ABI_NAMES

import random
import os
from pathlib import Path
import subprocess
from typing import List

def compare_executions(design_name: str, elf_path_1: str, elf_path_2: str, numinstrs: int):

    spike_out_1 = gen_full_trace_for_instrs(elf_path_1, get_design_march_flags_nocompressed(design_name), SPIKE_STARTADDR, numinstrs, not is_design_32bit(design_name))
    spike_out_2 = gen_full_trace_for_instrs(elf_path_2, get_design_march_flags_nocompressed(design_name), SPIKE_STARTADDR, numinstrs, not is_design_32bit(design_name))

    parsed_trace_1 = parse_full_trace(spike_out_1, not is_design_32bit(design_name))
    parsed_trace_2 = parse_full_trace(spike_out_2, not is_design_32bit(design_name))

    instr_addr_seq = list(map(lambda x: int(x[0], base=16) - SPIKE_STARTADDR, parsed_trace_1))

    # Compare the traces
    compare_parsed_traces(parsed_trace_1, parsed_trace_2, instr_addr_seq)

def gen_full_trace_for_instrs(elfpath: str, rvflags: str, startpc: int, numinstrs: int, is_64bit: bool):
    path_to_debug_file = _gen_spike_dbgcmd_file_for_full_trace(numinstrs, startpc, is_64bit)
    print(f"Generated debug file: {path_to_debug_file}")

    # Second, run the Spike command
    spike_shell_command = (
        "spike",
        "-d",
        f"--debug-cmd={path_to_debug_file}",
        f"--isa={rvflags}",
        f"--pc={SPIKE_STARTADDR}",
        elfpath
    )

    print(f"Running Spike command: {' '.join(filter(lambda s: '--debug-cmd' not in s, spike_shell_command))}  Debug file: {path_to_debug_file}")

    try:
        spike_out = subprocess.run(spike_shell_command, capture_output=True, text=True, timeout=get_spike_timeout_seconds()).stderr
    except Exception as e:
        raise Exception(f"Spike timeout in the debug script.\nCommand: {' '.join(spike_shell_command)}")

    spike_out = '\n'.join(filter(lambda s: ':' not in s and len(s) > 0, spike_out.split('\n')))
    num_elems_per_instr_according_to_bitwidth = NUM_ELEMS_PER_INSTR + int(not is_64bit)
    assert len(spike_out.split('\n')) == numinstrs * num_elems_per_instr_according_to_bitwidth, f"Unexpected number of lines in the full trace:" + str(len(spike_out.split('\n'))) + " -- expected: " + str(numinstrs * NUM_ELEMS_PER_INSTR)
    return spike_out
