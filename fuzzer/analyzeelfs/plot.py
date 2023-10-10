# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import PATH_TO_FIGURES

import json
import numpy as np
import os
from matplotlib import pyplot as plt

def plot_cascade_dependencies(json_path):
    in_dict = json.load(open(json_path, 'r'))
    instr_ages = in_dict['instr_ages']
    instr_ages_cfonly = in_dict['instr_ages_cfonly']

    # Remove the instructions that do not have input registers
    instr_ages = list(filter(lambda x: x is not None, instr_ages))
    instr_ages_cfonly = list(filter(lambda x: x is not None, instr_ages_cfonly))

    NUM_BINS = 100
    bin_width = max(instr_ages)/NUM_BINS

    X_MAX = 100

    # Bucket the values
    hist, bin_edges = np.histogram(instr_ages, bins=NUM_BINS, range=(0, X_MAX))
    hist_cfonly, bin_edges_cfonly = np.histogram(instr_ages_cfonly, bins=NUM_BINS, range=(0, X_MAX))

    # Normalize the counts
    normalized_hist = []
    normalized_hist_cfonly = []
    for i in range(len(hist)):
        normalized_hist.append(100 * hist[i] / len(instr_ages))
        normalized_hist_cfonly.append(100 * hist_cfonly[i] / len(instr_ages)) # We knowignly normalize by the total number of instructions

    average_age = sum(instr_ages) / len(instr_ages)
    median_age = np.median(instr_ages)

    print(f"Average age: {average_age}")
    print(f"Median age: {median_age}")

    plt.clf()
    fig = plt.figure(figsize=(5, 1.5))
    ax = fig.gca()

    bin_width = max(instr_ages)/len(bin_edges[:-1])
    ax.bar(bin_edges[:-1], normalized_hist, width=bin_width, color='k', zorder=3)
    ax.bar(bin_edges[:-1], normalized_hist_cfonly, width=bin_width, color='orange', zorder=3)

    ax.yaxis.grid(which='major')

    ax.set_xlabel("Length of the dependency chain")
    ax.set_ylabel("Test cases (%)")

    tick_orig = np.arange(0, max(instr_ages), 5)
    tick_positions = list(map(lambda x: x - bin_width/2, tick_orig))
    # Only take every 10th tick
    tick_positions = tick_positions[::10]
    ax.set_xticklabels(tick_orig[::10])
    ax.set_xticks(tick_positions)

    ax.set_xlim(-2, bin_edges[-1] + 2)

    ax.axvline(average_age - bin_width/2, color='r', linestyle='--', label=f"Average dependencies ({average_age:.1f})")
    ax.axvline(median_age - bin_width/2, color='blue', linestyle='-.', label=f"Median dependencies ({median_age:.1f})")

    fig.legend(framealpha=1, loc='upper center')

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'cascade_dependencies.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)


def plot_cascade_prevalences(json_path):
    # Load prevalences.json
    instr_prevalences = json.load(open(json_path, 'r'))

    # Remove the instructions that do not have input registers
    instr_prevalences = list(filter(lambda x: x is not None, instr_prevalences))

    # Bucket the values
    hist, bin_edges = np.histogram(instr_prevalences, bins=100, range=(0, 1))

    # Trim the trailing zeros
    num_trailing_zeros = 0
    for i in range(len(hist) - 1, -1, -1):
        if hist[i] == 0:
            num_trailing_zeros += 1
        else:
            break
    if num_trailing_zeros:
        hist = hist[:-num_trailing_zeros]
        bin_edges = bin_edges[:-num_trailing_zeros]

    # Normalize the counts
    normalized_hist = {}
    for i in range(len(hist)):
        normalized_hist[i] = 100 * hist[i] / len(instr_prevalences)

    average_density = sum(instr_prevalences) / len(instr_prevalences)
    median_density = np.median(instr_prevalences)

    plt.clf()
    fig = plt.figure(figsize=(5, 1.5))
    ax = fig.gca()

    ax.bar(bin_edges[:-1], normalized_hist.values(), width=0.01, color='k', zorder=3)

    ax.yaxis.grid(which='major')

    ax.set_xlabel("Prevalence of fuzzing instructions (%)")
    ax.set_ylabel("Test cases (%)")

    tick_positions = list(map(lambda x: x - 0.005, list(bin_edges) + [0.4]))
    # Only take every 10th tick
    tick_positions = tick_positions[::10]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([f"{int(100*(x+0.005))}" for x in tick_positions])

    ax.set_xlim(-0.01, bin_edges[-1] + 0.01)

    ax.axvline(average_density - .005, color='r', linestyle='--', label=f"Average prevalence ({100*average_density:.1f}%)")
    ax.axvline(median_density - .005, color='blue', linestyle='-.', label=f"Median prevalence ({100*median_density:.1f}%)")

    fig.legend(framealpha=1, loc='upper center')

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'cascade_prevalences.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)



