import bisect
import json
import numpy as np
import os
from tqdm import tqdm

from params.runparams import PATH_TO_TMP, PATH_TO_FIGURES

from matplotlib import pyplot as plt
from matplotlib import ticker

def formatter(x, pos):
    if x > 1000:
        return "{:,.0f}k".format(x//1000)
    else:
        return "{:,.0f}".format(x)

def plot_coverage_singlelines(produced_target_num_instrs):
    in_dict_ours_path = os.path.join(PATH_TO_TMP, f"modelsim_coverages_{produced_target_num_instrs}_series{0}_isdifuzz{int(0)}.json")
    in_dict_difuzz_path = os.path.join(PATH_TO_TMP, f"modelsim_coverages_{produced_target_num_instrs}_series{0}_isdifuzz{int(1)}.json")
    in_dict_ours = json.load(open(in_dict_ours_path, 'r'))
    in_dict_difuzz = json.load(open(in_dict_difuzz_path, 'r'))

    coverages_ours = in_dict_ours['coverages_sequence']
    all_num_instrs_ours = in_dict_ours['all_num_instrs']

    coverages_difuzz = in_dict_difuzz['coverages_sequence']
    all_num_instrs_difuzz = in_dict_difuzz['all_num_instrs']

    aggregated_coverages_ours = list(map(lambda x: sum(x.values()), coverages_ours))
    aggregated_coverages_difuzz = list(map(lambda x: sum(x.values()), coverages_difuzz))

    # For looking at toggle coverage only (which dominates the coverage)
    # aggregated_coverages_ours = list(map(lambda x: x['Toggles'], coverages_ours))
    # aggregated_coverages_difuzz = list(map(lambda x: x['Toggles'], coverages_difuzz))

    Xs_ours = [sum(all_num_instrs_ours[:i]) for i in range(len(all_num_instrs_ours))]
    Ys_ours = aggregated_coverages_ours

    Xs_difuzz = [sum(all_num_instrs_difuzz[:i]) for i in range(len(all_num_instrs_difuzz))]
    Ys_difuzz = aggregated_coverages_difuzz

    plt.plot(Xs_ours, Ys_ours, label='Cascade')
    plt.plot(Xs_difuzz, Ys_difuzz, label='DifuzzRTL')

    plt.xlabel('Number of instructions')
    plt.ylabel('Coverage points')

    plt.grid()

    plt.legend()
    plt.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, "comparisons_modelsim_singleseries.png")
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)


