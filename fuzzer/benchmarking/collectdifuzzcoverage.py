from params.runparams import PATH_TO_TMP, PATH_TO_FIGURES

import os
import json
from tqdm import tqdm

from copy import deepcopy
from matplotlib import pyplot as plt
from matplotlib import ticker
import numpy as np

PATH_TO_LOGS_DIR = os.path.join('/')
PATH_TO_LOG_OURS = os.path.join(PATH_TO_LOGS_DIR, 'out_rocket_state_cascade.log')
PATH_TO_LOG_DIFUZZ = os.path.join(PATH_TO_LOGS_DIR, 'out_rocket_state.log')

DIFUZZRTL_INSTRUM_SLOWDOWN_FACTOR = 1/1.15 # Reported in the DifuzzRTL paper
PROGRAM_GENERATION_SLOWDOWN_FACTOR = 1/(1-0.479) # See "Performance of program construction"

def collectdifuzzcoverage():
    # Grep the timestamp start lines
    with open(PATH_TO_LOG_OURS, 'r') as f:
        lines_ours = f.readlines()
    with open(PATH_TO_LOG_DIFUZZ, 'r') as f:
        lines_difuzz = f.readlines()

    # Get the first iter timestamp
    iter_start_timestamp_ours = None
    iter_start_timestamp_difuzz = None
    for line in tqdm(lines_ours):
        if line.startswith('absolute time iter start: '):
            iter_start_timestamp_ours = float(line.split('absolute time iter start: ')[1])
            break
    else:
        raise Exception("Cannot find iter start timestamp in ours")
    for line in tqdm(lines_difuzz):
        if line.startswith('absolute time iter start: '):
            iter_start_timestamp_difuzz = float(line.split('absolute time iter start: ')[1])
            break
    else:
        raise Exception("Cannot find iter start timestamp in difuzz")


    # Get the coverages
    coverages_ours = []
    coverages_difuzz = []
    timestamps_ours = []
    timestamps_difuzz = []
    for line in tqdm(lines_ours):
        if line.startswith('[Cascade] Coverage -- '):
            coverages_ours.append(line)
        if len(coverages_ours) > len(timestamps_ours):
            if line.startswith('absolute time iter start: '):
                timestamps_ours.append(float(line.split('absolute time iter start: ')[1]))
    for line in tqdm(lines_difuzz):
        if line.startswith('[DifuzzRTL] Coverage -- '):
            coverages_difuzz.append(line)
        if len(coverages_difuzz) > len(timestamps_difuzz):
            if line.startswith('absolute time iter start: '):
                timestamps_difuzz.append(float(line.split('absolute time iter start: ')[1]))

    durations_ours = list(map(lambda x: x - iter_start_timestamp_ours, timestamps_ours))
    durations_difuzz = list(map(lambda x: x - iter_start_timestamp_difuzz, timestamps_difuzz))

    retpath = os.path.join(PATH_TO_TMP, 'difuzz_coverage.json')
    json.dump({
        'coverages_ours': coverages_ours,
        'coverages_difuzz': coverages_difuzz,
        'durations_ours': durations_ours,
        'durations_difuzz': durations_difuzz
    }, open(retpath, 'w'))
    print(f"Saved to {retpath}")


def formatter(x, pos):
    return "{:,.0f}".format(x)

def filtertext(s):
    return int(s.split('-- ')[1].split(' [')[0])

