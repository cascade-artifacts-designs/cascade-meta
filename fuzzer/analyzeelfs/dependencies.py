from analyzeelfs.util import CASCADE_NUM_INITIAL_INSTR

import re

# The only instructions without destination register are:
# - stores
# - branches
# - fences, ecall, ebreak, mret, wfi
# - some CSR (write is not explicit in the assembly)

INTREG_ABINAMES = [
    'zero', 'ra', 'sp', 'gp', 'tp', 't0', 't1', 't2', 'fp', 's1', 'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11', 't3', 't4', 't5', 't6'
]

FPREG_ABINAMES = [
    'ft0', 'ft1', 'ft2', 'ft3', 'ft4', 'ft5', 'ft6', 'ft7', 'fs0', 'fs1', 'fa0', 'fa1', 'fa2', 'fa3', 'fa4', 'fa5', 'fa6', 'fa7', 'fs2', 'fs3', 'fs4', 'fs5', 'fs6', 'fs7', 'fs8', 'fs9', 'fs10', 'fs11', 'ft8', 'ft9', 'ft10', 'ft11'
]

# Return a tuple (reg_id, is_fp) for the given register name.
def regname_to_reg_id(regname: str):
    if regname in INTREG_ABINAMES:
        return (INTREG_ABINAMES.index(regname), False)
    elif regname == 's0':
        return (8, False)
    elif regname in FPREG_ABINAMES:
        return (FPREG_ABINAMES.index(regname), True)
    else:
        return None

