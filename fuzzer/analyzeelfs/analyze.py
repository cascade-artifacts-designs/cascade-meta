# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from analyzeelfs.dependencies import get_dependencies_per_instruction
from analyzeelfs.util import get_instance_elfpath, get_instance_finaladdr, filter_list_by_cf, get_instance_max_l_symbol, get_max_reached_l_symbol, compute_prevalence
from params.runparams import PATH_TO_TMP

import itertools
import json
import os
import subprocess

import multiprocessing as mp

ISA_FLAGS = '--isa=rv64g' # We are focusing on Rocket for this analysis

# Returns the run log for the given instance.
def spike_get_run_log(is_difuzzrtl: bool, design_name: str, instance_id: int, path_to_elf: str, finaladdr: int):
    # First, create a temporary file to store the command.
    cmd_tmp_path = os.path.join(PATH_TO_TMP, f"spikecmd_{int(is_difuzzrtl)}_{design_name}_{instance_id}.txt")
    with open(cmd_tmp_path, "w") as f:
        f.write(f"untiln pc 0 {hex(finaladdr)}\nq\n")
    subprocess_cmd = ["spike", "-d", f"--debug-cmd={cmd_tmp_path}", ISA_FLAGS, "--pc=0x80000000", path_to_elf]
    out_text = subprocess.run(subprocess_cmd, check=True, capture_output=True, text=True)
    # Remove the command file.
    os.remove(cmd_tmp_path)
    return out_text.stderr

def age_analysis_worker(is_difuzzrtl: bool, design_name: str, instance_id: int):
    elfpath = get_instance_elfpath(is_difuzzrtl, design_name, instance_id)
    if not os.path.exists(elfpath):
        return None, None
    finaladdr = get_instance_finaladdr(is_difuzzrtl, design_name, instance_id, elfpath)
    spike_log = spike_get_run_log(is_difuzzrtl, design_name, instance_id, elfpath, finaladdr)
    instr_ages_instance, indices_of_cf_instrs = get_dependencies_per_instruction(spike_log, is_difuzzrtl, instance_id)
    instr_ages_cfonly_instance = filter_list_by_cf(instr_ages_instance, indices_of_cf_instrs, True)
    return instr_ages_instance, instr_ages_cfonly_instance

# Analyzes the reached symbols
def symbol_analysis_worker(instance_id: int):
    design_name = 'rocket'
    is_difuzzrtl = True
    elfpath = get_instance_elfpath(is_difuzzrtl, design_name, instance_id)
    if not os.path.exists(elfpath):
        return None, None
    finaladdr = get_instance_finaladdr(is_difuzzrtl, design_name, instance_id, elfpath)
    spike_log = spike_get_run_log(is_difuzzrtl, design_name, instance_id, elfpath, finaladdr)
    max_available_lsymbol = get_instance_max_l_symbol(elfpath)
    max_reached_lsymbol = get_max_reached_l_symbol(spike_log)
    return max_available_lsymbol, max_reached_lsymbol

def prevalence_analysis_worker(is_difuzzrtl: bool, instance_id: int):
    design_name = 'rocket'
    elfpath = get_instance_elfpath(is_difuzzrtl, design_name, instance_id)
    if not os.path.exists(elfpath):
        return None, None
    finaladdr = get_instance_finaladdr(is_difuzzrtl, design_name, instance_id, elfpath)
    spike_log = spike_get_run_log(is_difuzzrtl, design_name, instance_id, elfpath, finaladdr)
    num_effective_instructions, num_overhead_instructions = compute_prevalence(is_difuzzrtl, spike_log, finaladdr)
    if num_effective_instructions < 0 or num_overhead_instructions < 0:
        print('num_effective_instructions < 0 or num_overhead_instructions < 0', num_effective_instructions, num_overhead_instructions, is_difuzzrtl, instance_id)
        print(elfpath)
    return num_effective_instructions, num_overhead_instructions

def analyze_elf_prevalence(is_difuzzrtl: bool, num_instances: int):
    num_effective_instructions_list = []
    num_overhead_instructions_list = []

    instances = list(zip(itertools.repeat(is_difuzzrtl), range(num_instances)))
    with mp.Pool(mp.cpu_count()) as p:
        for num_effective_instructions, num_overhead_instructions in p.starmap(prevalence_analysis_worker, instances):
            if num_effective_instructions is not None and num_overhead_instructions is not None:
                num_effective_instructions_list.append(num_effective_instructions)
                num_overhead_instructions_list.append(num_overhead_instructions)

    rates_reached = [num_effective_instructions_list[i] / (num_overhead_instructions_list[i] + num_effective_instructions_list[i]) for i in range(len(num_effective_instructions_list))]

    retpath = os.path.join(PATH_TO_TMP, f"prevalences_{int(is_difuzzrtl)}.json")
    os.makedirs(os.path.dirname(retpath), exist_ok=True)
    json.dump(rates_reached, open(retpath, "w"))
    print('Saved prevalence results to', retpath)
    return retpath

def analyze_elf_symbols(num_instances: int):
    is_difuzzrtl = True
    max_available_lsymbols = []
    max_reached_lsymbols = []

    instances = range(num_instances)
    with mp.Pool(mp.cpu_count()) as p:
        for max_available_lsymbol, max_reached_lsymbol in p.map(symbol_analysis_worker, instances):
            if max_available_lsymbol is not None and max_reached_lsymbol is not None:
                max_available_lsymbols.append(max_available_lsymbol)
                max_reached_lsymbols.append(max_reached_lsymbol)

    rates_reached = [max_reached_lsymbols[i] / max_available_lsymbols[i] for i in range(len(max_available_lsymbols))]

    retpath = os.path.join(PATH_TO_TMP, f"completions_{int(is_difuzzrtl)}.json")
    os.makedirs(os.path.dirname(retpath), exist_ok=True)
    json.dump(rates_reached, open(retpath, "w"))
    print('Saved completion results to', retpath)
    return retpath

def analyze_elf_dependencies(is_difuzzrtl: bool, design_name: str, num_instances: int):
    assert design_name == 'rocket'
    
    instr_ages = []
    instr_ages_cfonly = []

    instances = (itertools.repeat(is_difuzzrtl), itertools.repeat(design_name), range(num_instances))
    with mp.Pool(mp.cpu_count()) as p:
        for instr_ages_instance, instr_ages_cfonly_instance in p.starmap(age_analysis_worker, zip(*instances)):
            if instr_ages_instance is not None and instr_ages_cfonly_instance is not None:
                instr_ages.append(instr_ages_instance)
                instr_ages_cfonly.append(instr_ages_cfonly_instance)

    # Flatten the list
    instr_ages = [item for sublist in instr_ages for item in sublist]
    instr_ages_cfonly = [item for sublist in instr_ages_cfonly for item in sublist]

    retpath = os.path.join(PATH_TO_TMP, f"dependencies_{int(is_difuzzrtl)}.json")
    os.makedirs(os.path.dirname(retpath), exist_ok=True)
    json.dump(
        {
            'instr_ages': instr_ages,
            'instr_ages_cfonly': instr_ages_cfonly
        },
        open(retpath, 'w')
    )
    print('Saved dependency results to', retpath)
    return retpath