def plot_coverage_global(num_series, plot_num_instrs, produced_target_num_instrs):
    assert num_series > 0, f"num_series must be > 0, got {num_series}"
    assert plot_num_instrs < produced_target_num_instrs, f"plot_num_instrs must be < produced_target_num_instrs, got {plot_num_instrs} and {produced_target_num_instrs}"

    TOGGLE_ONLY = False

    all_series = list(range(num_series))

    all_in_dict_ours = []
    for absolute_series_id in all_series:
        all_in_dict_ours.append(json.load(open(os.path.join(PATH_TO_TMP, f"modelsim_coverages_{produced_target_num_instrs}_series{absolute_series_id}_isdifuzz{int(0)}.json"))))
    in_dict_difuzz = json.load(open(os.path.join(PATH_TO_TMP, f"modelsim_coverages_{produced_target_num_instrs}_series{0}_isdifuzz{int(1)}.json")))

    all_coverages_ours = []
    all_num_instrs_ours = []
    for series_id in range(len(all_series)):
        all_coverages_ours.append(all_in_dict_ours[series_id]['coverages_sequence'])
        all_num_instrs_ours.append(all_in_dict_ours[series_id]['all_num_instrs'])

    coverages_difuzz = in_dict_difuzz['coverages_sequence']
    all_num_instrs_difuzz = in_dict_difuzz['all_num_instrs']

    all_aggregated_coverages_ours = []
    for series_id in range(len(all_series)):
        if TOGGLE_ONLY:
            all_aggregated_coverages_ours.append(list(map(lambda x: 0 if not x else x['Toggles'], all_coverages_ours[series_id])))
        else:
            all_aggregated_coverages_ours.append(list(map(lambda x: sum(x.values()), all_coverages_ours[series_id])))
    if TOGGLE_ONLY:
        aggregated_coverages_difuzz = list(map(lambda x: 0 if not x else x['Toggles'], coverages_difuzz))
    else:
        aggregated_coverages_difuzz = list(map(lambda x: sum(x.values()), coverages_difuzz))

    # For looking at toggle coverage only (which dominates the coverage)
    # aggregated_coverages_ours = list(map(lambda x: x['Toggles'], coverages_ours))
    # aggregated_coverages_difuzz = list(map(lambda x: x['Toggles'], coverages_difuzz))

    all_Xs_ours = []
    for series_id in range(len(all_series)):
        all_Xs_ours.append([sum(all_num_instrs_ours[series_id][:i]) for i in range(len(all_num_instrs_ours[series_id]))])

    # Combine all Xs
    combined_Xs_ours = []
    for series_id in range(len(all_series)):
        combined_Xs_ours += all_Xs_ours[series_id]
    combined_Xs_ours = sorted(list(set(combined_Xs_ours)))

    # Combine all Ys
    all_combined_Ys_ours = []
    for series_id in range(len(all_series)):
        all_combined_Ys_ours.append([])
        for curr_x in combined_Xs_ours:
            # If we dont have data so much to the left for this series, or so much to the right, we just put None
            if curr_x < all_Xs_ours[series_id][0]:
                all_combined_Ys_ours[-1].append(None)
            elif curr_x > all_Xs_ours[series_id][-1]:
                all_combined_Ys_ours[-1].append(None)
            # If we got data for this x, we put it
            elif curr_x in all_Xs_ours[series_id]:
                all_combined_Ys_ours[-1].append(all_aggregated_coverages_ours[series_id][all_Xs_ours[series_id].index(curr_x)])
            # Else, we do linear interpolation
            else:
                x_left = all_Xs_ours[series_id][bisect.bisect_left(all_Xs_ours[series_id], curr_x) - 1]
                x_right = all_Xs_ours[series_id][bisect.bisect_right(all_Xs_ours[series_id], curr_x)]
                y_left = all_aggregated_coverages_ours[series_id][all_Xs_ours[series_id].index(x_left)]
                y_right = all_aggregated_coverages_ours[series_id][all_Xs_ours[series_id].index(x_right)]
                all_combined_Ys_ours[-1].append(y_left + (y_right - y_left) * (curr_x - x_left) / (x_right - x_left))

    # Average all Ys, ignore the None values
    Ys_ours = []
    for curr_x_id, curr_x in enumerate(combined_Xs_ours):
        curr_ys = []
        for series_id in range(len(all_series)):
            if all_combined_Ys_ours[series_id][curr_x_id] is not None:
                curr_ys.append(all_combined_Ys_ours[series_id][curr_x_id])
        Ys_ours.append(sum(curr_ys) / len(curr_ys))

    Xs_difuzz = [sum(all_num_instrs_difuzz[:i]) for i in range(len(all_num_instrs_difuzz))]
    Ys_difuzz = aggregated_coverages_difuzz

    # Stop X at plot_num_instrs
    Xs_difuzz = Xs_difuzz[:bisect.bisect_right(Xs_difuzz, plot_num_instrs)+1]
    Ys_difuzz = Ys_difuzz[:bisect.bisect_right(Xs_difuzz, plot_num_instrs)+1]
    combined_Xs_ours = combined_Xs_ours[:bisect.bisect_right(combined_Xs_ours, plot_num_instrs)+1]
    Ys_ours = Ys_ours[:bisect.bisect_right(combined_Xs_ours, plot_num_instrs)+1]

    # Find the first x in combined_Xs_ours such that Ys_ours[x] > Ys_difuzz[-1]
    interest_x_ours = combined_Xs_ours[bisect.bisect_left(Ys_ours, Ys_difuzz[-1])]
    interest_y_ours = Ys_ours[bisect.bisect_left(Ys_ours, Ys_difuzz[-1])]

    plt.clf()
    fig = plt.figure(figsize=(5, 1.8))
    ax = fig.gca()

    ax.plot(combined_Xs_ours, Ys_ours, color='k', label='Cascade')
    ax.plot(Xs_difuzz, Ys_difuzz, color='red', label='DifuzzRTL')

    # Plot the line of equal coverage
    ax.plot([interest_x_ours, Xs_difuzz[-1]], [interest_y_ours, Ys_difuzz[-1]], '--', color='gray')
    ax.plot([interest_x_ours, interest_x_ours], [Ys_ours[0], interest_y_ours], '--', color='gray', label=f"Intersection: {formatter(interest_x_ours, None)} instrs")

    ax.set_xlabel('Number of instructions')
    ax.set_ylabel('Simulator coverage')

    ax.set_ylim(bottom=4e5)

    ax.yaxis.set_major_formatter(ticker.FuncFormatter(formatter))
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(formatter))

    ax.grid()

    ax.legend(ncol=2)
    fig.tight_layout()

    retpath = os.path.join(PATH_TO_FIGURES, "comparisons_modelsim.png")
    os.makedirs(PATH_TO_FIGURES, exist_ok=True)
    plt.savefig(retpath, dpi=300)