# DifuzzRTL

def plot_difuzzrtl_instrages(json_path):
    in_dict = json.load(open(json_path, 'r'))
    instr_ages = in_dict['instr_ages']

    # Remove the instructions that do not have input registers
    instr_ages = list(filter(lambda x: x is not None, instr_ages))

    # Count the number of instructions in each age
    count_by_age = {}
    existing_instr_ages = set(instr_ages)
    for existing_instr_age in existing_instr_ages:
        count_by_age[existing_instr_age] = instr_ages.count(existing_instr_age)

    # Normalize the counts
    normalized_count_by_age = {}
    for age in count_by_age:
        normalized_count_by_age[age] = 100 * count_by_age[age] / len(instr_ages)

    average_age = sum(instr_ages) / len(instr_ages)
    median_age = np.median(list(instr_ages))

    X = list(normalized_count_by_age.keys())
    Y = list(normalized_count_by_age.values())

    # Control flow only

    instr_ages_cfonly = in_dict['instr_ages_cfonly']

    # Count the number of instructions in each age
    count_by_age_cfonly = {}
    existing_instr_ages_cfonly = set(instr_ages_cfonly)
    for existing_instr_age_cfonly in existing_instr_ages_cfonly:
        count_by_age_cfonly[existing_instr_age_cfonly] = instr_ages_cfonly.count(existing_instr_age_cfonly)

    # Normalize the counts
    normalized_count_by_age_cfonly = {}
    for age in count_by_age_cfonly:
        normalized_count_by_age_cfonly[age] = 100 * count_by_age_cfonly[age] / len(instr_ages)

    X_all = list(normalized_count_by_age_cfonly.keys())
    Y_all = list(normalized_count_by_age_cfonly.values())

    plt.clf()
    fig = plt.figure(figsize=(5, 1.5))
    ax = fig.gca()

    width = 0.5

    ax.bar(X, Y, width=width, color='k', zorder=3)
    ax.bar(X_all, Y_all, width=width, color='orange', zorder=3)
    ax.yaxis.grid()

    ax.set_xlabel("Length of the dependency chain")
    ax.set_ylabel("Proportion (%)")

    ax.axvline(average_age - .005, color='r', linestyle='--', label=f"Average #dependencies ({average_age:.1f})")
    ax.axvline(median_age - .005, color='blue', linestyle='-.', label=f"Median #dependencies ({median_age:.1f})")

    fig.legend(framealpha=1)

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'difuzzrtl_dependencies.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)


