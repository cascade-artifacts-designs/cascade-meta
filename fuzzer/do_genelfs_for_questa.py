# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script generates many Cascade ELFs.

from common.spike import calibrate_spikespeed
from analyzeelfs.genmanyelfs import gen_many_elfs
from modelsim.patchwritetohost import replace_write_to_host
from modelsim.countinstrs import countinstrs_difuzzrtl

import os
import subprocess
import multiprocessing as mp

# Change for your own setup using environment variables.
DIFUZZRTL_FUZZER_DIR_PATH = '/cascade-difuzzrtl/docker/shareddir/savedockerdifuzzrtl/Fuzzer'
SPIKE_PATH_FOR_DIFUZZRTL  = '/opt/riscv/bin/spike'
DIFUZZRTL_CASCADE_MOUNTDIR = '/cascade-mountdir'


def __patch_difuzzrtl_writetohost_worker(elfpath):
    # patched_elfpath is elfpath, where the base file name is prependend with 'patched_'
    patched_elfpath = os.path.join(os.path.dirname(elfpath), 'patched_' + os.path.basename(elfpath))
    return replace_write_to_host(elfpath, patched_elfpath)

def __countinstrs_difuzzrtl_worker(elfpath):
    # patched_elfpath is elfpath, where the base file name is prependend with 'patched_'
    patched_elfpath = os.path.join(os.path.dirname(elfpath), 'patched_' + os.path.basename(elfpath))
    numinstrs = countinstrs_difuzzrtl(patched_elfpath)

    # The output path is the elfpath where .elf is substituted with _numinstrs.txt
    retpath = os.path.join(os.path.dirname(elfpath), os.path.basename(elfpath).replace('.elf', '_numinstrs.txt'))
    with open(retpath, 'w') as f:
        f.write(hex(numinstrs))

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    num_cascade_elfs = 5000
    num_difuzzrtl_elfs = 25000

    # Get the environment variables if they are defined
    DIFUZZRTL_FUZZER_DIR_PATH_CANDIDATE = os.getenv('CASCADE_PATH_TO_DIFUZZRTL_FUZZER')
    if DIFUZZRTL_FUZZER_DIR_PATH_CANDIDATE is not None:
        DIFUZZRTL_FUZZER_DIR_PATH = DIFUZZRTL_FUZZER_DIR_PATH_CANDIDATE
    SPIKE_PATH_FOR_DIFUZZRTL_CANDIDATE = os.getenv('CASCADE_PATH_TO_SPIKE_FOR_DIFUZZRTL')
    if SPIKE_PATH_FOR_DIFUZZRTL_CANDIDATE is not None:
        SPIKE_PATH_FOR_DIFUZZRTL = SPIKE_PATH_FOR_DIFUZZRTL_CANDIDATE
    DIFUZZRTL_CASCADE_MOUNTDIR_CANDIDATE = os.getenv('CASCADE_PATH_TO_DIFUZZRTL_MOUNTDIR')
    if DIFUZZRTL_CASCADE_MOUNTDIR_CANDIDATE is not None:
        DIFUZZRTL_CASCADE_MOUNTDIR = DIFUZZRTL_CASCADE_MOUNTDIR_CANDIDATE

    target_dir = DIFUZZRTL_CASCADE_MOUNTDIR
    num_cores = int(os.getenv('CASCADE_JOBS', 160))

    assert os.path.isdir(target_dir), f"Target directory {target_dir} does not exist."

    # Generate the Cascade ELFs. This is typically fast because parallel.
    gen_many_elfs('rocket', num_cores, num_cascade_elfs, target_dir)
    
    # Generate the DifuzzRTL ELFs. This is typically slow because sequential.
    cmd_gen_difuzzrtl_elfs = f"cd {DIFUZZRTL_FUZZER_DIR_PATH} && make SIM_BUILD=builddir VFILE=RocketTile_state TOPLEVEL=RocketTile NUM_ITER={num_difuzzrtl_elfs} OUT=outdir IS_CASCADE=0 IS_RECORD=1 SPIKE={SPIKE_PATH_FOR_DIFUZZRTL}"
    print('Running command to generate DifuzzRTL ELFs: ' + cmd_gen_difuzzrtl_elfs)
    subprocess.run(cmd_gen_difuzzrtl_elfs, shell=True, check=True)

    # Now we must move the generated ELFs to the target_dir.
    cmd_move_difuzzrtl_elfs = f"mv {os.environ['CASCADE_PATH_TO_DIFUZZRTL_ELFS']}* {target_dir}"
    print('Running command to move the DifuzzRTL ELFs: ' + cmd_move_difuzzrtl_elfs)
    subprocess.run(cmd_move_difuzzrtl_elfs, shell=True, check=True)

    # Patch the DifuzzRTL ELFs
    # Get the ELFs
    difuzzrtl_elfpaths = []
    for elf in os.listdir(target_dir):
        if elf.startswith('id_'):
            difuzzrtl_elfpaths.append(os.path.join(target_dir, elf))
    # Patch each ELF
    with mp.Pool(num_cores) as pool:
        pool.map(__patch_difuzzrtl_writetohost_worker, difuzzrtl_elfpaths)
    # Count the number of instructions in each ELF
    calibrate_spikespeed()
    with mp.Pool(num_cores) as pool:
        pool.map(__countinstrs_difuzzrtl_worker, difuzzrtl_elfpaths)

    print('    Done generating the ELFs for Modelsim.')

else:
    raise Exception("This module must be at the toplevel.")
