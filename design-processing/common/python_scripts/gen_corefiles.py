# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# sys.argv[1]: source template core file
# sys.argv[2]: destination template core file

import os
import re
import sys

if __name__ == "__main__":
    src_filename = sys.argv[1]
    tgt_filename = sys.argv[2]

    with open(src_filename, "r") as f:
        content = f.read()

    # Find the occurrences of a dollar sign and alpha-numeric characters
    pattern = r'\$([A-Za-z_]+[A-Za-z0-9_]*)'
    matches = re.findall(pattern, content)

    # Replace occurrences with the actual value
    for match in matches:
        env_var_name = match
        env_var_value = os.environ.get(env_var_name, '')
        content = content.replace('$' + env_var_name, env_var_value)

    with open(tgt_filename, "w") as f:
        f.write(content)

