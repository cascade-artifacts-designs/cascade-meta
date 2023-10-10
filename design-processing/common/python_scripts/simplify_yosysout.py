# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Takes a Yosys output with paramod module names, and simplifies these module names.

import hashlib
import multiprocessing as mp
import re
import sys

num_workers = mp.cpu_count()

MODULE_DECL_REGEX = r"\\\$paramod\$([^ ]+) "
BACKARRAY_DECL_REGEX = r"\\([a-zA-Z0-9_]+)\[(\d+)\]([a-zA-Z0-9_.]*)"

UGLY_MODULENAME_MAX_LENGTH = 30

# sys.argv[1]: source file path.
# sys.argv[2]: target file path.

module_hash_correspondances = dict()

# WARNING: the lines generated into module_hash_correspondances_debugheaderlines may be used by subsequent scripts. Modify their format with care.
module_hash_correspondances_debugheaderlines = []

def simplify_module_name(modulename_ugly):
    global module_hash_correspondances_debugheaderlines
    # Remove all backslashes, dollar and equal signs
    candidate = modulename_ugly.replace('$', '').replace('\\', '').replace('=', '')
    # If the name is still too long, we replace it with a short hash
    if len(candidate) > UGLY_MODULENAME_MAX_LENGTH:
        if candidate not in module_hash_correspondances:
            m = hashlib.sha256()
            m.update(candidate.encode('ascii'))
            candidate_hash = f"simplif_{m.hexdigest()[:20]}"
            assert candidate_hash not in module_hash_correspondances.values(), "Unlucky clash in hashes"
            module_hash_correspondances[candidate] = candidate_hash
            module_hash_correspondances_debugheaderlines.append(f"//   {candidate.ljust(UGLY_MODULENAME_MAX_LENGTH)}: {module_hash_correspondances[candidate]}")
        return module_hash_correspondances[candidate]
    else:
        return candidate

def simplify_backarray(backarray_name, backarray_index, postarr):
    print('triple', backarray_name, backarray_index, postarr)
    return "{}__{}_{}".format(backarray_name, backarray_index, postarr.replace('.', '_DOT_'))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Takes at least 2 arguments: the Verilog source file path, the Verilog target file path. The rest of the arguments are modules that must not be removed")

    with open(sys.argv[1], "r") as f:
        verilog_content = f.read()

    #####################
    # Module names
    #####################
    matches = re.findall(MODULE_DECL_REGEX, verilog_content, re.IGNORECASE)

    for modulesuffix in matches:
        simplified_modulename = 'paramod'+simplify_module_name(modulesuffix)
        verilog_content = verilog_content.replace('\$paramod$'+modulesuffix, simplified_modulename)

    #####################
    # Arrays preceded by a backslash
    #####################
    matches = re.findall(BACKARRAY_DECL_REGEX, verilog_content, re.IGNORECASE)

    for arrname, arrindex, postarr in matches:
        simplified_backarray = simplify_backarray(arrname, arrindex, postarr)
        verilog_content = verilog_content.replace('\\'+arrname+'['+arrindex+']'+postarr, simplified_backarray)

    if module_hash_correspondances_debugheaderlines:
        verilog_content = '// Simplified module names\n' + '\n'.join(module_hash_correspondances_debugheaderlines) + '\n\n' + verilog_content

    with open(sys.argv[2], "w") as f:
        f.write(verilog_content)
