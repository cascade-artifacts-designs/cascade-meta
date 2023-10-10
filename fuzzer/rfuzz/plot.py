# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import PATH_TO_FIGURES

import json
import os
import matplotlib.pyplot as plt
import numpy as np

# Number of coverage points per design. Manually collected from the instrumented designs.
NUM_COVERAGE_POINTS = {
    'picorv32': 172,
    'kronos': 178,
    'vexriscv': 634,
    'rocket': 2265,
    'boom': 7752,
}

DESIGN_PRETTY_NAMES = {
    'picorv32': 'PicoRV32',
    'kronos': 'Kronos',
    'vexriscv': 'VexRiscv',
    'rocket': 'Rocket',
    'boom': 'BOOM',
}

X_MAX_SECONDS = 100
X_SECONDS_AFTER_RFUZZ_END = None

assert X_SECONDS_AFTER_RFUZZ_END is None or X_MAX_SECONDS is None

# Display the perftuples as stacked bars
def plot_rfuzz(active_rfuzz_coverage_path_per_design: dict, passive_rfuzz_coverage_path_per_design: dict):

    design_names = list(NUM_COVERAGE_POINTS.keys())
    ignored_design_names = set()

    # Load the coverage data and durations
    coverage_durations_dicts = {}
    for design_name in design_names:
        json_path = active_rfuzz_coverage_path_per_design[design_name]
        if not os.path.exists(json_path):
            print(f"Warning: Skipping design {design_name}. File `{json_path}` does not exist.")
            ignored_design_names.add(design_name)
        else:
            with open(json_path, 'r') as f:
                coverage_durations_dicts[design_name] = json.load(f)

    # Load the coverage data and durations for cascade on rfuzz coverage
    coverage_durations_dicts_cascade = {}
    for design_name in design_names:
        json_path = passive_rfuzz_coverage_path_per_design[design_name]
        if not os.path.exists(json_path):
            print(f"Warning: Skipping design {design_name}. File `{json_path}` does not exist.")
            ignored_design_names.add(design_name)
        else:
            with open(json_path, 'r') as f:
                coverage_durations_dicts_cascade[design_name] = json.load(f)

    # Remove absent design names
    for design_name in ignored_design_names:
        design_names.remove(design_name)

    coverage_dict = {design_name: 100*np.array(coverage_durations_dicts[design_name]['coverage_sequence'])/NUM_COVERAGE_POINTS[design_name] for design_name in design_names}
    durations_seconds_dict = {design_name: np.array(coverage_durations_dicts[design_name]['durations']) for design_name in design_names}

    coverage_dict_cascade = {design_name: 100*np.array(coverage_durations_dicts_cascade[design_name]['coverage_sequence'])/NUM_COVERAGE_POINTS[design_name] for design_name in design_names}
    durations_seconds_dict_cascade = {design_name: np.array(coverage_durations_dicts_cascade[design_name]['durations']) for design_name in design_names}

    # Cumulative sum of durations
    durations_seconds_dict_cumsum_cascade = {design_name: [sum(durations_seconds_dict_cascade[design_name][0:id_in_tuple]) for id_in_tuple in range(len(durations_seconds_dict_cascade[design_name]))] for design_name in durations_seconds_dict.keys()}

    fig, axs = plt.subplots(len(design_names), 1, figsize=(7, 6), sharex=True)

    for i, ax in enumerate(axs):
        design_name = design_names[i]
        X = durations_seconds_dict[design_name]
        Y = np.array(coverage_dict[design_name])
        X_cascade = durations_seconds_dict_cumsum_cascade[design_name]
        Y_cascade = np.array(coverage_dict_cascade[design_name])

        # Truncate after X_SECONDS_AFTER_RFUZZ_END more
        if X_SECONDS_AFTER_RFUZZ_END is not None:
            for j, x in enumerate(X_cascade):
                if x > X[-1] + X_SECONDS_AFTER_RFUZZ_END:
                    X_cascade = X_cascade[:j+1]
                    Y_cascade = Y_cascade[:j+1]
                    break
        if X_MAX_SECONDS is not None:
            ax.set_xlim(0, X_MAX_SECONDS)
            for j, x in enumerate(X_cascade):
                if x > X_MAX_SECONDS:
                    X_cascade = X_cascade[:j+1]
                    Y_cascade = Y_cascade[:j+1]
                    break

        # Extend X and Y to the max of X_cascade
        X = np.append(X, X_cascade[-1])
        Y = np.append(Y, Y[-1])

        ax.plot(X_cascade, Y_cascade, zorder=3, color='k', label='Cascade')
        ax.plot(X, Y, zorder=3, color='red', label='RFUZZ')
        ax.set_title(f"{DESIGN_PRETTY_NAMES[design_name]} ({NUM_COVERAGE_POINTS[design_name]} coverage points)")
        ax.grid(zorder=0)

        ax.set_ylim(0, 100)

        ax.set_ylabel(' ')
        ax.legend(framealpha=1, loc='center right')
    # fig.y_label('Coverage points (%)')
    fig.text(0, 0.5, 'Coverage points (%)', va='center', rotation='vertical')

    ax.set_xlabel('Time (seconds)')
    fig.tight_layout()

    # Display the plot
    retpath = os.path.join(PATH_TO_FIGURES, 'rfuzz.png')
    print('Saving figure to', retpath)
    os.makedirs(os.path.dirname(retpath), exist_ok=True)
    plt.savefig(retpath, dpi=300)
