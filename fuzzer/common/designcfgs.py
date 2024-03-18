# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

import json
import os
from functools import cache

DESIGN_REPOS_JSON_NAME = "design_repos.json"

def get_design_cascade_path(design_name):
    # 1. Find the designs folder.
    designs_folder = os.getenv("CASCADE_DESIGN_PROCESSING_ROOT")
    if not designs_folder:
        raise Exception("Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo")
    # 2. Find the repo name.
    with open(os.path.join(designs_folder, DESIGN_REPOS_JSON_NAME), "r") as f:
        read_dict = json.load(f)
    try:
        repo_name = read_dict[design_name]
    except:
        candidate_names = read_dict.keys()
        raise ValueError("Design name not in design_repos.json: {}. Candidates are: {}.".format(design_name, ', '.join(candidate_names)))
    return os.path.join(designs_folder, repo_name)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the design config of the relevant repo.
@cache
def get_design_cfg(design_name):
    with open(os.path.join(get_design_cascade_path(design_name), "meta", "cfg.json"), "r") as f:
        return json.load(f)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the top soc name, for example ibex_tiny_soc.
def get_design_top_soc(design_name) -> str:
    device_config = get_design_cfg(design_name)
    return device_config["toplevel"]

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the boot address of the design.
def get_design_boot_addr(design_name) -> int:
    device_config = get_design_cfg(design_name)
    return int(device_config["bootaddr"], base=0)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the march flags for the design, for example `-march=rv64gc -mabi=lp64`.
def get_design_march_ccflags(design_name) -> int:
    device_config = get_design_cfg(design_name)
    return device_config["marchflags"]

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return for example `rv64gc`.
def get_design_march_flags(design_name) -> str:
    return get_design_march_ccflags(design_name).split('-march=')[1].split(' ')[0].lower()

def get_design_march_flags_nocompressed(design_name) -> str:
    return get_design_march_ccflags(design_name).split('-march=')[1].split(' ')[0].lower().replace('c', '')

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the stop signal address of the design: the address to which to write to stop the simulation.
def get_design_stop_sig_addr(design_name) -> int:
    device_config = get_design_cfg(design_name)
    return int(device_config["stopsigaddr"], base=0)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the register dump address of the design: the address to which the CPU dumps the registers, in order from 1.
def get_design_reg_dump_addr(design_name) -> int:
    device_config = get_design_cfg(design_name)
    return int(device_config["regdumpaddr"], base=0)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return the floating point register dump address of the design: the address to which the CPU dumps the floating point registers, in order from 0.
def get_design_fpreg_dump_addr(design_name) -> int:
    device_config = get_design_cfg(design_name)
    return int(device_config["fpregdumpaddr"], base=0)

# @param design_name: must be one of the keys of the design_repos.json dict.
# @return true iff the design is 32bit.
@cache
def is_design_32bit(design_name) -> bool:
    march_flags = get_design_march_flags(design_name)
    assert '128' not in march_flags, "Ensure that you support 128-bit design everywhere, and then remove this assertion."
    return '32' in march_flags

@cache
def design_has_float_support(design_name) -> bool:
    return 'f' in get_design_march_flags(design_name) or 'g' in get_design_march_flags(design_name)

@cache
def design_has_double_support(design_name) -> bool:
    return 'd' in get_design_march_flags(design_name) or 'g' in get_design_march_flags(design_name)

@cache
def design_has_muldiv_support(design_name) -> bool:
    return 'm' in get_design_march_flags(design_name) or 'g' in get_design_march_flags(design_name)

@cache
def design_has_atop_support(design_name) -> bool:
    return 'a' in get_design_march_flags(design_name) or 'g' in get_design_march_flags(design_name)

@cache
def design_has_compressed_support(design_name) -> bool:
    return 'c' in get_design_march_flags(design_name)

def design_has_misaligned_data_support(design_name) -> bool:
    device_config = get_design_cfg(design_name)
    return device_config["misaligned_data_supported"]

