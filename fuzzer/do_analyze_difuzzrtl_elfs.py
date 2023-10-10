# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script analyzes the properties of the Cascade-generated ELFs.

from analyzeelfs.analyze import analyze_elf_prevalence, analyze_elf_dependencies, analyze_elf_symbols
from analyzeelfs.plot import plot_difuzzrtl_completions, plot_difuzzrtl_prevalences, plot_difuzzrtl_instrages

import os
import sys

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    num_elfs = 50
    if len(sys.argv) > 1:
        num_elfs = int(sys.argv[1])

    num_cores_for_elf_generation = int(os.getenv('CASCADE_JOBS', 160))

    prevalence_json = analyze_elf_prevalence(True, num_elfs)
    dependencies_json = analyze_elf_dependencies(True, 'rocket', num_elfs)
    symbols_json = analyze_elf_symbols(num_elfs)

    plot_difuzzrtl_prevalences(prevalence_json)
    plot_difuzzrtl_instrages(dependencies_json)
    plot_difuzzrtl_completions(symbols_json)

else:
    raise Exception("This module must be at the toplevel.")
