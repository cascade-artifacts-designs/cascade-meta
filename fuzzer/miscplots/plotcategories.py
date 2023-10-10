# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the bars representing bugs per category

from params.runparams import PATH_TO_FIGURES

import numpy as np
import os
from matplotlib import pyplot as plt
from collections import defaultdict

X_TICK_NAMES = [
    'Exceptions',
    'Uarchvals',
    'Archvals',
    'Archflags',
    'Hangs',
    'Perfcnt',
]

TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS = X_TICK_NAMES.index('Exceptions')
TYPE_UARCH_VALS = X_TICK_NAMES.index('Uarchvals')
TYPE_ARCH_FPU_VALS = X_TICK_NAMES.index('Archvals')
TYPE_ARCH_FPU_FLAGS = X_TICK_NAMES.index('Archflags')
TYPE_HANGS = X_TICK_NAMES.index('Hangs')
TYPE_PERF_CNT = X_TICK_NAMES.index('Perfcnt')

bug_classification = {
    'V1': TYPE_UARCH_VALS,
    'V2': TYPE_UARCH_VALS,
    'V3': TYPE_UARCH_VALS,
    'V4': TYPE_UARCH_VALS,
    'V5': TYPE_UARCH_VALS,
    'V6': TYPE_UARCH_VALS,
    'V7': TYPE_UARCH_VALS,
    'V8': TYPE_UARCH_VALS,
    'V9': TYPE_UARCH_VALS,
    'V10': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'V11': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'V12': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'V13': TYPE_HANGS,
    'V14': TYPE_PERF_CNT,
    'V15': TYPE_UARCH_VALS,

    'P1': TYPE_HANGS,
    'P2': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'P3': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'P4': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'P5': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'P6': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,

    'K1': TYPE_UARCH_VALS,
    'K2': TYPE_HANGS,
    'K3': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'K4': TYPE_PERF_CNT,
    'K5': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,

    'C1': TYPE_ARCH_FPU_VALS,
    'C2': TYPE_ARCH_FPU_FLAGS,
    'C3': TYPE_ARCH_FPU_FLAGS,
    'C4': TYPE_ARCH_FPU_FLAGS,
    'C5': TYPE_ARCH_FPU_FLAGS,
    'C6': TYPE_ARCH_FPU_VALS,
    'C7': TYPE_ARCH_FPU_VALS,
    'C8': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,
    'C9': TYPE_SPURIOUS_OR_MISSING_EXCEPTIONS,

    'B1': TYPE_ARCH_FPU_VALS,
    'B2': TYPE_PERF_CNT,
}

DESIGN_PRETTY_NAMES = [
    'PicoRV32',
    'Kronos',
    'VexRiscv',
    'CVA6',
    'BOOM',
    # 'Rocket',
]

DESIGN_COLORS = [
    'orange',
    'gray',
    'black',
    'red',
    'blue',
    # 'purple',
]

def plot_bugtypes_bars():
    in_dict = defaultdict(lambda: defaultdict(int))

    # Just some assertions
    for bugtype_key, bugtype_value in bug_classification.items():
        assert bugtype_value < len(X_TICK_NAMES)

    # Get the stats
    for bugtype_key, bugtype_value in bug_classification.items():
        for design_name in DESIGN_PRETTY_NAMES:
            if bugtype_key[0] == design_name[0]:
                in_dict[design_name][bugtype_value] += 1

    Ys = []
    for design_name in DESIGN_PRETTY_NAMES:
        Ys.append([in_dict[design_name][type_id] for type_id in range(len(X_TICK_NAMES))])

    X = np.arange(len(X_TICK_NAMES))

    # Stacked bat chart with X and Ys
    fig = plt.figure(figsize=(6, 2.2))
    ax = fig.gca()

    width = 0.5

    for i, design_name in enumerate(DESIGN_PRETTY_NAMES):
        bars = ax.bar(X, Ys[i], bottom=np.sum(Ys[:i], axis=0), width=width, label=design_name, zorder=3, color=DESIGN_COLORS[i])
        for bar in bars:
            bar.set(edgecolor='black', linewidth=0.5)

    ax.bar_label(ax.containers[-1], padding=-1)

    ax.yaxis.grid()
    ax.set_ylim(0, 13)

    ax.set_ylabel("New bugs")

    ax.set_xticks(X)
    ax.set_xticklabels(X_TICK_NAMES)

    fig.legend(framealpha=1)

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'bug_categories.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)
