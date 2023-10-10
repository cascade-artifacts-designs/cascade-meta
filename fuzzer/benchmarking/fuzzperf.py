# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module measures the program construction performance.

from params.runparams import PATH_TO_TMP
from common.spike import calibrate_spikespeed
from common.profiledesign import profile_get_medeleg_mask
from cascade.fuzzfromdescriptor import run_rtl
from top.fuzzdesign import gen_new_test_instance

import multiprocessing as mp
import json
import os

def _time_measurement_worker(design_name: str, worker_randseed: int, expected_run_duration_seconds_per_worker: float):
    assert expected_run_duration_seconds_per_worker > 0
    assert worker_randseed >= 0

    cumul_time_seconds_spent_in_gen_bbs = 0
    cumul_time_seconds_spent_in_spike_resol = 0
    cumul_time_seconds_spent_in_gen_elf = 0
    cumul_time_seconds_spent_in_rtl_sim = 0

    round_id = 0
    while cumul_time_seconds_spent_in_gen_bbs + cumul_time_seconds_spent_in_spike_resol + cumul_time_seconds_spent_in_gen_elf + cumul_time_seconds_spent_in_rtl_sim < expected_run_duration_seconds_per_worker:
        curr_seed = 1000000 * worker_randseed + round_id
        memsize, _, _, nmax_bbs, authorize_privileges = gen_new_test_instance(design_name, curr_seed, True)

        try:
            time_seconds_spent_in_gen_bbs, time_seconds_spent_in_spike_resol, time_seconds_spent_in_gen_elf, time_seconds_spent_in_rtl_sim = run_rtl(memsize, design_name, curr_seed, nmax_bbs, authorize_privileges, False)
        except Exception as e:
            print('Exception in time-measuring process with design', design_name, 'randseed', worker_randseed, 'and round id', round_id, ':', e)
            continue

        cumul_time_seconds_spent_in_gen_bbs += time_seconds_spent_in_gen_bbs
        cumul_time_seconds_spent_in_spike_resol += time_seconds_spent_in_spike_resol
        cumul_time_seconds_spent_in_gen_elf += time_seconds_spent_in_gen_elf
        cumul_time_seconds_spent_in_rtl_sim += time_seconds_spent_in_rtl_sim
        round_id += 1
        # print(cumul_time_seconds_spent_in_gen_bbs + cumul_time_seconds_spent_in_spike_resol + cumul_time_seconds_spent_in_gen_elf + cumul_time_seconds_spent_in_rtl_sim, '/', expected_run_duration_seconds_per_worker)
    return cumul_time_seconds_spent_in_gen_bbs, cumul_time_seconds_spent_in_spike_resol, cumul_time_seconds_spent_in_gen_elf, cumul_time_seconds_spent_in_rtl_sim


design_names_for_fuzzperf = [
    'kronos',
    'picorv32',
    'vexriscv',
    'rocket',
    'cva6',
    'boom',
]

# Each worker must reach the total desired duration divided by the number of workers.
def benchmark_collect_construction_performance(num_workers: int):
    assert num_workers > 0
    TOTAL_DURATION_PER_DESIGN_SECONDS = 24*60*60

    cumul_time_seconds_spent_in_gen_bbs = dict()
    cumul_time_seconds_spent_in_spike_resol = dict()
    cumul_time_seconds_spent_in_gen_elf = dict()
    cumul_time_seconds_spent_in_rtl_sim = dict()

    for design_name in design_names_for_fuzzperf:
        worker_instances = ((design_name, i, TOTAL_DURATION_PER_DESIGN_SECONDS/num_workers) for i in range(num_workers))

        calibrate_spikespeed()
        profile_get_medeleg_mask(design_name)

        print(f"Starting performance testing of `{design_name}` on {num_workers} processes.")

        with mp.Pool(num_workers) as p:
            results = p.starmap(_time_measurement_worker, worker_instances)

        cumul_time_seconds_spent_in_gen_bbs[design_name]     = sum(map(lambda s: s[0], results))
        cumul_time_seconds_spent_in_spike_resol[design_name] = sum(map(lambda s: s[1], results))
        cumul_time_seconds_spent_in_gen_elf[design_name]     = sum(map(lambda s: s[2], results))
        cumul_time_seconds_spent_in_rtl_sim[design_name]     = sum(map(lambda s: s[3], results))

    save_dict = {
        'cumul_time_seconds_spent_in_gen_bbs': cumul_time_seconds_spent_in_gen_bbs,
        'cumul_time_seconds_spent_in_spike_resol': cumul_time_seconds_spent_in_spike_resol,
        'cumul_time_seconds_spent_in_gen_elf': cumul_time_seconds_spent_in_gen_elf,
        'cumul_time_seconds_spent_in_rtl_sim': cumul_time_seconds_spent_in_rtl_sim
    }

    json.dump(save_dict, open(os.path.join(PATH_TO_TMP, 'fuzzperf.json'), 'w'))
    print('Saved performance results to', os.path.join(PATH_TO_TMP, 'fuzzperf.json'))

