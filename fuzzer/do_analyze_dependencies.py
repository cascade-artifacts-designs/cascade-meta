# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script analyzes the properties of the Cascade-generated ELFs.

from params.runparams import PATH_TO_TMP
from analyzeelfs.genmanyelfs import gen_many_elfs
from analyzeelfs.analyze import analyze_elf_prevalence, analyze_elf_dependencies
from analyzeelfs.plot import plot_cascade_dependencies, plot_cascade_prevalences

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    NUM_ELFS = 500

    num_cores_for_elf_generation = int(os.getenv('CASCADE_JOBS', 160))

    gen_many_elfs('rocket', num_cores_for_elf_generation, NUM_ELFS, os.path.join(PATH_TO_TMP, 'manyelfs'))

    dependencies_json_path = analyze_elf_dependencies(False, 'rocket', NUM_ELFS)
    print('dependencies_json_path', dependencies_json_path)

    plot_cascade_dependencies(dependencies_json_path)

else:
    raise Exception("This module must be at the toplevel.")
