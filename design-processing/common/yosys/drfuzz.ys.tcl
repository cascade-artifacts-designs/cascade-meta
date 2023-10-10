# Copyright 2023 Flavien Solt & Tobias Kovats, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

if { [info exists ::env(VERILOG_INPUT)] }    { set VERILOG_INPUT $::env(VERILOG_INPUT) }       else { puts "Please set VERILOG_INPUT environment variable"; exit 1 }
if { [info exists ::env(VERILOG_OUTPUT)] }   { set VERILOG_OUTPUT $::env(VERILOG_OUTPUT) }     else { puts "Please set VERILOG_OUTPUT environment variable"; exit 1 }
if { [info exists ::env(VERBOSE)]}   {set VERBOSE -verbose}     else { set VERBOSE ""}
if { [info exists ::env(SHALLOW)]}   {set SHALLOW -shallow}     else { set SHALLOW ""}
if { [info exists ::env(EXCLUDE_SIGNALS)]}   {set EXCLUDE_SIGNALS $::env(EXCLUDE_SIGNALS)}     else { set EXCLUDE_SIGNALS ""}
if { [info exists ::env(TOP_MODULE)] }       { set TOP_MODULE $::env(TOP_MODULE) }             else { puts "Please set TOP_MODULE environment variable"; exit 1 }
if { [info exists ::env(TOP_RESET)] }       { set TOP_RESET $::env(TOP_RESET) }             else { puts "Please set TOP_RESET environment variable"; exit 1 }

yosys read_verilog -defer -DSTOP_COND=0 -sv $VERILOG_INPUT
yosys hierarchy -top $TOP_MODULE -check
yosys proc
yosys pmuxtree
yosys opt -purge

yosys mark_resets $VERBOSE $SHALLOW $TOP_RESET
yosys mux_probes $VERBOSE $SHALLOW
yosys port_mux_probes $VERBOSE

yosys port_fuzz_inputs $VERBOSE $EXCLUDE_SIGNALS
yosys meta_reset $VERBOSE
yosys opt_clean

yosys write_verilog -simple-lhs -sv $VERILOG_OUTPUT
