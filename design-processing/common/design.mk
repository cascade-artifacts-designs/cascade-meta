# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Make fragment that designs can include for common functionality

ifeq "" "$(CASCADE_ENV_SOURCED)"
$(error Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo)
endif

ifeq "" "$(CASCADE_META_ROOT)"
$(error Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo)
endif

extract_timestamps:
	for log in generated/out/*.sv.log; \
    do echo $$log; \
    python3 $(CASCADE_META_ROOT)/python_scripts/extract_timestamps.py $$log split; \
    done

generated generated/common/dv generated/common generated/scattered generated/sv_sources generated/out generated/dv traces logs statistics build modelsim:
	mkdir -p $@

wave: | traces
	gtkwave -S scripts/gtkwave_init.tcl traces/sim.vcd
wave_fst: | traces
	gtkwave -S scripts/gtkwave_init.tcl traces/sim.fst
wave_fst_vanilla: | traces
	gtkwave -S scripts/gtkwave_init.tcl traces/sim_vanilla.fst

.PHONY: clean
clean:
	rm -rf build generated traces logs statistics ../Bender.lock fusesoc.conf modelsim
