# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This module runs RFUZZ and collects multiplexer toggle coverage.
# We call this "Active RFUZZ" as opposed to running Cascade and collecting the multiplexer select coverage.

from common.threads import capture_process_output
from common.designcfgs import get_design_cascade_path
from params.runparams import PATH_TO_TMP

import json
import os

def collect_active_coverage_rfuzz(design_name: str, timeout_seconds: int):
    # Run the active RFUZZ on the required design
    cmd = ['make', '-C', f"{get_design_cascade_path(design_name)}", 'rerun_drfuzz_notrace']

    lines = capture_process_output(' '.join(cmd), timeout_seconds)

    # Get the start coverage
    start_coverage = None
    for line_id, line in enumerate(lines):
        if line.startswith('COVERAGE:'):
            start_coverage = int(lines[line_id+1], 10)
            break
    if start_coverage is None:
        print('lines')
        print(lines)
        raise Exception(f"Could not find the start coverage for design `{design_name}`.")

    # Get the start timestamp
    start_timestamp_milliseconds = None
    for line in lines:
        if line.startswith('Timestamp start:'):
            start_timestamp_milliseconds = int(line.split(' ')[-1], 10)
            break
    if start_timestamp_milliseconds is None:
        raise Exception(f"Could not find the start timestamp for design `{design_name}`.")

    coverage_amounts = [start_coverage]
    coverage_durations = [0]

    # Get the coverage amounts and durations
    for line_id, line in enumerate(lines):
        if line.startswith('Timestamp toggle:'):
            coverage_durations.append((int(line.split(' ')[-1], 10) - start_timestamp_milliseconds) / 1000)
            coverage_amounts.append(int(lines[line_id+1].split(' ')[-1], 10))

    json_filepath = os.path.join(PATH_TO_TMP, f"rfuzz_active_coverages_{design_name}.json")
    with open(json_filepath, 'w') as f: 
        json.dump({'coverage_sequence': coverage_amounts, 'durations': coverage_durations}, f)
    return json_filepath

