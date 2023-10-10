# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import os
from params.runparams import DO_ASSERT

# Replace the environment with new values.
# sram_taintfile: path relative to cascadedir
# bootrom_elf: path relative to cascadedir
def setup_sim_env(sram_elf, bootrom_elf, tracefile, simtime, cascadedir, coveragefile, verbose: bool = True):
    if DO_ASSERT:
        assert isinstance(sram_elf, str)
        assert isinstance(bootrom_elf, str) or bootrom_elf is None
        assert isinstance(tracefile, str) or tracefile is None
        assert isinstance(simtime, int)
        assert isinstance(coveragefile, str) or coveragefile is None

    # Make all paths absolute.
    if bootrom_elf:
        bootrom_elf = os.path.join(cascadedir, bootrom_elf)

    # Copy the OS environment.
    my_env = os.environ.copy()

    # Replace the environment simlen.
    my_env["SIMLEN"] = str(simtime)

    if tracefile:
        my_env["TRACEFILE"] = tracefile
    else:
        my_env.pop("TRACEFILE", None) # Remove TRACEFILE if it exists

    if coveragefile:
        my_env["COVERAGEFILE"] = coveragefile
        # For Modelsim
        my_env["MODELSIM_VLOG_COVERFLAG"] = '+cover'
        my_env["MODELSIM_VSIM_COVERFLAG"] = '-coverage'
        my_env["MODELSIM_VSIM_COVERPATH"] = coveragefile
    else:
        my_env.pop("COVERAGEFILE", None)
        # For Modelsim
        my_env.pop("MODELSIM_VLOG_COVERFLAG", None)
        my_env.pop("MODELSIM_VSIM_COVERFLAG", None)
        my_env.pop("MODELSIM_VSIM_COVERPATH", None)

    # Replace the environment ELF paths.
    my_env["SIMSRAMELF"] = sram_elf
    if bootrom_elf:
        my_env["SIMROMELF"] = bootrom_elf
    else:
        my_env["SIMROMELF"] = sram_elf

    if verbose:
        print('setting SIMSRAMELF to {}'.format(my_env["SIMSRAMELF"]))
        print('setting SIMROMELF to {}'.format(my_env["SIMROMELF"]))
    return my_env
