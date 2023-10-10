# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# Find and replace in the DifuzzRTL elfs to trigger end of simulation
def find_pattern_in_object_file(file_path, pattern):
    pattern_length = len(pattern)
    byte_index_for_debug = 0
    with open(file_path, 'rb') as file:
        window = bytearray(pattern_length)
        while True:
            bytes_read = file.readinto(window)
            if bytes_read < pattern_length:
                # Reached end of file
                break
            if window == pattern:
                # Found the pattern
                print('byte_index_for_debug', hex(byte_index_for_debug))
                return True
            # Slide the window by one byte
            window[:-1] = window[1:]
            byte_index_for_debug += 1

    # Pattern not found
    return False