def plot_construction_performance():
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.rcParams['pdf.fonttype'] = 42
    matplotlib.rcParams['ps.fonttype'] = 42
    import numpy as np
    
    assert os.path.exists(os.path.join(PATH_TO_TMP, 'fuzzperf.json'))

    save_dict = json.load(open(os.path.join(PATH_TO_TMP, 'fuzzperf.json'), 'r'))

    cumul_time_seconds_spent_in_gen_bbs = save_dict['cumul_time_seconds_spent_in_gen_bbs']
    cumul_time_seconds_spent_in_spike_resol = save_dict['cumul_time_seconds_spent_in_spike_resol']
    cumul_time_seconds_spent_in_gen_elf = save_dict['cumul_time_seconds_spent_in_gen_elf']
    cumul_time_seconds_spent_in_rtl_sim = save_dict['cumul_time_seconds_spent_in_rtl_sim']

    perftuples_dict = dict()
    for design_name in design_names_for_fuzzperf:
        perftuples_dict[design_name] = [
            cumul_time_seconds_spent_in_gen_bbs[design_name],
            cumul_time_seconds_spent_in_spike_resol[design_name],
            cumul_time_seconds_spent_in_gen_elf[design_name],
            cumul_time_seconds_spent_in_rtl_sim[design_name]
        ]

    legends = [
        'Interm. program construc.',
        'Asymmetric ISA pre-sim.',
        'Final ELF writing'
    ]

    perftuples_dict_normalized = {design_name: [100 * perftuple[id_in_tuple] / sum(perftuple) for id_in_tuple in range(len(perftuples_dict[design_name]))] for design_name, perftuple in perftuples_dict.items()}
    perftuples_transpose = [[perftuples_dict_normalized[design_name][id_in_tuple] for design_name in design_names_for_fuzzperf] for id_in_tuple in range(len(perftuples_dict_normalized[design_names_for_fuzzperf[0]]))]

    elem_id_labels = ['Intermediate program construction', 'ISS resolution', 'Final ELF writing']
    elem_id_colors = ['k', 'red', 'orange']

    width = 0.5
    bottom = np.zeros(len(design_names_for_fuzzperf))

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.grid(color='gray', zorder=0, axis='y', linewidth=0.4)
    ax.set_ylim(0, 100)

    for elem_id, elem_label in enumerate(elem_id_labels):
        # Set up the stacked bar chart
        bars = ax.bar(design_names_for_fuzzperf, perftuples_transpose[elem_id], width, bottom=bottom, color=elem_id_colors[elem_id], label=legends[elem_id], zorder=3)
        bottom += perftuples_transpose[elem_id]
        # Add edges to bars
        for bar in bars:
            bar.set(edgecolor='black', linewidth=0.5)

    ax.bar_label(ax.containers[-1], fmt="%.1f%%", padding=0)

    ax.set_ylabel('Time per step (%)')
    ax.legend(framealpha=1)

    # Display the plot
    ax.plot()
    
    print('Saving figure to', os.path.join(PATH_TO_TMP, 'fuzzperf.png'))
    plt.savefig(os.path.join(PATH_TO_TMP, 'fuzzperf.png'), dpi=300)
    plt.savefig(os.path.join(PATH_TO_TMP, 'fuzzperf.pdf'), dpi=300)
