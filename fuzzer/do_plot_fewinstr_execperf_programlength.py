# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script plots performance results for limited numbers of instructions.

import matplotlib.pyplot as plt
import numpy as np
import json
import locale
import os
from collections import defaultdict


DESIGN_PRETTY_NAMES = {
    'picorv32': 'PicoRV32',
    'kronos': 'Kronos',
    'vexriscv': 'VexRiscv',
    'cva6': 'CVA6',
    'boom': 'BOOM',
    'rocket': 'Rocket',
}

colors = [
    'black',
    (240/256, 0/256, 0/256),
    'brown',
    'orange',
    'green',
    'cyan',
]


# Display the performance plot
def plotperf():
    with open("perf_ubenchmark_fewinstructions.json", "r") as f:
        json_dict = json.load(f)

    nums_instrs = json_dict['nums_instructions']
    instance_gen_durations = json_dict['instance_gen_durations']
    run_durations = json_dict['run_durations']
    effective_num_instructions = json_dict['effective_num_instructions']

    design_names = list(instance_gen_durations.keys())

    # Correct parasite outliers who dont show the correct number of instructions.
    for design_name in design_names:
        for num_instrs_id, num_instrs in enumerate(nums_instrs):
            for effective_num_instruction_id in range(len(effective_num_instructions[design_name][str(num_instrs)])):
                if effective_num_instructions[design_name][str(num_instrs)][effective_num_instruction_id] in (2, 11, 101, 1001, 10001, 100001, 1000001):
                    effective_num_instructions[design_name][str(num_instrs)][effective_num_instruction_id] -= 1

    # Filter out minus-ones
    for design_name in design_names:
        for num_instrs_id, num_instrs in enumerate(nums_instrs):
            to_del_indices = []
            for effective_num_instruction_id in range(len(effective_num_instructions[design_name][str(num_instrs)])):
                if effective_num_instructions[design_name][str(num_instrs)][effective_num_instruction_id] == -1:
                    to_del_indices.append(effective_num_instruction_id)
            for to_del_index in reversed(to_del_indices):
                del effective_num_instructions[design_name][str(num_instrs)][to_del_index]
                del instance_gen_durations[design_name][str(num_instrs)][to_del_index]
                del run_durations[design_name][str(num_instrs)][to_del_index]

    # Scale
    SCALE_FACTOR = 1
    for design_name in design_names:
        for num_instrs_id, num_instrs in enumerate(nums_instrs):
            for run_id, run_duration in enumerate(run_durations[design_name][str(num_instrs)]):
                run_durations[design_name][str(num_instrs)][run_id] *= SCALE_FACTOR
            for run_id, instance_gen_duration in enumerate(instance_gen_durations[design_name][str(num_instrs)]):
                instance_gen_durations[design_name][str(num_instrs)][run_id] *= SCALE_FACTOR



    instrs_per_second_livegen_per_design = defaultdict(lambda: defaultdict(int)) # instrs_per_second_livegen_per_design[numinstrs_id][run_id] = instrs_per_second
    averages_livegen_per_design = []
    stddevs_livegen_per_design = []

    # Method 2
    gen_instrs_per_second = defaultdict(lambda: defaultdict(int))
    summed_effective_num_instructions = defaultdict(lambda: defaultdict(int))
    assert len(instrs_per_second_livegen_per_design) == 0, "Do not call both methods at the same time!"
    for design_name in design_names:
        for num_instrs_id, num_instrs in enumerate(nums_instrs):
            gen_instrs_per_second[design_name][str(num_instrs)] = sum(run_durations[design_name][str(num_instrs)])
            summed_effective_num_instructions[design_name][str(num_instrs)] = sum(effective_num_instructions[design_name][str(num_instrs)])

    # Compute the average throughput
    for design_name in design_names:
        for num_instrs_id, num_instrs in enumerate(nums_instrs):
            instrs_per_second_livegen_per_design[design_name][str(num_instrs)] = summed_effective_num_instructions[design_name][str(num_instrs)] / gen_instrs_per_second[design_name][str(num_instrs)]

    # Do a grouped bar plot.
    ips_not_transposed = [[instrs_per_second_livegen_per_design[design_name][str(num_instrs)] for num_instrs in nums_instrs] for design_name_id, design_name in enumerate(design_names)]

    x = np.arange(len(nums_instrs))  # the label locations
    bar_width = 1/(len(design_names)+2)  # the width of the bars

    fig, ax = plt.subplots(figsize=(6, 2))
    ax.grid(color='gray', zorder=0, axis='y', linewidth=0.4)

    for design_name_id, design_name in enumerate(design_names):
        ax.bar(x + bar_width/2 - (len(design_names) - 1)/2 * bar_width + design_name_id * bar_width, ips_not_transposed[design_name_id], bar_width, label=DESIGN_PRETTY_NAMES[design_name], edgecolor='k', color=colors[design_name_id], zorder=3)

    # Format the X labels with comma separators
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    nums_instrs_strs = list(map(lambda ni: locale.format_string("%d", ni, grouping=True), nums_instrs))

    # Make Y label logarithmic
    ax.set_yscale('log')
    ax.set_axisbelow(True)

    ax.set_ylabel('Exec. fuzz. instrs/s')
    ax.set_xlabel('Number of fuzzing instructions per program (program length)')
    ax.set_xticks(x)
    ax.set_xticklabels(nums_instrs_strs)
    fig.legend(ncol=2, framealpha=1, loc='upper left', bbox_to_anchor=(0.15, 0.91, 1.0, 0.1))
    plt.tight_layout()
    plt.savefig('execperf_programlength.png', dpi=300)

if __name__ == '__main__':
    plotperf()
else:
    print('This script is not meant to be imported')
    exit(1)
