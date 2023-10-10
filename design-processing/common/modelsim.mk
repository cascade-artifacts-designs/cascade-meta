# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Make fragment that designs can include for common functionality regarding Modelsim

ifeq "" "$(CASCADE_ENV_SOURCED)"
$(error Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo)
endif

ifeq "" "$(CASCADE_META_ROOT)"
$(error Please re-source env.sh first, in the meta repo, and run from there, not this repo. See README.md in the meta repo)
endif

# Requires the env variables
# - MODELSIM_PATH_TO_BUILD_TCL: path to the ModelSim build TCL script
# - TOP_SOC: the top SoC name, for ibex_tiny_soc
# - CASCADE_DIR: the path of the design's cascade/ directory

FUZZCOREID ?= 0
VARIANT_ID ?=

MODELSIM_SV_VANILLA = generated/out/vanilla.sv dv/sv/tb_top.sv src/$(TOP_SOC).sv $(CASCADE_DESIGN_PROCESSING_ROOT)/common/src/sram_mem.sv

MODELSIM_WORKDIR = $(MODELSIM_WORKROOT)/$(TOP_SOC)$(VARIANT_ID)_$(FUZZCOREID)

build_vanilla_notrace_modelsim:       $(MODELSIM_PATH_TO_BUILD_TCL) $(MODELSIM_SV_VANILLA)     | $(MODELSIM_WORKDIR) modelsim traces logs
	cd $(MODELSIM_WORKDIR); CASCADE_DIR=$(CASCADE_DIR) TRACE=notrace   INSTRUMENTATION=vanilla CASCADE_META_COMMON=$(CASCADE_DESIGN_PROCESSING_ROOT)/common     MODELSIM_INCDIRSTR=$(MODELSIM_INCDIRSTR) MODELSIM_VLOG_COVERFLAG=$(MODELSIM_VLOG_COVERFLAG) TOP_SOC=$(TOP_SOC) VARIANT_ID=$(VARIANT_ID) SV_TOP=src/$(TOP_SOC).sv        SV_MEM=$(CASCADE_DESIGN_PROCESSING_ROOT)/common/src/sram_mem.sv SV_TB=dv/sv/tb_top.sv CURR_OPENTITAN_ROOT=$(CURR_OPENTITAN_ROOT) $(MODELSIM_VERSION) vsim -64 -vopt -c -do $<; cd -
	touch modelsim/vanilla.log
build_vanilla_trace_modelsim:         $(MODELSIM_PATH_TO_BUILD_TCL) $(MODELSIM_SV_VANILLA)     | $(MODELSIM_WORKDIR) modelsim traces logs
	cd $(MODELSIM_WORKDIR); CASCADE_DIR=$(CASCADE_DIR) TRACE=trace     INSTRUMENTATION=vanilla CASCADE_META_COMMON=$(CASCADE_DESIGN_PROCESSING_ROOT)/common     MODELSIM_INCDIRSTR=$(MODELSIM_INCDIRSTR) MODELSIM_VLOG_COVERFLAG=$(MODELSIM_VLOG_COVERFLAG) TOP_SOC=$(TOP_SOC) VARIANT_ID=$(VARIANT_ID) SV_TOP=src/$(TOP_SOC).sv        SV_MEM=$(CASCADE_DESIGN_PROCESSING_ROOT)/common/src/sram_mem.sv SV_TB=dv/sv/tb_top.sv CURR_OPENTITAN_ROOT=$(CURR_OPENTITAN_ROOT) $(MODELSIM_VERSION) vsim -64 -vopt -c -do $<; cd -
	touch modelsim/vanilla.log
