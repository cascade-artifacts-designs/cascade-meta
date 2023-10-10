# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Plots the bars representing the security implications of bugs

from params.runparams import PATH_TO_FIGURES

import numpy as np
import os
from matplotlib import pyplot as plt
from collections import defaultdict

A = 'No check'
B = 'Spur. except.'
C = 'Info leakage'
D = 'DoS'
E = 'CF hijack'
F = 'DF violations'
G = 'Logic hiding'

X_TICK_NAMES = [
    A,
    B,
    C,
    D,
    E,
    F,
    G,
]

TYPE_MISSING_CHECKS = X_TICK_NAMES.index(A)
TYPE_SPURIOUS_EXCEPTS = X_TICK_NAMES.index(B)
TYPE_INFOLEAK = X_TICK_NAMES.index(C)
TYPE_DOS = X_TICK_NAMES.index(D)
TYPE_CF_HIJACK = X_TICK_NAMES.index(E)
TYPE_DF_INTEGRITY = X_TICK_NAMES.index(F)
TYPE_LOGIC_COMPRO = X_TICK_NAMES.index(G)

bug_classification = {
    TYPE_MISSING_CHECKS: set([
        'V10', 'V11', 'P5', 'K3'
    ]),
    TYPE_SPURIOUS_EXCEPTS: set([
        'V12', 'P2', 'P3', 'P4', 'P5', 'P6', 'K5', 'C8', 'C9'
    ]),
    TYPE_INFOLEAK: set([
        'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V15', 'K1', 'C1', 'B1',
        'C2', 'C3', 'C4', 'C5'
        'V10', 'V11'
    ]),
    TYPE_DOS: set([
        'V13', 'P1', 'K2'
    ]),
    TYPE_CF_HIJACK: set([
        'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'V5', 'V6'
    ]),
    TYPE_DF_INTEGRITY: set([
        'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8', 'V9', 'V15', 'K1', 'B1',
    ]),
    TYPE_LOGIC_COMPRO: set([
        'Y1'
    ]),
}

DESIGN_PRETTY_NAMES = [
    'PicoRV32',
    'Kronos',
    'VexRiscv',
    'CVA6',
    'BOOM',
    'Yosys',
]

DESIGN_COLORS = [
    'orange',
    'gray',
    'black',
    'red',
    'blue',
    'darkgreen',
]

def plot_security_implications():
    global X_TICK_NAMES
    in_dict = defaultdict(lambda: defaultdict(int))

    for implication_type in range(len(X_TICK_NAMES)):
        for bug_name in bug_classification[implication_type]:
            for design_name in DESIGN_PRETTY_NAMES:
                if bug_name[0] == design_name[0]:
                    in_dict[design_name][implication_type] += 1

    Ys = []
    for design_name in DESIGN_PRETTY_NAMES:
        Ys.append([in_dict[design_name][type_id] for type_id in range(len(X_TICK_NAMES))])

    X = np.arange(len(X_TICK_NAMES))

    # Sort the XTICK_NAMES an Ys in decreasing order Ys
    X_TICK_NAMES = [X_TICK_NAMES[i] for i in np.argsort(np.sum(Ys, axis=0))[::-1]]
    Ys = [np.array(Ys[i])[np.argsort(np.sum(Ys, axis=0))[::-1]] for i in range(len(Ys))]


    # Stacked bat chart with X and Ys
    fig = plt.figure(figsize=(5, 1.8))
    ax = fig.gca()

    width = 0.5

    for i, design_name in enumerate(DESIGN_PRETTY_NAMES):
        bars = ax.bar(X, Ys[i], bottom=np.sum(Ys[:i], axis=0), width=width, label=design_name, zorder=3, color=DESIGN_COLORS[i])
        for bar in bars:
            bar.set(edgecolor='black', linewidth=0.5)

    ax.bar_label(ax.containers[-1], padding=0)

    # Add angle to ticks
    for tick in ax.get_xticklabels():
        tick.set_rotation(20)

    ax.yaxis.grid()
    ax.set_ylim(0, 23)

    ax.set_ylabel("New bugs")

    ax.set_xticks(X)
    ax.set_xticklabels(X_TICK_NAMES)

    fig.legend(framealpha=1, ncol=2, bbox_to_anchor=(1.01, 1), loc='upper right')

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'security_implications.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)
