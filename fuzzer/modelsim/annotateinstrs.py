# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script colocates each DifuzzRTL ELF in the shared directory with its instruction count.
# It is meant to be executed in the Docker container and not locally.

from modelsim.countinstrs import _gen_spike_dbgcmd_file_for_count_instrs
from common.spike import SPIKE_STARTADDR, get_spike_timeout_seconds

import os
import subprocess

def countinstrs_difuzzrtl(elf_id: int) -> int:
    elfdir_path = '/cascade-mountdir'
    # Check that the shared directory exists
    assert os.path.isdir(elfdir_path), f"Shared directory `{elfdir_path}` does not exist."

    rvflags = 'rv64g'
    elfpath = os.path.join(elfdir_path, f"patched_id_{elf_id}.elf")

    assert elfpath is not None, "elfpath is None"
    assert 'patched' in elfpath, "elfpath is not a patched difuzzrtl elf"

    # Get the final pc
    final_addr_str = subprocess.check_output([f"nm {elfpath} | grep write_tohost"], shell=True, text=True)
    final_addr = int(final_addr_str.split()[0], 16)

    # Generate the spike debug commands file
    path_to_debug_file = _gen_spike_dbgcmd_file_for_count_instrs(identifier_str=f"difuzzrtl_patched{elf_id}", startpc=SPIKE_STARTADDR, endpc=final_addr)

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

    return len(list(filter(lambda s: s.startswith('core   0: 0x'), spike_out.split('\n'))))
