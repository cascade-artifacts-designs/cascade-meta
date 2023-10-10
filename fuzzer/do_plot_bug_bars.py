# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script plots the bars related to the bug categories and their security implications.

from miscplots.plotcategories import plot_bugtypes_bars
from miscplots.plotsecuimplications import plot_security_implications

import os

if __name__ == '__main__':
    if "CASCADE_ENV_SOURCED" not in os.environ:
        raise Exception("The Cascade environment must be sourced prior to running the Python recipes.")

    plot_bugtypes_bars()
    plot_security_implications()
