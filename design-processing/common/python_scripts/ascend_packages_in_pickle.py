# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Move the packages up in the pickle files, works in place.

import re
import sys

# sys.argv[1]: source and target pickle Verilog file

REGEX = r"package(?:.|\n)+?endpackage"

if __name__ == "__main__":
    src_filename = sys.argv[1]

    with open(src_filename, "r") as f:
        content = f.read()

    # Get the package texts
    packagetexts = re.findall(REGEX, content, re.DOTALL)
    # Remove them from the pickle
    content = re.sub(REGEX, '\n\n', content, re.DOTALL)

    # Write them to the top of the pickle file
    content = '\n\n'.join(packagetexts) + content

    with open(src_filename, "w") as f:
        f.write(content)
