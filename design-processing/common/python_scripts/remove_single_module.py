# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Remove a single module declaration from given SystemVerilog file.

import re
import sys

# sys.argv[1]: source file path.
# sys.argv[2]: target file path (will be a copy of the source file, but without the specified modules).
# sys.argv[3]: name of the top module to remove.
# sys.argv[4]: number of expected occurrences of the module.

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Takes 4 arguments: the Verilog source file path, the Verilog target file path, the module name to remove and the number of expected module declarations.")

    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()        

    module_name = sys.argv[3]
    num_expected_occurrences = int(sys.argv[4])
    num_found_occurrences = len(re.findall("module(\s|\n)+{}(\s|\n)*(\(|#|import)(.|\n)+?endmodule[^\n]*\n".format(module_name), verilog_content))
    assert num_found_occurrences == num_expected_occurrences, f"Found `{num_found_occurrences}` occurrences of declarations of module `{sys.argv[3]}`, expected `{num_expected_occurrences}`."
    # Remove the first occurrence of the module declaration
    verilog_content, num_subs = re.subn("module(\s|\n)+{}(\s|\n)*(\(|#|import)(.|\n)+?endmodule[^\n]*\n".format(module_name), "\n", verilog_content, 1, flags=re.MULTILINE|re.DOTALL) # Weakness: does not ignore comments.
    print("  Removed {}/{} occurrence of module {}.".format(num_subs, num_expected_occurrences, module_name))

    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
