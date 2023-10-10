# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module is for debugging the context setter.

from common.designcfgs import get_design_march_flags_nocompressed, get_design_boot_addr
from common.spike import SPIKE_STARTADDR, FPREG_ABINAMES, get_spike_timeout_seconds
from params.runparams import NO_REMOVE_TMPFILES, PATH_TO_TMP
from cascade.basicblock import gen_basicblocks
from cascade.fuzzsim import SimulatorEnum
from cascade.spikeresolution import gen_elf_from_bbs
from cascade.reduce import _save_ctx_and_jump_to_pillar_specific_instr

import random
import os
from pathlib import Path
import subprocess
from typing import List

NUM_ELEMS_PER_INSTR = 76
INTREG_ABI_NAMES = ['zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 's0', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6']

ELEM_PRETTY = [
    'pc 0',
    f"{INTREG_ABI_NAMES[1]} (x1)",
    f"{INTREG_ABI_NAMES[2]} (x2)",
    f"{INTREG_ABI_NAMES[3]} (x3)",
    f"{INTREG_ABI_NAMES[4]} (x4)",
    f"{INTREG_ABI_NAMES[5]} (x5)",
    f"{INTREG_ABI_NAMES[6]} (x6)",
    f"{INTREG_ABI_NAMES[7]} (x7)",
    f"{INTREG_ABI_NAMES[8]} (x8)",
    f"{INTREG_ABI_NAMES[9]} (x9)",
    f"{INTREG_ABI_NAMES[10]} (x10)",
    f"{INTREG_ABI_NAMES[11]} (x11)",
    f"{INTREG_ABI_NAMES[12]} (x12)",
    f"{INTREG_ABI_NAMES[13]} (x13)",
    f"{INTREG_ABI_NAMES[14]} (x14)",
    f"{INTREG_ABI_NAMES[15]} (x15)",
    f"{INTREG_ABI_NAMES[16]} (x16)",
    f"{INTREG_ABI_NAMES[17]} (x17)",
    f"{INTREG_ABI_NAMES[18]} (x18)",
    f"{INTREG_ABI_NAMES[19]} (x19)",
    f"{INTREG_ABI_NAMES[20]} (x20)",
    f"{INTREG_ABI_NAMES[21]} (x21)",
    f"{INTREG_ABI_NAMES[22]} (x22)",
    f"{INTREG_ABI_NAMES[23]} (x23)",
    f"{INTREG_ABI_NAMES[24]} (x24)",
    f"{INTREG_ABI_NAMES[25]} (x25)",
    f"{INTREG_ABI_NAMES[26]} (x26)",
    f"{INTREG_ABI_NAMES[27]} (x27)",
    f"{INTREG_ABI_NAMES[28]} (x28)",
    f"{INTREG_ABI_NAMES[29]} (x29)",
    f"{INTREG_ABI_NAMES[30]} (x30)",
    f"{INTREG_ABI_NAMES[31]} (x31)",
    'freg 0',
    'freg 1',
    'freg 2',
    'freg 3',
    'freg 4',
    'freg 5',
    'freg 6',
    'freg 7',
    'freg 8',
    'freg 9',
    'freg 10',
    'freg 11',
    'freg 12',
    'freg 13',
    'freg 14',
    'freg 15',
    'freg 16',
    'freg 17',
    'freg 18',
    'freg 19',
    'freg 20',
    'freg 21',
    'freg 22',
    'freg 23',
    'freg 24',
    'freg 25',
    'freg 26',
    'freg 27',
    'freg 28',
    'freg 29',
    'freg 30',
    'freg 31',
    'fcsr',
    'mepc',
    'sepc',
    'mcause',
    'scause',
    'mscratch',
    'sscratch',
    'mtvec',
    'stvec',
    'medeleg',
    'mstatus',
    'minstret',
    'minstreth',
]

FROM_FILE = False
REDUCTION_SIMULATOR = SimulatorEnum.VERILATOR
NOPIZE_SANDWICH_INSTRUCTIONS = False # Not fully implemented & tested, hence do not yet set to True
FLATTEN_SANDWICH_INSTRUCTIONS = False # Not fully implemented & tested, hence do not yet set to True