build_vanilla_trace_fst_modelsim:     $(MODELSIM_PATH_TO_BUILD_TCL) $(MODELSIM_SV_VANILLA)     | $(MODELSIM_WORKDIR) modelsim traces logs
	cd $(MODELSIM_WORKDIR); CASCADE_DIR=$(CASCADE_DIR) TRACE=trace_fst INSTRUMENTATION=vanilla CASCADE_META_COMMON=$(CASCADE_DESIGN_PROCESSING_ROOT)/common     MODELSIM_INCDIRSTR=$(MODELSIM_INCDIRSTR) MODELSIM_VLOG_COVERFLAG=$(MODELSIM_VLOG_COVERFLAG) TOP_SOC=$(TOP_SOC) VARIANT_ID=$(VARIANT_ID) SV_TOP=src/$(TOP_SOC).sv        SV_MEM=$(CASCADE_DESIGN_PROCESSING_ROOT)/common/src/sram_mem.sv SV_TB=dv/sv/tb_top.sv CURR_OPENTITAN_ROOT=$(CURR_OPENTITAN_ROOT) $(MODELSIM_VERSION) vsim -64 -vopt -c -do $<; cd -
	touch modelsim/vanilla.log

RERUN_MODELSIM_TARGETS_NOTRACE   = rerun_vanilla_notrace_modelsim
RERUN_MODELSIM_TARGETS_TRACE     = rerun_vanilla_trace_modelsim
RERUN_MODELSIM_TARGETS_TRACE_FST = rerun_vanilla_trace_fst_modelsim
$(RERUN_MODELSIM_TARGETS_NOTRACE):   rerun_%_notrace_modelsim:   $(CASCADE_DESIGN_PROCESSING_ROOT)/common/modelsim/modelsim_run.tcl | $(MODELSIM_WORKDIR) modelsim traces logs
	cd $(MODELSIM_WORKDIR); TOP_SOC=$(TOP_SOC) CASCADE_DIR=$(CASCADE_DIR) VARIANT_ID=$(VARIANT_ID) TRACE=notrace   INSTRUMENTATION=$* TRACEFILE=$(TRACEFILE)                   MODELSIM_VSIM_COVERFLAG=$(MODELSIM_VSIM_COVERFLAG) MODELSIM_VSIM_COVERPATH=$(MODELSIM_VSIM_COVERPATH) python3 $(PATH_TO_INSTANCELIMIT_PY) --limit-instances=$(MODELSIM_MAX_INSTANCES) "$(MODELSIM_VERSION) vsim -64 -c -do $<"; cd -
$(RERUN_MODELSIM_TARGETS_TRACE):     rerun_%_trace_modelsim:     $(CASCADE_DESIGN_PROCESSING_ROOT)/common/modelsim/modelsim_run.tcl | $(MODELSIM_WORKDIR) modelsim traces logs
	cd $(MODELSIM_WORKDIR); TOP_SOC=$(TOP_SOC) CASCADE_DIR=$(CASCADE_DIR) VARIANT_ID=$(VARIANT_ID) TRACE=trace     INSTRUMENTATION=$* TRACEFILE=$(TRACEFILE)                   MODELSIM_VSIM_COVERFLAG=$(MODELSIM_VSIM_COVERFLAG) MODELSIM_VSIM_COVERPATH=$(MODELSIM_VSIM_COVERPATH) python3 $(PATH_TO_INSTANCELIMIT_PY) --limit-instances=$(MODELSIM_MAX_INSTANCES) "$(MODELSIM_VERSION) vsim -64 -c -do $<"; cd -
$(RERUN_MODELSIM_TARGETS_TRACE_FST): rerun_%_trace_fst_modelsim: $(CASCADE_DESIGN_PROCESSING_ROOT)/common/modelsim/modelsim_run.tcl | $(MODELSIM_WORKDIR) modelsim traces logs
	cd $(MODELSIM_WORKDIR); TOP_SOC=$(TOP_SOC) CASCADE_DIR=$(CASCADE_DIR) VARIANT_ID=$(VARIANT_ID) TRACE=trace_fst INSTRUMENTATION=$* TRACEFILE=$(TRACEFILE) MODELSIM_NOQUIT=1 MODELSIM_VSIM_COVERFLAG=$(MODELSIM_VSIM_COVERFLAG) MODELSIM_VSIM_COVERPATH=$(MODELSIM_VSIM_COVERPATH) python3 $(PATH_TO_INSTANCELIMIT_PY) --limit-instances=$(MODELSIM_MAX_INSTANCES) "$(MODELSIM_VERSION) vsim -64 -do $<"; cd -

$(MODELSIM_WORKDIR):
	mkdir -p $@
