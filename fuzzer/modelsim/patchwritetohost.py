# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Only for difuzzrtl. Patches the ELFs to write to the suitable address to stop the testbench.

import os

# @return True iff the ELF existed
def replace_write_to_host(path_to_origin_elf, path_to_patched_elf):
    assert os.path.exists(path_to_origin_elf), f"ELF {path_to_origin_elf} does not exist."
    assert path_to_origin_elf != path_to_patched_elf, f"ELF path and patched ELF path are the same. Difference is not strictly required but this is suspicious."

    if not os.path.exists(path_to_origin_elf):
        return False

    # Read the object file as binary
    with open(path_to_origin_elf, 'rb') as file:
        content = file.read()

    pattern = b'\x93\x01\x10\x00\x17\x1f\x00\x00\x23\x26\x3f\xc6'
    pattern_head = b'\x93\x01\x10\x00\x17\x1f\x00\x00\x23'
    assert pattern_head in content, f"Pattern {pattern_head} not found in the ELF {path_to_origin_elf}"
    assert content.count(pattern_head) == 1, f"Pattern {pattern_head} found more than once in the ELF."
    replacement = b'\x37\x05\x00\x60\x23\x20\x05\x00\x6f\x00\x00\x00'
    assert len(pattern) == len(replacement), f"Pattern and replacement have different lengths: {len(pattern)} vs {len(replacement)}"

    # Patch now
    index_of_pattern = content.index(pattern_head)
    content = content[:index_of_pattern] + replacement + content[index_of_pattern + len(pattern):]

    # Write the modified content back to the file
    with open(path_to_patched_elf, 'wb') as file:
        file.write(content)    
    return True
