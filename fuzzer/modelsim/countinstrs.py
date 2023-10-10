# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import DO_ASSERT, NO_REMOVE_TMPFILES, PATH_TO_TMP
from common.spike import SPIKE_STARTADDR, get_spike_timeout_seconds
import os
import subprocess
from pathlib import Path

# At the moment, this function is not used.
def countinstrs_cascade_fromelf(elf_id: int, elfpath: str, rvflags: str, final_addr: int) -> int:
    # Generate the spike debug commands file
    path_to_debug_file = _gen_spike_dbgcmd_file_for_count_instrs(identifier_str=f"cascade_countinstrs{elf_id}", startpc=SPIKE_STARTADDR, endpc=final_addr)

    # Second, run the Spike command
    spike_shell_command = (
        "spike",
        "-d",
        f"--debug-cmd={path_to_debug_file}",
        f"--isa={rvflags}",
        f"--pc={SPIKE_STARTADDR}",
        elfpath
    )

    try:
        spike_out = subprocess.run(spike_shell_command, capture_output=True, text=True, timeout=get_spike_timeout_seconds()).stderr
    except Exception as e:
        raise Exception(f"Spike timeout (A) for identifier str: difuzzrtl_patched{elf_id}. Command: {' '.join(filter(lambda s: '--debug-cmd' not in s, spike_shell_command))}  Debug file: {path_to_debug_file}")
    if not NO_REMOVE_TMPFILES:
        os.remove(path_to_debug_file)
        del path_to_debug_file

    return len(list(filter(lambda s: s.startswith('core   0: 0x'), spike_out.split('\n'))))


def countinstrs_cascade(elf_id: int) -> int:
    design_name = 'rocket'
    num_instrs_path = os.path.join(os.environ['CASCADE_PATH_TO_DIFUZZRTL_ELFS_FOR_MODELSIM'], f"{design_name}_{elf_id}_numinstrs.txt")
    with open(num_instrs_path, 'r') as file:
        content = file.read()
    return int(content, 16)

# Relies on pre-computed number of instructions
def countinstrs_difuzzrtl_nospike(elf_id: int) -> int:
    num_instrs_path = os.path.join(os.environ['CASCADE_PATH_TO_DIFUZZRTL_ELFS_FOR_MODELSIM'], f"id_{elf_id}_numinstrs.txt")
    with open(num_instrs_path, 'r') as file:
        content = file.read()
    return int(content, 16)

def countinstrs_difuzzrtl(path_to_patched_elf) -> int:
    rvflags = 'rv64g'

    assert path_to_patched_elf is not None, "path_to_patched_elf is None"
    assert 'patch' in path_to_patched_elf, "path_to_patched_elf is not a patched difuzzrtl elf"

    # Get the final pc
    final_addr_str = subprocess.check_output([f"nm {path_to_patched_elf} | grep write_tohost"], shell=True, text=True)
    final_addr = int(final_addr_str.split()[0], 16)

    # Generate the spike debug commands file
    path_to_debug_file = _gen_spike_dbgcmd_file_for_count_instrs(identifier_str=f"difuzzrtl_patched{hash(path_to_patched_elf)}", startpc=SPIKE_STARTADDR, endpc=final_addr)

    # Second, run the Spike command
    spike_shell_command = (
        "spike",
        "-d",
        f"--debug-cmd={path_to_debug_file}",
        f"--isa={rvflags}",
        f"--pc={SPIKE_STARTADDR}",
        path_to_patched_elf
    )

    try:
        spike_out = subprocess.run(spike_shell_command, capture_output=True, text=True, timeout=get_spike_timeout_seconds()).stderr
    except Exception as e:
        raise Exception(f"Spike timeout (A) for identifier str: {path_to_patched_elf}. Command: {' '.join(filter(lambda s: '--debug-cmd' not in s, spike_shell_command))}  Debug file: {path_to_debug_file}")
    if not NO_REMOVE_TMPFILES:
        os.remove(path_to_debug_file)
        del path_to_debug_file

    return len(list(filter(lambda s: s.startswith('core   0: 0x'), spike_out.split('\n'))))



def _gen_spike_dbgcmd_file_for_count_instrs(identifier_str: str, startpc: int, endpc: int):
    path_to_debug_file = os.path.join(PATH_TO_TMP, 'dbgcmds', f"cmds_count_instrs_{identifier_str}")
    # if not os.path.exists(path_to_debug_file):
    Path(os.path.dirname(path_to_debug_file)).mkdir(parents=True, exist_ok=True)
    spike_debug_commands = [
        f"until pc 0 0x{startpc:x}",
        f"untiln pc 0 0x{endpc:x}",
        f"q\n",
    ]
    spike_debug_commands_str = '\n'.join(spike_debug_commands)

    with open(path_to_debug_file, 'w') as f:
        f.write(spike_debug_commands_str)

    return path_to_debug_file