def plot_difuzzrtl_prevalences(json_path):
    # Load prevalences.json
    instr_prevalences = json.load(open(json_path, 'r'))

    # Remove the instructions that do not have input registers
    instr_prevalences = list(filter(lambda x: x is not None, instr_prevalences))

    # Bucket the values
    hist, bin_edges = np.histogram(instr_prevalences, bins=100, range=(0, 1))

    # Trim the trailing zeros
    num_trailing_zeros = 0
    for i in range(len(hist) - 1, -1, -1):
        if hist[i] == 0:
            num_trailing_zeros += 1
        else:
            break
    if num_trailing_zeros:
        hist = hist[:-num_trailing_zeros]
        bin_edges = bin_edges[:-num_trailing_zeros]

    # Normalize the counts/scratch/flsolt/data/python-tmp/prevalences_1.json
    normalized_hist = {}
    for i in range(len(hist)):
        normalized_hist[i] = 100 * hist[i] / len(instr_prevalences)

    average_density = sum(instr_prevalences) / len(instr_prevalences)
    median_density = np.median(instr_prevalences)

    plt.clf()
    fig = plt.figure(figsize=(5, 1.5))
    ax = fig.gca()

    ax.bar(bin_edges[:-1], normalized_hist.values(), width=0.01, color='k', zorder=3)

    # ax.bar(X, Y, color='k', zorder=3)
    ax.yaxis.grid(which='major')

    ax.set_xlabel("Prevalence of fuzzing instructions (%)")
    ax.set_ylabel("Test cases (%)")

    tick_positions = list(map(lambda x: x - 0.005, list(bin_edges) + [0.4]))
    # Only take every 5th tick
    tick_positions = tick_positions[::5]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([f"{int(100*(x+0.005))}" for x in tick_positions])

    ax.set_xlim(-0.01, bin_edges[-1] + 0.01)

    ax.axvline(average_density - .005, color='r', linestyle='--', label=f"Average prevalence ({100*average_density:.1f}%)")
    ax.axvline(median_density - .005, color='blue', linestyle='-.', label=f"Median prevalence ({100*median_density:.1f}%)")

    fig.legend(framealpha=1)

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'difuzzrtl_prevalences.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)



def plot_difuzzrtl_completions(json_path):
    # Load rates_reached.json
    instr_completions = json.load(open(json_path, 'r'))

    # Remove the instructions that do not have input registers
    instr_completions = list(filter(lambda x: x is not None, instr_completions))

    # Bucket the values
    hist, bin_edges = np.histogram(instr_completions, bins=100, range=(0, 1))

    # Trim the trailing zeros
    num_trailing_zeros = 0
    for i in range(len(hist) - 1, -1, -1):
        if hist[i] == 0:
            num_trailing_zeros += 1
        else:
            break
    if num_trailing_zeros:
        hist = hist[:-num_trailing_zeros]
        bin_edges = bin_edges[:-num_trailing_zeros]

    # Normalize the counts
    normalized_hist = {}
    for i in range(len(hist)):
        normalized_hist[i] = 100 * hist[i] / len(instr_completions)

    average_completion = sum(instr_completions) / len(instr_completions)
    median_completion = np.median(instr_completions)

    plt.clf()
    fig = plt.figure(figsize=(5, 1.5))
    ax = fig.gca()

    ax.bar(bin_edges[:-1], normalized_hist.values(), width=0.01, color='k', zorder=3)

    # ax.bar(X, Y, color='k', zorder=3)
    ax.yaxis.grid()

    ax.set_xlabel("Fuzzing stage completion (%)")
    ax.set_ylabel("Test cases (%)")

    tick_positions = list(map(lambda x: x - 0.005, list(bin_edges) + [0.4]))
    # Only take every 10th tick
    tick_positions = tick_positions[::10]
    ax.set_xticks(tick_positions)
    ax.set_xticklabels([f"{int(100*(x+0.005))}" for x in tick_positions])

    ax.set_ylim(0, max(normalized_hist.values()) + 5)
    ax.set_xlim(-0.01, bin_edges[-1] + 0.01)

    ax.axvline(average_completion - .005, color='r', linestyle='--', label=f"Average completion rate ({100*average_completion:.1f}%)")
    ax.axvline(median_completion - .005, color='blue', linestyle='-.', label=f"Median completion rate ({100*median_completion:.1f}%)")

    fig.legend(framealpha=1)

    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, 'difuzzrtl_completions.png')
    print('Saving figure to', retpath)
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)