def _gen_spike_dbgcmd_file_for_full_trace(numinstrs: int, startpc: int, is_64bit: bool):
    assert startpc >= SPIKE_STARTADDR
    path_to_debug_file = os.path.join(PATH_TO_TMP, 'dbgcmds', f"cmds_fulltrace{startpc:x}_{numinstrs}.txt")
    Path(os.path.dirname(path_to_debug_file)).mkdir(parents=True, exist_ok=True)
    spike_debug_commands = [
        f"until pc 0 0x{startpc:x}"
    ]
    for _ in range(numinstrs):
        curr_size = len(spike_debug_commands)
        spike_debug_commands.append('pc 0')
        spike_debug_commands.append('reg 0 1')
        spike_debug_commands.append('reg 0 2')
        spike_debug_commands.append('reg 0 3')
        spike_debug_commands.append('reg 0 4')
        spike_debug_commands.append('reg 0 5')
        spike_debug_commands.append('reg 0 6')
        spike_debug_commands.append('reg 0 7')
        spike_debug_commands.append('reg 0 8')
        spike_debug_commands.append('reg 0 9')
        spike_debug_commands.append('reg 0 10')
        spike_debug_commands.append('reg 0 11')
        spike_debug_commands.append('reg 0 12')
        spike_debug_commands.append('reg 0 13')
        spike_debug_commands.append('reg 0 14')
        spike_debug_commands.append('reg 0 15')
        spike_debug_commands.append('reg 0 16')
        spike_debug_commands.append('reg 0 17')
        spike_debug_commands.append('reg 0 18')
        spike_debug_commands.append('reg 0 19')
        spike_debug_commands.append('reg 0 20')
        spike_debug_commands.append('reg 0 21')
        spike_debug_commands.append('reg 0 22')
        spike_debug_commands.append('reg 0 23')
        spike_debug_commands.append('reg 0 24')
        spike_debug_commands.append('reg 0 25')
        spike_debug_commands.append('reg 0 26')
        spike_debug_commands.append('reg 0 27')
        spike_debug_commands.append('reg 0 28')
        spike_debug_commands.append('reg 0 29')
        spike_debug_commands.append('reg 0 30')
        spike_debug_commands.append('reg 0 31')

        for fp_reg_id in range(32):
            spike_debug_commands.append(f"freg 0 {FPREG_ABINAMES[fp_reg_id]}")

        spike_debug_commands.append('reg 0 fcsr')
        spike_debug_commands.append('reg 0 mepc')
        spike_debug_commands.append('reg 0 sepc')
        spike_debug_commands.append('reg 0 mcause')
        spike_debug_commands.append('reg 0 scause')
        spike_debug_commands.append('reg 0 mscratch')
        spike_debug_commands.append('reg 0 sscratch')
        spike_debug_commands.append('reg 0 mtvec')
        spike_debug_commands.append('reg 0 stvec')
        spike_debug_commands.append('reg 0 medeleg')
        spike_debug_commands.append('reg 0 mstatus')
        spike_debug_commands.append('reg 0 minstret')
        if not is_64bit:
            spike_debug_commands.append('reg 0 minstreth')

        num_elems_per_instr_according_to_bitwidth = NUM_ELEMS_PER_INSTR + int(not is_64bit)
        assert len(spike_debug_commands) == curr_size + num_elems_per_instr_according_to_bitwidth, f"len(spike_debug_commands)={len(spike_debug_commands)}, curr_size={curr_size}"

        spike_debug_commands.append('r 1')

    spike_debug_commands.append('q\n')

    assert len(spike_debug_commands) == 1 + numinstrs * (num_elems_per_instr_according_to_bitwidth + 1) + 1, f"len(spike_debug_commands)={len(spike_debug_commands)}, expected {numinstrs * (NUM_ELEMS_PER_INSTR + 1) + 1} , numinstrs={numinstrs}"
    spike_debug_commands_str = '\n'.join(spike_debug_commands)

    with open(path_to_debug_file, 'w') as f:
        f.write(spike_debug_commands_str)

    return path_to_debug_file

def gen_full_trace(elfpath: str, rvflags: str, startpc: int, numinstrs: int, is_64bit: bool):
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

def parse_full_trace(spike_out: str, is_64bit: bool):
    ret = []
    spike_out_splitted = spike_out.split('\n')
    num_elems_per_instr_according_to_bitwidth = NUM_ELEMS_PER_INSTR + int(not is_64bit)
    assert len(spike_out_splitted) % num_elems_per_instr_according_to_bitwidth == 0, f"Unexpected number of lines in the full trace:" + str(len(spike_out_splitted)) + " -- modulo: " + str(len(spike_out_splitted) % num_elems_per_instr_according_to_bitwidth)
    num_instrs = len(spike_out_splitted) // num_elems_per_instr_according_to_bitwidth
    for instr_id in range(num_instrs):
        ret.append([])
        entry_start = instr_id * num_elems_per_instr_according_to_bitwidth
        for elem_id in range(num_elems_per_instr_according_to_bitwidth):
            ret[instr_id].append(spike_out_splitted[entry_start + elem_id])
    return ret

