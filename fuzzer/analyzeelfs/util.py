from params.runparams import PATH_TO_TMP
import subprocess
import os
import re

CASCADE_NUM_INITIAL_INSTR = 5 + 64 # 64 instructions in the initial block + 5 instructions in the spike bootrom
CASCADE_NUM_FINAL_INSTR = 105 # 105 instructions in the final block

def get_instance_elfpath(is_difuzzrtl: bool, design_name: str, instance_id: int):
    if is_difuzzrtl:
        assert design_name == 'rocket', "Only Rocket is supported for difuzz-rtl."
        path_to_diffuzzrtl_elfs = os.environ['CASCADE_PATH_TO_DIFUZZRTL_ELFS']
        return os.path.join(path_to_diffuzzrtl_elfs, f"id_{instance_id}.elf")
    else:
        elfdir_path = os.path.join(PATH_TO_TMP, 'manyelfs')
        return os.path.join(elfdir_path, f"{design_name}_{instance_id}.elf")

def get_instance_finaladdr(is_difuzzrtl: bool, design_name: str, instance_id: int, elfpath: str = None):
    if is_difuzzrtl:
        assert elfpath is not None, "elfpath must be provided for difuzz-rtl."
        ret_addr = subprocess.check_output([f"nm {elfpath} | grep _test_end"], shell=True, text=True)
        return int(ret_addr.split()[0], 16)
    else:
        elfdir_path = os.path.join(PATH_TO_TMP, 'manyelfs')
        with open(os.path.join(elfdir_path, f"{design_name}_{instance_id}_finaladdr.txt"), "r") as f:
            return int(f.read(), 16) + 0x80000000

# For DifuzzRTL. The last l symbol is always empty (contains only ecall)
def get_instance_max_l_symbol(elfpath: str = None):
    ret_lines = subprocess.check_output([f"nm {elfpath}"], shell=True, text=True)
    # Among ret_lines, find all lines that have the pattern _l followed by digits
    ret_lines = list(filter(lambda s: re.search(r'_l\d+', s), ret_lines.split('\n')))
    ret_symbols = list(map(lambda s: s.split()[-1], ret_lines))
    ret_vals = list(map(lambda s: int(s[2:], 10), ret_symbols))
    return max(ret_vals)

def get_max_reached_l_symbol(spike_log: str):
    ret = []
    for line in spike_log.split('\n'):
        if re.search(r'_l\d+', line):
            symbol_str = line.split()[-1]
            symbol_val = int(symbol_str[2:], 10)
            ret.append(symbol_val)
    if not ret:
        return 0
    return max(ret)

# @param finaladdr not used by difuzzrtl
def compute_prevalence(is_difuzzrtl: bool, spike_log: str, finaladdr: int):
    num_overhead_instructions = 0
    num_effective_instructions = 0

    if is_difuzzrtl:
        is_currently_overhead = True

        for line in spike_log.split('\n'):
            if re.search(r'_l\d+', line):
                is_currently_overhead = False
            elif 'exception' in line:
                is_currently_overhead = True
            
            num_overhead_instructions += is_currently_overhead
            num_effective_instructions += not is_currently_overhead
        return num_effective_instructions, num_overhead_instructions
    else:
        # Filter the lines that correspond to executed instructions
        num_executed_instrs = len(list(filter(lambda l: l.startswith('core   0: 0x'), spike_log.split('\n'))))
        num_effective_instructions = num_executed_instrs - CASCADE_NUM_INITIAL_INSTR
        num_overhead_instructions = CASCADE_NUM_FINAL_INSTR + CASCADE_NUM_INITIAL_INSTR
        return num_effective_instructions, num_overhead_instructions

# @param only_cf: If True, only return the control-flow instructions. Else, only the non-control-flow.
def filter_list_by_cf(candidate_list, indices_of_cf_instrs, only_cf: bool):
    assert only_cf
    return [candidate_list[i] for i in indices_of_cf_instrs]
