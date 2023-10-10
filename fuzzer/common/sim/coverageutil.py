# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script provides utilities to merge coverage files from Verilator and estimate the number of achieved coverage points.

from params.runparams import PATH_TO_TMP

import os
import subprocess

# @param new_coveragepath_list a list of coverage files to merge and from which to extract coverage.
# @param delete_after_merge the coverage files are being deleted on-the-fly if this param is true.
# @param the path to which the merged coverage file should be written.
# @return num_coverage_points. Also writes to the retunr path.
def merge_and_extract_coverages_modelsim(design_name, new_coveragepath_list: list, return_path, delete_after_merge: bool = True, absolute: bool = False, name_complement: str = ''):
    # Merge coverage files.
    command_file_formerge = os.path.join(PATH_TO_TMP, 'coverage_merge_modelsim'+str(hash(tuple(new_coveragepath_list)))+f"{name_complement}.tcl")
    with open(command_file_formerge, 'w') as f:
        # print(f"return path: {return_path} (type: {type(return_path)})")
        # print(f"new_coveragepath_list (type: {type(new_coveragepath_list)}): {new_coveragepath_list}")
        f.write('vcover merge ' + ' '.join(new_coveragepath_list) + ' -out ' + return_path + '\nquit -f')
    subprocess.run(['vsim', '-64', '-c', '-do', command_file_formerge], check=True, capture_output=True)
    if delete_after_merge:
        for coverage_file in new_coveragepath_list:
            os.remove(coverage_file)
    # Delete the command file
    os.remove(command_file_formerge)

    # Extract coverage points.
    # ...
    # ...
    # ...
    # ...
    #     Enabled Coverage              Bins      Hits    Misses    Weight  Coverage
    #     ----------------              ----      ----    ------    ------  --------
    #     Assertions                       2         2         0         1   100.00%
    #     Branches                     28954     18911     10043         1    65.31%
    #     Conditions                   19253      2084     17169         1    10.82%
    #     Expressions                  21037      7461     13576         1    35.46%
    #     FSM States                      10         6         4         1    60.00%
    #     FSM Transitions                 22         7        15         1    31.81%
    #     Statements                   39610     34272      5338         1    86.52%
    #     Toggles                     988006    323898    664108         1    32.78%

    # Total coverage (filtered view): 43.77%
    # End time: ...

    command_file_forreport = os.path.join(PATH_TO_TMP, 'coverage_report_modelsim'+str(hash(tuple(new_coveragepath_list)))+f"{name_complement}.tcl")
    with open(command_file_forreport, 'w') as f:
        f.write('vcover report ' + return_path + ' -summary' + '\nquit -f')
    exec_out = subprocess.run(['vsim', '-64', '-c', '-do', command_file_forreport], check=True, text=True, capture_output=True)
    # Delete the command file
    os.remove(command_file_forreport)

    outlines = exec_out.stdout.split('\n')

    # Extract the coverage percentage for the different coverage types.
    coverage_types = ['Branches', 'Conditions', 'Expressions', 'FSM States', 'FSM Transitions', 'Statements', 'Toggles']

    if absolute:
        coverage_vals = {}
        for coverage_type in coverage_types:
            for line in outlines:
                if coverage_type in line:
                    if 'FSM' in line:
                        coverage_vals[coverage_type] = int(line.split()[4])
                    else:
                        coverage_vals[coverage_type] = int(line.split()[3])
                    break
        return coverage_vals
    else:
        coverage_percentages = {}
        for coverage_type in coverage_types:
            for line in outlines:
                if coverage_type in line:
                    coverage_percentages[coverage_type] = float(line.split()[-1][:-1])
                    break
        return coverage_percentages
