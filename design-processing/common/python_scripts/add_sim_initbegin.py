# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script replaces initial X states by random values (actually, by zeros), as the primitives are removed by Yosys.
# This is a simplified version that detects all the registers without a reset signal and add an initial begin statement for them.

import multiprocessing as mp
import re
import sys

# sys.argv[1]: path to source cascade.sv
# sys.argv[2]: path to target cascade.sv file where the initial states are randomized

MODULE_REGEX = r"(module(?:\s|\n)+(?:.+?)(?:\s|\n)*(?:\(|#|import)(?:.|\n)+?endmodule)"
MODULE_FF_LINE0 = r"always_ff @\((?:pos|neg)edge\s+[a-zA-Z0-9_]+\)\s*$"

NUM_PARALLEL_TASKS = mp.cpu_count() - 2

# @param module_name for debug only
# @return the transformed module definition.
def add_initial_blocks(module_definition: str):
    # tactic: cut into lines and find the succession of two line types.
    module_definition_lines = list(map(lambda s: s.strip(), module_definition.split('\n')))
    signal_names_to_initialize = []
    # Find the signal names to initialize
    for module_line_id in range(len(module_definition_lines)):
        # If this is a single edge sensitive register. Note the absence of `begin` keyword.
        if re.match(MODULE_FF_LINE0, module_definition_lines[module_line_id]):
            # print(module_line_id, module_definition_lines[module_line_id+1])
            curr_module_line_id_for_assignment = module_line_id+1
            # Manage cascaded ifs
            while re.match(r"if\s*\([\\$!a-zA-Z0-9_]+\)\s*$", module_definition_lines[curr_module_line_id_for_assignment].strip()):
                curr_module_line_id_for_assignment += 1
            curr_assignment_line = module_definition_lines[curr_module_line_id_for_assignment]
            if not '<=' in curr_assignment_line:
                print(f"WARNING: Did not find symbol `<=` in register assignment in line `{curr_assignment_line}`.")
            else:
                signal_names_to_initialize.append(list(filter(lambda s: bool(s), curr_assignment_line.split('<=')[0].split(' ')))[-1])
    # Initialize the signals
    if signal_names_to_initialize:
        lines_to_add = [
            '// Added block to randomize initial values.',
            '`ifdef RANDOMIZE_INIT',
            '  initial begin'
        ]
        for signal_name in signal_names_to_initialize:
            lines_to_add.append(f"    {signal_name} = '0;")
        lines_to_add.append('  end')
        lines_to_add.append('`endif // RANDOMIZE_INIT')
        # Insert at the end of the module definition
        if module_definition_lines[-1].split(' ')[0].strip() != 'endmodule':
            raise ValueError(f"End of module line is unexpectedly `{module_definition_lines[-1]}`.")
        last_line = module_definition_lines[-1]
        module_definition_lines[-1] = lines_to_add[0]
        for line_to_add_id in range(1, len(lines_to_add)):
            module_definition_lines.append(lines_to_add[line_to_add_id])
        module_definition_lines.append(last_line)
    return '\n'.join(module_definition_lines)

if __name__ == "__main__":
    global cascade_in_lines
    cascade_in_path =  sys.argv[1]
    cascade_out_path = sys.argv[2]

    with open(cascade_in_path, "r") as f:
        cascade_in_content = f.read()

    # module_definitions will be a list of pairs (module_content including module and endmodule keywords, module name)
    module_definitions = re.findall(MODULE_REGEX, cascade_in_content, re.MULTILINE | re.DOTALL)

    with mp.Pool(processes=NUM_PARALLEL_TASKS) as pool:
        # ret_strlines: list of per-instruction lists of strings
        initialized_module_definitions = list(pool.map(add_initial_blocks, module_definitions))
        pool.close()
        pool.join()

    with open(cascade_out_path, "w") as f:
        f.write('\n\n'.join(initialized_module_definitions))