def compare_parsed_traces(expected_trace: List[List[str]], actual_trace: List[List[str]], instr_addrs):
    num_matches = 0
    num_mismatches = 0
    for instr_id in range(len(expected_trace)):
        for elem_id in range(len(expected_trace[instr_id])):
            if expected_trace[instr_id][elem_id] != actual_trace[instr_id][elem_id]:
                print(f"Instr {instr_id} {hex(SPIKE_STARTADDR+instr_addrs[instr_id])} , elem id `{ELEM_PRETTY[elem_id]}`: Unexpected value in the full trace. Expected: {expected_trace[instr_id][elem_id]} -- Actual: {actual_trace[instr_id][elem_id]}")
                num_mismatches += 1
            else:
                num_matches += 1
    print(f"Matches: {num_matches}/{num_matches + num_mismatches} -- {num_matches / (num_matches + num_mismatches) * 100}%")

def debug_top(memsize: int, design_name: str, randseed: int, nmax_bbs: int, authorize_privileges: bool, start_bb: int, start_instr: int, end_addr: int):
    from cascade.fuzzerstate import FuzzerState
    random.seed(randseed)

    # Generate the full program
    fuzzerstate = FuzzerState(get_design_boot_addr(design_name), design_name, memsize, randseed, nmax_bbs, authorize_privileges)
    gen_basicblocks(fuzzerstate)
    # end_addr = fuzzerstate.final_bb_base_addr

    # Get the number of interesting instructions
    is_critical_section = False
    num_interesting_instrs = 0
    instr_addrs = []
    instr_addrs_rev_dict = dict()

    for bb_id, bb in enumerate(fuzzerstate.instr_objs_seq):
        if bb_id != start_bb and not is_critical_section:
            continue
        for bb_instr_id, bb_instr in enumerate(bb):
            if bb_id == start_bb and bb_instr_id == start_instr:
                is_critical_section = True
            curr_addr = fuzzerstate.bb_start_addr_seq[bb_id] + bb_instr_id * 4 # NO_COMPRESSED
            print(f"Curr addr: {hex(curr_addr)}, end addr: {hex(end_addr)}, bb id: {bb_id}, instr id: {bb_instr_id}, is_critical_section: {is_critical_section}")
            if is_critical_section:
                instr_addrs_rev_dict[curr_addr] = num_interesting_instrs
                num_interesting_instrs += 1
                instr_addrs.append(curr_addr)
            if curr_addr == end_addr:
                print(f"End addr reached: {hex(end_addr)}")
                is_critical_section = False
                break
    assert not is_critical_section, "Critical section not closed"

    print(f"Number of interesting instructions: {num_interesting_instrs}")

    spikecheck_out = spike_resolution_debug(fuzzerstate, True, start_bb, start_instr, num_interesting_instrs)

    spikecheck_trace = parse_full_trace(spikecheck_out, fuzzerstate.is_design_64bit)

    ###
    # Get the expected values from the full program
    ###

    if not FROM_FILE:
        expected_rtl_elfpath = gen_elf_from_bbs(fuzzerstate, False, 'debugctx_expected', fuzzerstate.instance_to_str(), fuzzerstate.design_base_addr)
        start_addr = fuzzerstate.bb_start_addr_seq[start_bb] + 4*start_instr # NO_COMPRESSED
        expected_spike_out = gen_full_trace(expected_rtl_elfpath, get_design_march_flags_nocompressed(design_name), start_addr + SPIKE_STARTADDR, num_interesting_instrs, fuzzerstate.is_design_64bit)
        with open(os.path.join(PATH_TO_TMP, 'spike_expected_trace.txt'), 'w') as f:
            f.write(expected_spike_out)
            print(f"Expected trace written to {os.path.join(PATH_TO_TMP, 'spike_expected_trace.txt')}")
    else:
        with open(os.path.join(PATH_TO_TMP, 'spike_expected_trace.txt'), 'r') as f:
            expected_spike_out = f.read()

    expected_trace = parse_full_trace(expected_spike_out, fuzzerstate.is_design_64bit)

    print(f"Expected trace parsed")

    ###
    # Get the values from the reduced program
    ###

    if not FROM_FILE:
        reduced_fuzzerstate = _save_ctx_and_jump_to_pillar_specific_instr(fuzzerstate, start_bb, start_instr)
        reduced_rtl_elfpath = gen_elf_from_bbs(fuzzerstate, False, 'debugctx_reduced', reduced_fuzzerstate.instance_to_str(), reduced_fuzzerstate.design_base_addr)
        reduced_spike_out = gen_full_trace(reduced_rtl_elfpath, get_design_march_flags_nocompressed(design_name), start_addr + SPIKE_STARTADDR, num_interesting_instrs, fuzzerstate.is_design_64bit)
        with open(os.path.join(PATH_TO_TMP, 'spike_reduced_trace.txt'), 'w') as f:
            f.write(reduced_spike_out)
            print(f"Expected trace written to {os.path.join(PATH_TO_TMP, 'spike_reduced_trace.txt')}")
    else:
        with open(os.path.join(PATH_TO_TMP, 'spike_reduced_trace.txt'), 'r') as f:
            expected_spike_out = f.read()

    reduced_trace = parse_full_trace(reduced_spike_out, fuzzerstate.is_design_64bit)

    # Compare the traces
    # compare_parsed_traces(expected_trace, spikecheck_trace)
    compare_parsed_traces(expected_trace, reduced_trace, instr_addrs)


