# Modelsim build script
# Not suitable for designs with dependencies.

# TRACE must be `notrace` or `trace` or `trace_fst`

if { [info exists ::env(CASCADE_DIR)] }         { set CASCADE_DIR $::env(CASCADE_DIR)}                     else { puts "Please set CASCADE_DIR environment variable"; exit 1 }
if { [info exists ::env(MODELSIM_WORKROOT)] }   { set MODELSIM_WORKROOT $::env(MODELSIM_WORKROOT)}         else { puts "Please set MODELSIM_WORKROOT environment variable"; exit 1 }
if { [info exists ::env(INSTRUMENTATION)] }     { set INSTRUMENTATION $::env(INSTRUMENTATION)}             else { puts "Please set INSTRUMENTATION environment variable"; exit 1 }
if { [info exists ::env(TRACE)] }               { set TRACE $::env(TRACE)}                                 else { puts "Please set TRACE environment variable"; exit 1 }
if { [info exists ::env(CASCADE_META_COMMON)] } { set CASCADE_META_COMMON $::env(CASCADE_META_COMMON)}     else { puts "Please set CASCADE_META_COMMON environment variable"; exit 1 }
if { [info exists ::env(SV_TOP)] }              { set SV_TOP $CASCADE_DIR/$::env(SV_TOP) }                 else { puts "Please set SV_TOP environment variable"; exit 1 }
if { [info exists ::env(TOP_SOC)] }             { set TOP_SOC   $::env(TOP_SOC) }                          else { puts "Please set TOP_SOC environment variable"; exit 1 }
if { [info exists ::env(SV_MEM)] }              { set SV_MEM    $::env(SV_MEM) }                           else { puts "Please set SV_MEM environment variable"; exit 1 }
if { [info exists ::env(SV_TB)] }               { set SV_TB  $CASCADE_DIR/$::env(SV_TB) }                  else { puts "Please set SV_TB environment variable"; exit 1 }
if { [info exists ::env(FUZZCOREID)] }          { set FUZZCOREID  $::env(FUZZCOREID) }                     else { puts "No FUZZCOREID specified. Defaulting to 0."; set FUZZCOREID 0 }
# Useful if multiple designs have the same top soc name (typically rocket and boom)
if { [info exists ::env(VARIANT_ID)] }          { set VARIANT_ID  $::env(VARIANT_ID) }                     else { set VARIANT_ID "" }
# In case we want to have an include directory, MODELSIM_INCDIRSTR="+incdir+my/first/incdirectory +incdir+my/second/incdirectory" for example
if { [info exists ::env(MODELSIM_INCDIRSTR)] }  { set MODELSIM_INCDIRSTR  $::env(MODELSIM_INCDIRSTR) }     else { set MODELSIM_INCDIRSTR "" }
# Cover flag should be +cover or empty, or for example +cover=bcst
if { [info exists ::env(MODELSIM_VLOG_COVERFLAG)] }  { set MODELSIM_VLOG_COVERFLAG  $::env(MODELSIM_VLOG_COVERFLAG) }     else { set MODELSIM_VLOG_COVERFLAG "" }

set LIB ${MODELSIM_WORKROOT}/${TOP_SOC}${VARIANT_ID}_${FUZZCOREID}/work_${INSTRUMENTATION}_${TRACE}

vlog -64 -suppress 7061 -suppress 2583 -suppress 8386 -suppress 13314 -sv -work $LIB $MODELSIM_VLOG_COVERFLAG +define+RANDOMIZE_INIT=1 +define+STOP_COND=0 -ccflags '-std=c++11' $MODELSIM_INCDIRSTR -sv $CASCADE_DIR/generated/out/$INSTRUMENTATION.sv

vlog -64 -suppress 7061 -suppress 2583 -suppress 8386 -suppress 13314 -sv -work $LIB $MODELSIM_VLOG_COVERFLAG -ccflags '-std=c++11' -sv $SV_TOP
vlog -64 -suppress 7061 -suppress 2583 -suppress 8386 -suppress 13314 -suppress 7034 -sv -work $LIB $MODELSIM_VLOG_COVERFLAG -ccflags '-std=c++11' -sv $SV_MEM
vlog -64 -suppress 7061 -suppress 2583 -suppress 8386 -suppress 13314 -sv -work $LIB $MODELSIM_VLOG_COVERFLAG -ccflags '-std=c++11' -sv $SV_TB

vlog -64 -ccflags '-std=c++11' -work $LIB $MODELSIM_VLOG_COVERFLAG -dpiheader $CASCADE_META_COMMON/dv/elf.h $CASCADE_META_COMMON/dv/elfloader.cc $CASCADE_META_COMMON/dv/common_functions.cc

vlog -64 -sv -work $LIB $MODELSIM_VLOG_COVERFLAG $CASCADE_META_COMMON/dv/sv/rst_gen.sv $CASCADE_META_COMMON/dv/sv/clk_rst_gen.sv $SV_TOP

quit -f