def plot_difuzzrtl_coverage():
    in_dict = json.load(open(os.path.join(PATH_TO_TMP, 'difuzz_coverage.json')))
    coverages_ours = in_dict['coverages_ours']
    coverages_difuzz = in_dict['coverages_difuzz']
    durations_ours = in_dict['durations_ours']
    durations_difuzz = in_dict['durations_difuzz']

    coverages_ours_nocorpus = deepcopy(coverages_ours)

    durations_ours_nocorpus = []

    # Express durations in hours
    for i in range(len(durations_ours)):
        durations_ours[i] /= 3600
    for i in range(len(durations_difuzz)):
        durations_difuzz[i] /= 3600

    # Apply slowdown factor
    for i in range(len(durations_ours)):
        durations_ours[i] *= DIFUZZRTL_INSTRUM_SLOWDOWN_FACTOR

    # Without a pre-generated corpus
    for i in range(len(durations_ours)):
        durations_ours_nocorpus.append(durations_ours[i] * PROGRAM_GENERATION_SLOWDOWN_FACTOR)

    # Limit the time window
    TIME_LIMIT_HOURS = 57
    if TIME_LIMIT_HOURS is not None:
        for i in range(len(durations_ours)):
            if durations_ours[i] > TIME_LIMIT_HOURS:
                durations_ours = durations_ours[:i]
                coverages_ours = coverages_ours[:i]
                break
        for i in range(len(durations_ours)):
            if durations_ours_nocorpus[i] > TIME_LIMIT_HOURS:
                coverages_ours_nocorpus = coverages_ours_nocorpus[:i]
                durations_ours_nocorpus = durations_ours_nocorpus[:i]
                break
        for i in range(len(durations_difuzz)):
            if durations_difuzz[i] > TIME_LIMIT_HOURS:
                durations_difuzz = durations_difuzz[:i]
                coverages_difuzz = coverages_difuzz[:i]
                break

    # Filter coverages from the text
    coverages_ours = list(map(filtertext, coverages_ours))
    coverages_ours_nocorpus = list(map(filtertext, coverages_ours_nocorpus))
    coverages_difuzz = list(map(filtertext, coverages_difuzz))

    # Plot ours and difuzz on the same figure
    plt.clf()
    fig = plt.figure(figsize=(5, 2))
    ax = fig.gca()

    ax.plot(durations_ours, coverages_ours, color='cyan', label='Cascade (with corpus)')
    ax.plot(durations_ours_nocorpus, coverages_ours_nocorpus, color='k', label='Cascade (live generation)')
    ax.plot(durations_difuzz, coverages_difuzz, color='r', label='DifuzzRTL')

    # Plot lines for 4h, 12h, 24h, 48h
    times_of_interest = [48]
    colors_of_interest = ['gray']
    assert len(times_of_interest) == len(colors_of_interest)

    interest_xs_difuzz = []
    interest_ys = []
    for i in range(len(durations_difuzz)):
        for time_of_interest_id, time_of_interest in enumerate(times_of_interest):
            if durations_difuzz[i] >= time_of_interest and len(interest_xs_difuzz) == time_of_interest_id:
                interest_xs_difuzz.append(durations_difuzz[i-1])
                interest_ys.append(coverages_difuzz[i-1])

    # Fint the corresponding ours values
    interest_xs_ours = []
    for i in range(len(durations_ours)):
        for time_of_interest_id, time_of_interest in enumerate(times_of_interest):
            if coverages_ours[i] >= interest_ys[time_of_interest_id] and len(interest_xs_ours) == time_of_interest_id:
                interest_xs_ours.append(durations_ours[i])

    interest_xs_ours_nocorpus = []
    for i in range(len(durations_ours_nocorpus)):
        for time_of_interest_id, time_of_interest in enumerate(times_of_interest):
            if coverages_ours_nocorpus[i] >= interest_ys[time_of_interest_id] and len(interest_xs_ours_nocorpus) == time_of_interest_id:
                interest_xs_ours_nocorpus.append(durations_ours_nocorpus[i])

    assert len(interest_xs_ours) == len(interest_xs_difuzz)
    assert len(interest_xs_ours) == len(interest_ys)
    assert len(interest_xs_ours_nocorpus) == len(interest_xs_difuzz)
    assert len(interest_xs_ours_nocorpus) == len(interest_ys)

    print(f"Time DifuzzRTL: {interest_xs_difuzz}")
    print(f"Time Cascade (with corpus) for getting the same coverage: {interest_xs_ours}")
    print(f"Time Cascade (live generation) for getting the same coverage: {interest_xs_ours_nocorpus}")

    print (f"Speedup of Cascade (with corpus) over DifuzzRTL: {interest_xs_difuzz[0]/interest_xs_ours[0]}")
    print (f"Speedup of Cascade (live generation) over DifuzzRTL: {interest_xs_difuzz[0]/interest_xs_ours_nocorpus[0]}")

    # Plot the interesting lines
    # Horizontal lines
    for i in range(len(interest_xs_ours)):
        ax.plot([interest_xs_ours[i], interest_xs_difuzz[i]], [interest_ys[i], interest_ys[i]], color=colors_of_interest[i], linestyle='--')
    # # Vertical lines on the left-hand side
    # for i in range(len(interest_xs_ours)):
    #     ax.axvline(interest_xs_ours[i], color=colors_of_interest[i], linestyle='--', label=f"Cascade exceeds in {round(interest_xs_ours[i]*60)}min")
    # Vertical lines on the right-hand side
    for i in range(len(interest_xs_ours)):
        ax.plot([interest_xs_difuzz[i], interest_xs_difuzz[i]], [interest_ys[i], 0], color=colors_of_interest[i], linestyle='--')

    ax.yaxis.grid(which='major')
    ax.xaxis.grid(which='major')

    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Coverage pts")

    xticks = [10*i for i in range(int(durations_ours[-1]/10))] + times_of_interest
    # xticks.remove(10)
    ax.set_xticks(xticks)
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(formatter))
    ax.legend(framealpha=0.8, loc='center right')

    fig.tight_layout()

    outpath = os.path.join(PATH_TO_FIGURES, 'difuzzrtl_coverage.png')
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath, dpi=300)