# Privilege modes
# @return the privilege modes of the design, for example `msu`.
def design_get_privlvs_letters(design_name) -> str:
    device_config = get_design_cfg(design_name)
    return device_config["privlvs"]
def design_has_supervisor_mode(design_name) -> str:
    return 's' in design_get_privlvs_letters(design_name)
def design_has_user_mode(design_name) -> str:
    return 'u' in design_get_privlvs_letters(design_name)

# MMU
def design_has_only_bare(design_name) -> str:
    return not get_design_cfg(design_name)["mmu"]
def design_has_sv32(design_name) -> str:
    return "sv32" in get_design_cfg(design_name)["mmu"]
def design_has_sv39(design_name) -> str:
    return "sv39" in get_design_cfg(design_name)["mmu"]
def design_has_sv48(design_name) -> str:
    return "sv48" in get_design_cfg(design_name)["mmu"]

def design_get_privlvs_letters(design_name) -> str:
    device_config = get_design_cfg(design_name)
    return device_config["privlvs"]

def design_has_pmp(design_name) -> str:
    if design_name == "picorv32":
        return False
    return True

# For Verilator
# @param design_name: must be one of the keys of the design_repos.json dict.
# @param dotrace: boolean.
# @return pair(the base path to the 'cascade' folder of the design repository, the RELATIVE path to the hardware simulation binary of the given design with the given parameters).
def get_design_hsb_path(design_name, dotrace):
    design_cascade_path = get_design_cascade_path(design_name)
    dotrace_str = "trace" if dotrace else "notrace"
    toplevel_name = get_design_cfg(design_name)["toplevel"]
    return design_cascade_path, "build/run_vanilla_{}_0.1/default-verilator/V{}".format(dotrace_str, toplevel_name)

# For Modelsim
# @param design_name: must be one of the keys of the design_repos.json dict.
# @param dotrace: boolean.
# @return pair(the base path to the 'cascade' folder of the design repository, the RELATIVE path to the hardware simulation binary of the given design with the given parameters).
def get_design_worklib_path(design_name, dotrace, fuzzcoreid: int = 0):
    design_cascade_path = get_design_cascade_path(design_name)
    dotrace_str = "trace" if dotrace else "notrace"
    if design_name == 'rocket':
        local_dirname = f"{get_design_top_soc(design_name)}_rocket_{fuzzcoreid}"
    elif design_name == 'boom':
        local_dirname = f"{get_design_top_soc(design_name)}_boom_{fuzzcoreid}"
    else:
        local_dirname = f"{get_design_top_soc(design_name)}_{fuzzcoreid}"
    return design_cascade_path, os.path.join(os.getenv('MODELSIM_WORKROOT'), local_dirname, f"work_vanilla_{dotrace_str}")

# Prettifies known design names.
def get_design_prettyname(design_name):
    if design_name == "ibex":
        return "Ibex"
    elif design_name == "cva6":
        return "Ariane"
    elif design_name == "pulpissimo":
        return "PULPissimo"
    elif design_name == "rocket":
        return "Rocket"
    elif design_name == "boom":
        return "BOOM"
    else:
        raise NotImplementedError(f"get_design_prettyname not implemented for design `{design_name}`.")
        return design_name

# Get the path to V<toplevel_name>__024root.h'
def get_root_c_header_path(design_name, dotrace):
    cascade_path = get_design_cascade_path(design_name)
    run_target_str = "run_vanilla_{}_0.1".format("trace" if dotrace else "notrace")
    return os.path.join(cascade_path, "build", run_target_str, "default-verilator")

# The instructions to stop a benchmark
def get_stop_instructions(design_name, rd_id: int):
    if rd_id < 0 or rd_id > 32:
        raise ValueError(f"Unexpected destination register value: {rd_id}")
    if design_name in ('rocket', 'boom'):
        return f"la t0, 0x60000000\n sw x{rd_id}, (t0)"
    else:
        return f"sw x{rd_id}, (x0)"
