// Copyright 2023 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

// Some utilities for DifuzzRTL

#pragma once

#include <stdint.h>
#include <cassert>
#include <vector>

/////////
// The 3 functions below differ by the width of the cover port, given how Verilator represent different bit widths.
/////////

// Get the value of a subset of the input.
static uint32_t get_field_value_single32(uint32_t data, int start_index, int width)
{
    assert (start_index >= 0);
    assert (width >= 0);
    assert (width <= 20); // DiffuzzRTL defines the max hash width as 20 bits.
    assert (start_index + width <= 32);
    return (data >> start_index) & ((1 << width) - 1);
}

// Get the value of a subset of the input.
static uint32_t get_field_value_single64(uint64_t data, int start_index, int width)
{
    assert (start_index >= 0);
    assert (width >= 0);
    assert (width <= 20); // DiffuzzRTL defines the max hash width as 20 bits.
    assert (start_index + width <= 64);
    return (data >> start_index) & ((1 << width) - 1);
}

// Get the value of a subset of the input.
static uint32_t get_field_value_multi32(std::vector<uint32_t> data, int start_index, int width)
{
    assert (start_index >= 0);
    assert (width >= 0);
    assert (width <= 20); // DiffuzzRTL defines the max hash width as 20 bits.
    assert (start_index + width <= 32*data.size());

    // Discriminate whether the field is contained in a single word or multiple words (cannot be more than 2 because max 20 bits)
    if (start_index / 32 < (start_index + width) / 32) {
        assert ((start_index + width) / 32 == (start_index / 32) + 1);
        // The field is contained in multiple words.
        // Get the first word.
        uint32_t first_word = data[start_index / 32];
        // Get the second word.
        uint32_t second_word = data[(start_index + width) / 32];
        // Get the value of the field in the first word.
        uint32_t first_word_field = get_field_value_single32(first_word, start_index % 32, 32 - (start_index % 32));
        // Get the value of the field in the second word.
        uint32_t second_word_field = get_field_value_single32(second_word, 0, (start_index + width) % 32);
        // Concatenate the two values.
        return (second_word_field << (32 - (start_index % 32))) | first_word_field;
    } else {
        // The field is contained in a single word.
        return get_field_value_single32(data[start_index / 32], start_index % 32, width);
    }
}
