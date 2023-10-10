# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Corrects Yosys mistakes such as: assign { 48'hffffffffffff, \gen_special_results[0].active_format.special_results.special_res [31:16] } = info_q[5]

import sys
import re

# sys.argv[1] the path to the input file.
# sys.argv[2] the path to the output file.

if __name__ == "__main__":
    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()
    verilog_lines = verilog_content.splitlines()
    # Find all lines ids that contain $display
    display_line_ids = []
    for line_id in range(len(verilog_lines)):
        if "$display" in verilog_lines[line_id] or "$finish" in verilog_lines[line_id]:
            display_line_ids.append(line_id)
    # Replace them with `begin end`
    for line_id in display_line_ids:
        verilog_lines[line_id] = "  begin end"
    # Rebuild the verilog content
    verilog_content = "\n".join(verilog_lines)
    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
