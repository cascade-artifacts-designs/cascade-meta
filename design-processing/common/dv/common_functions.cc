// Copyright 2023 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

/* functions all designs can use in their C++ code */

#include <stdlib.h>
#include <stdio.h>

extern "C" {
  const char *Get_SRAM_ELF_object_filename(void);
  const char *Get_BootROM_ELF_object_filename(void);
  const char *cascade_getenv(char *varname);
}

extern "C" const char *Get_SRAM_ELF_object_filename(void)
{
    /* This function is used inside the ELF Loader code in ift_sram.sv
     * to determine the filename to load. The environment variable
     * SIMSRAMELF can be used to override the default.
     */
    const char* simsram_env = std::getenv("SIMSRAMELF");
    if(simsram_env == NULL) { fprintf(stderr, "SIMSRAMELF required\n"); exit(1); }
    return simsram_env;
}

extern "C" const char *Get_BootROM_ELF_object_filename(void)
{
    /* As above: allow ROM ELF filename to be overridden using
     * SIMROMELF environment variable. Used in ift_boot_rom_hdac.sv.
     */
    const char* simrom_env = std::getenv("SIMROMELF");
    if(simrom_env == NULL) { fprintf(stderr, "SIMROMELF required\n"); exit(1); }
    return simrom_env;
}

/* workaround for inconsistent prototype when getenv() is directly imported; we import cascade_getenv() instead */
extern "C" const char *cascade_getenv(char *varname)
{
    return (char *) getenv((char *) varname);
}
