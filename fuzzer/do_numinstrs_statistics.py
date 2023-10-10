# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script generates some statistics on the number of instructions per test case.

from cascade.fuzzfromdescriptor import gen_new_test_instance, fuzz_single_from_descriptor
from cascade.basicblock import gen_basicblocks
from cascade.fuzzerstate import FuzzerState
from common.designcfgs import get_design_boot_addr

import numpy as np
import os
import sys
import random
import json
import multiprocessing as mp
from common.profiledesign import profile_get_medeleg_mask
from common.spike import calibrate_spikespeed

# sys.argv[1]: num samples
# sys.argv[2]: num cores

design_name = "rocket"

def gen_numinstrs_single_elf(randseed: int):
    memsize, _, _, num_bbs, authorize_privileges = gen_new_test_instance(design_name, randseed, True)

    random.seed(randseed)
    fuzzerstate = FuzzerState(get_design_boot_addr(design_name), design_name, memsize, randseed, num_bbs, authorize_privileges, None, False)
    gen_basicblocks(fuzzerstate)
    num_fuzzing_instrs = sum([len(bb) for bb in fuzzerstate.instr_objs_seq])
    return num_fuzzing_instrs

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    num_samples = int(sys.argv[1])
    num_workers = int(sys.argv[2])

    ##############
    # Gen the data
    ##############

    # # Numbers from 1 to num_samples
    # random_seeds = [i for i in range(num_samples)]

    # calibrate_spikespeed()
    # profile_get_medeleg_mask(design_name)

    # with mp.Pool(processes=num_workers) as pool:
    #     all_numinstrs = pool.map(gen_numinstrs_single_elf, random_seeds)

    # json.dump(all_numinstrs, open("numinstrs.json", "w"))

    ##############
    # Plot the data
    ##############
    # Plot as a histogram

    all_numinstrs = json.load(open("numinstrs.json", "r"))
    print("Num programs:", len(all_numinstrs))

    import matplotlib.pyplot as plt
    BINS = 100

    hist, bin_edges = np.histogram(all_numinstrs, bins=BINS)

    # Define the colors you want to use for the bars alternately
    dark_gray = (100/255, 100/255, 100/255)
    colors = ['black', dark_gray]

    # Create a figure and axis
    fig, ax = plt.subplots(figsize=(6, 1.4))

    # Create the histogram bars with alternating colors
    for i in range(BINS):
        ax.bar(bin_edges[i], hist[i], width=bin_edges[i+1] - bin_edges[i], color=colors[i % len(colors)], edgecolor='black', linewidth=0.5, zorder=3)

    ax.yaxis.grid(which='major', color='gray', zorder=1, linewidth=0.4)
    ax.set_axisbelow(True)

    plt.xlabel('Number of fuzzing instructions')
    plt.ylabel('Frequency')
    plt.tight_layout()

    # Create the "out" dir if it does not exist
    plt.savefig('numinstrs.png', dpi=300)


else:
    raise Exception("This module must be at the toplevel.")