# Takes a fuzzerstate after its basic blocks were generated.
# Does the address resolution in place in the fuzzerstate, and returns the list of expected register values.
# @return a list of fuzzerstate.num_pickable_regs
# 1 (does not contain the zero register)
def spike_resolution_debug(fuzzerstate, check_pc_spike_again: bool, start_bb: int, start_instr: int, num_interesting_instrs: int):
    from cascade.spikeresolution import _transmit_addrs_to_producers_for_spike_resolution, gen_regdump_reqs, _feed_regdump_to_instrs, _check_pc_trace_from_spike
    from cascade.util import IntRegIndivState
    import itertools
    
    design_name = fuzzerstate.design_name
    _transmit_addrs_to_producers_for_spike_resolution(fuzzerstate)
    # print('start addrs', list(map(hex, fuzzerstate.bb_start_addr_seq)))
    spike_resolution_elfpath = gen_elf_from_bbs(fuzzerstate, True, 'spikeresol', fuzzerstate.instance_to_str(), SPIKE_STARTADDR)
    # print('Spike resolution elfpath:', spike_resolution_elfpath)
    regdump_reqs = gen_regdump_reqs(fuzzerstate)
    flat_instr_objs = list(itertools.chain.from_iterable(fuzzerstate.instr_objs_seq))
    # len(flat_instr_objs)+1: the +1 is to reach the final basic block and thereby overwrite the potential destination register of a jal/jalr
    regvals, (finalintregvals_spikeresol, finalfpuregvals_spikeresol) = run_trace_regs_at_pc_locs(fuzzerstate.instance_to_str(), spike_resolution_elfpath, get_design_march_flags_nocompressed(design_name), SPIKE_STARTADDR, regdump_reqs, True, fuzzerstate.final_bb_base_addr+SPIKE_STARTADDR, fuzzerstate.num_pickable_floating_regs if fuzzerstate.design_has_fpu else 0, fuzzerstate.design_has_fpud)
    if not NO_REMOVE_TMPFILES:
        os.remove(spike_resolution_elfpath)
        del spike_resolution_elfpath

    # IMPORTANT: We reset the randomness here to have deterministic branch instructions.
    # (Rare) example where it matters: assume we need to pop the last bb, say with id 20. Then we could have a bug with request size 19 but not with request size 20, or vice versa.
    random.seed(fuzzerstate.randseed) # We could as well seed with zero here.
    _feed_regdump_to_instrs(fuzzerstate, regvals)

    # Use spike to check the rtl elf if requested
    assert check_pc_spike_again
    if check_pc_spike_again:
        # Generate the RTL ELF, but located for spike at SPIKE_STARTADDR
        rtl_spike_elfpath = gen_elf_from_bbs(fuzzerstate, False, 'spikedoublecheck', fuzzerstate.instance_to_str(), SPIKE_STARTADDR)
        if NO_REMOVE_TMPFILES:
            print('rtl_spike_elfpath:', rtl_spike_elfpath)
        
        start_addr = fuzzerstate.bb_start_addr_seq[start_bb] + 4*start_instr # NO_COMPRESSED
        spikecheck_out = gen_full_trace(rtl_spike_elfpath, get_design_march_flags_nocompressed(design_name), start_addr + SPIKE_STARTADDR, num_interesting_instrs, fuzzerstate.is_design_64bit)

        return spikecheck_out