# @param run_log the execution log without the register values.
# @param ages a list of ages, one age (int) for each instruction
def get_dependencies_per_instruction(spike_log: str, is_difuzzrtl: bool, instance_id_for_debug: int):

    reg_ages = [-1]*32 # reg_ages[0] should always be -1
    freg_ages = [-1]*32

    lines_treated = 0
    line_ages = []

    indices_cf_instructions = []

    is_currently_overhead = is_difuzzrtl

    all_lines = list(spike_log.split('\n'))
    if not is_difuzzrtl:
        all_lines = all_lines[CASCADE_NUM_INITIAL_INSTR:]

    for line_id, line in enumerate(spike_log.split('\n')):
        if not line.startswith('core   0: 0x'):
            if is_difuzzrtl:
                if re.search(r'_l\d+', line):
                    is_currently_overhead = False
                elif 'exception' in line:
                    is_currently_overhead = True
            continue

        if is_currently_overhead:
            assert is_difuzzrtl, "Overhead in non-difuzzrtl log should not be computed like this"
            continue

        assert reg_ages[0] == -1, "Register 0 age should always be -1"
        assert len(line_ages) == lines_treated, f"Line {lines_treated} has no age"
        lines_treated += 1

        # Parse the current line
        stripped_line = list(map(lambda s: s.replace(',', '').strip(), line.split()))
        curr_pc = int(stripped_line[2], 16)

        curr_instr_encoding = stripped_line[4:]
        curr_opcode = curr_instr_encoding[0]

        # Detect the input and output registerss
        in_reg_ids = []
        in_reg_is_fp = []
        out_reg = None
        is_out_reg_fp = None

        # Special case of branches
        if curr_opcode in ('beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu'):
            indices_cf_instructions.append(lines_treated - 1)
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[1]}"
            reg_id, is_fp = reg_id_pair
            assert not is_fp, f"Branch instruction with FP register: {curr_instr_encoding[1]}"
            in_reg_ids.append(reg_id)
            in_reg_is_fp.append(is_fp)
            del reg_id_pair, reg_id, is_fp

            reg_id_pair = regname_to_reg_id(curr_instr_encoding[2])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[2]}"
            reg_id, is_fp = reg_id_pair
            assert not is_fp, f"Branch instruction with FP register: {curr_instr_encoding[2]}"
            in_reg_ids.append(reg_id)
            in_reg_is_fp.append(is_fp)
            del reg_id_pair, reg_id, is_fp
        elif curr_opcode in ('fence', 'fence.i', 'ebreak', 'ecall', 'wfi') or 'prefetch' in curr_opcode:
            line_ages.append(None)
            continue
        elif 'csr' in curr_opcode:
            # Check whether there is an output register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[1])
            if reg_id_pair is not None:
                reg_id, is_fp = reg_id_pair
                assert not is_fp, f"CSR instruction with FP register: {curr_instr_encoding[1]}"
                if reg_id != 0:
                    # CSR read resets the register age
                    reg_ages[reg_id] = -1
                del reg_id, is_fp
            del reg_id_pair

            # Get the input register if any
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[-1])
            if reg_id_pair is not None:
                reg_id, is_fp = reg_id_pair
                assert not is_fp, f"CSR instruction with FP register: {curr_instr_encoding[1]}"
                if is_fp:
                    line_ages.append(freg_ages[reg_id]+1)
                else:
                    line_ages.append(reg_ages[reg_id]+1)
            else:
                line_ages.append(None)
            continue
        elif curr_opcode in ('sd', 'sw', 'sh', 'sb'):
            # Get the age of the input register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[2].split('(')[1][:-1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[2]}"
            reg_id, is_fp = reg_id_pair
            assert not is_fp, f"Store instruction with FP register: {curr_instr_encoding[2]}"
            line_ages.append(reg_ages[reg_id]+1)
            del reg_id_pair, reg_id, is_fp
            continue
        elif curr_opcode in ('ld', 'lw', 'lh', 'lb', 'lwu', 'lhu', 'lbu'):
            # Get the age of the input register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[2].split('(')[1][:-1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[2]}"
            input_reg_id, input_is_fp = reg_id_pair
            assert not input_is_fp, f"Load instruction with FP register: {curr_instr_encoding[2]}"
            line_ages.append(reg_ages[input_reg_id]+1)
            del reg_id_pair

            # Output register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[1]}"
            reg_id, is_fp = reg_id_pair
            assert not is_fp, f"Load instruction with FP register: {curr_instr_encoding[1]}"
            if reg_id != 0:
                reg_ages[reg_id] = reg_ages[input_reg_id]+1
            del reg_id_pair, reg_id, is_fp
            del input_reg_id, input_is_fp
            continue
        elif curr_opcode in ('fsd', 'fsw'):
            # Get the age of the input register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[2].split('(')[1][:-1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[2].split('(')[1][:-1]}"
            reg_id, is_fp = reg_id_pair
            assert not is_fp, f"Fstore instruction with FP register: {curr_instr_encoding[2].split('(')[1][:-1]}"
            line_ages.append(reg_ages[reg_id]+1)
            del reg_id_pair, reg_id, is_fp
            continue
        elif curr_opcode in ('fld', 'flw'):
            # Get the age of the input register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[2].split('(')[1][:-1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[2].split('(')[1][:-1]}"
            input_reg_id, input_is_fp = reg_id_pair
            assert not input_is_fp, f"Fload instruction with FP register: {curr_instr_encoding[2].split('(')[1][:-1]}"
            line_ages.append(reg_ages[input_reg_id]+1)
            del reg_id_pair

            # Output register
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[1]}"
            reg_id, is_fp = reg_id_pair
            assert is_fp, f"Fload instruction with int register: {curr_instr_encoding[1]}"
            freg_ages[reg_id] = reg_ages[input_reg_id]+1
            del reg_id_pair, reg_id, is_fp
            del input_reg_id, input_is_fp
            continue
        elif curr_opcode == 'xor' and len(curr_instr_encoding) == 4 and curr_instr_encoding[1] == curr_instr_encoding[2] and curr_instr_encoding[2] == curr_instr_encoding[3]:
            reg_id_pair = regname_to_reg_id(curr_instr_encoding[1])
            assert reg_id_pair is not None, f"Unknown register name: {curr_instr_encoding[1]}"
            reg_id, is_fp = reg_id_pair
            assert not is_fp, f"Xor instruction with float register: {curr_instr_encoding[1]}"
            line_ages.append(reg_ages[reg_id]+1)
            if reg_id != 0:
                reg_ages[reg_id] = -1
            continue
        else:
            if curr_opcode == 'jalr':
                indices_cf_instructions.append(lines_treated - 1)
            if len(curr_instr_encoding) > 1:
                reg_id_pair = regname_to_reg_id(curr_instr_encoding[1])
                if reg_id_pair is None:
                    # Can happen for JAL
                    assert curr_instr_encoding[1] == 'pc', f"Unknown register name: {curr_instr_encoding[1]}"
                else:
                    out_reg, is_out_reg_fp = reg_id_pair
            for i in range(2, len(curr_instr_encoding)):
                if '(' in curr_instr_encoding[i]:
                    curr_instr_encoding[i] = curr_instr_encoding[i].split('(')[1].split(')')[0]
                reg_id_pair = regname_to_reg_id(curr_instr_encoding[i])
                if reg_id_pair is not None:
                    in_reg, is_in_reg_fp = reg_id_pair
                    in_reg_ids.append(in_reg)
                    in_reg_is_fp.append(is_in_reg_fp)
                    del reg_id_pair, in_reg, is_in_reg_fp

        # Compute the max age of input registers
        max_age_of_input_regs = 0
        for i in range(len(in_reg_ids)):
            if in_reg_is_fp[i]:
                max_age_of_input_regs = max(max_age_of_input_regs, freg_ages[in_reg_ids[i]])
            else:
                max_age_of_input_regs = max(max_age_of_input_regs, reg_ages[in_reg_ids[i]])
        line_ages.append(max_age_of_input_regs+1)
        # Update the age of the output register if applicable
        if out_reg is not None and (out_reg != 0 or is_out_reg_fp):
            if is_out_reg_fp:
                freg_ages[out_reg] = max_age_of_input_regs + 1
            else:
                reg_ages[out_reg] = max_age_of_input_regs + 1

    return line_ages, indices_cf_instructions