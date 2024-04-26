# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

# This script is responsible for generating the basic blocks

from params.runparams import DO_ASSERT
from common.spike import SPIKE_STARTADDR
from rv.csrids import CSR_IDS
from params.fuzzparams import BRANCH_TAKEN_PROBA, LIMIT_MEM_SATURATION_RATIO, RANDOM_DATA_BLOCK_MIN_SIZE_BYTES, RANDOM_DATA_BLOCK_MAX_SIZE_BYTES
from cascade.randomize.createcfinstr import create_instr, create_regfsm_instrobjs
from cascade.randomize.pickinstrtype import gen_next_instrstr_from_isaclass
from cascade.randomize.pickisainstrclass import gen_next_isainstrclass, ISAInstrClass
from cascade.randomize.pickmemop import pick_memop_addr, get_alignment_bits, is_instrstr_load
from cascade.randomize.pickfpuop import gen_fpufsm_instrs
from cascade.randomize.pickexceptionop import gen_exception_instr, gen_tvecfill_instr, gen_epcfill_instr, gen_medeleg_instr, gen_ppfill_instrs
from cascade.randomize.pickrandomcsrop import gen_random_csr_op
from cascade.randomize.pickprivilegedescentop import gen_priv_descent_instr
from cascade.cfinstructionclasses import is_placeholder, JALInstruction, JALRInstruction, BranchInstruction, ExceptionInstruction, TvecWriterInstruction, EPCWriterInstruction, GenericCSRWriterInstruction, MisalignedMemInstruction, PrivilegeDescentInstruction, EcallEbreakInstruction, SimpleExceptionEncapsulator, CSRRegInstruction
from cascade.util import get_range_bits_per_instrclass, IntRegIndivState, BASIC_BLOCK_MIN_SPACE, INSTRUCTIONS_BY_ISA_CLASS
from cascade.finalblock import get_finalblock_max_size,finalblock
from cascade.initialblock import gen_initial_basic_block
from cascade.blacklist import blacklist_changing_instructions, blacklist_final_block, blacklist_context_setter
from cascade.privilegestate import PrivilegeStateEnum

import random

# Given the provided control flow instruction, finds a location for a new block, but does not allocate it.
# @return False if could not find a next bb address
def gen_next_bb_addr(fuzzerstate, isa_class: ISAInstrClass, curr_addr: int):
    range_bits_each_direction = get_range_bits_per_instrclass(isa_class)
    # We must select the next basic block address before the resolution
    fuzzerstate.next_bb_addr = fuzzerstate.memview.gen_random_free_addr(4, BASIC_BLOCK_MIN_SPACE, curr_addr - (1 << range_bits_each_direction), curr_addr + (1 << range_bits_each_direction))
    # If we could not find a new address where to place the next basic block, then return and consider this stage complete.
    if fuzzerstate.next_bb_addr is None:
        return False
    return True

# The first BASIC_BLOCK_MIN_SPACE must be pre-allocated. The rationale is that we want to pre-allocate at least for the first basic block, to prevent the store data from landing exactly there.
# @return True iff the creation is successful
def gen_basicblock(fuzzerstate):
    fuzzerstate.init_new_bb() # Update fuzzer state to support a new basic block

    # This points to the first address after the current basic block allocation. The block allocation takes 16 bytes in advance, to avoid storing and then not being able to continue expanding the basic block.
    curr_alloc_cursor = fuzzerstate.curr_bb_start_addr + BASIC_BLOCK_MIN_SPACE

    curr_isa_class = None # This is used in case there is only space for control flow

    # For Amo Synchronize updates ; gzhinsert 
    fence_need = False

    # We stop the instruction generation either when there is no more space available, or when we encounter an end-of-state instruction
    while fuzzerstate.memview.get_available_contig_space(curr_alloc_cursor)-4 > BASIC_BLOCK_MIN_SPACE:

        # Allocate the next 4 bytes
        fuzzerstate.memview.alloc_mem_range(curr_alloc_cursor, curr_alloc_cursor+4)
        curr_alloc_cursor += 4
        curr_addr = fuzzerstate.curr_bb_start_addr + 4*len(fuzzerstate.instr_objs_seq[-1])

        # Synchronize updates
        if fence_need:
            fuzzerstate.instr_objs_seq[-1].append(create_instr("fence", fuzzerstate, curr_addr))
            fence_need = False
            continue

        # Get the next instruction class
        if fuzzerstate.has_reached_max_instr_num():
            curr_isa_class = ISAInstrClass.JAL
        else:
            curr_isa_class = gen_next_isainstrclass(fuzzerstate)

        # If this is an instruction that influences offset register states
        if curr_isa_class == ISAInstrClass.REGFSM:
            new_instrobjs = create_regfsm_instrobjs(fuzzerstate)
            fuzzerstate.instr_objs_seq[-1].append(new_instrobjs[0])

            # For consumers, we may need to insert one more instruction
            for next_instrobj_id in range(1, len(new_instrobjs)):
                fuzzerstate.memview.alloc_mem_range(curr_alloc_cursor, curr_alloc_cursor+4)
                curr_alloc_cursor += 4
                fuzzerstate.instr_objs_seq[-1].append(new_instrobjs[next_instrobj_id])
            del new_instrobjs # For safety, we prevent accidental reuse of this variable
            continue
        # If this is an FPU enable-disable instruction or a rounding mode change
        elif curr_isa_class == ISAInstrClass.FPUFSM:
            new_instrobjs = gen_fpufsm_instrs(fuzzerstate)
            if len(new_instrobjs) == 1: # Equivalent to FPU enable/disable
                fuzzerstate.fpuendis_coords.append((len(fuzzerstate.instr_objs_seq)-1, len(fuzzerstate.instr_objs_seq[-1])))
            if DO_ASSERT:
                assert len(new_instrobjs) * 4 < BASIC_BLOCK_MIN_SPACE # NO_COMPRESSED
            fuzzerstate.instr_objs_seq[-1] += new_instrobjs
            if len(new_instrobjs) > 1:
                fuzzerstate.memview.alloc_mem_range(curr_alloc_cursor, curr_alloc_cursor+4*(len(new_instrobjs)-1)) # NO_COMPRESSED
                curr_alloc_cursor += 4*(len(new_instrobjs)-1) # NO_COMPRESSED
            del new_instrobjs # For safety, we prevent accidental reuse of this variable
            continue

        # If this is a privilege descent instruction or an mpp/spp write instruction
        elif curr_isa_class == ISAInstrClass.DESCEND_PRV:
            # print('Priv descent at addr', hex(curr_addr), 'privstate', fuzzerstate.privilegestate.privstate)
            new_instrobj = gen_priv_descent_instr(fuzzerstate)
            # print('  New privstate', fuzzerstate.privilegestate.privstate)

            # Create space for the next basic block.
            if not gen_next_bb_addr(fuzzerstate, curr_isa_class, curr_addr):
                # Abort the bb
                fuzzerstate.instr_objs_seq.pop()
                fuzzerstate.bb_start_addr_seq.pop()
                fuzzerstate.intregpickstate.restore_state(fuzzerstate.saved_reg_states[-1])
                return False
            fuzzerstate.instr_objs_seq[-1].append(new_instrobj)
            del new_instrobj
            return True

        elif curr_isa_class == ISAInstrClass.PPFSM:
            new_instrobjs = gen_ppfill_instrs(fuzzerstate)
            if DO_ASSERT:
                assert len(new_instrobjs) * 4 < BASIC_BLOCK_MIN_SPACE # NO_COMPRESSED
            fuzzerstate.instr_objs_seq[-1] += new_instrobjs
            if len(new_instrobjs) > 1:
                fuzzerstate.memview.alloc_mem_range(curr_alloc_cursor, curr_alloc_cursor+4*(len(new_instrobjs)-1)) # NO_COMPRESSED
                curr_alloc_cursor += 4*(len(new_instrobjs)-1) # NO_COMPRESSED
            del new_instrobjs # For safety, we prevent accidental reuse of this variable
            continue

        elif curr_isa_class == ISAInstrClass.EXCEPTION:
            # Create space for the next basic block.
            if not gen_next_bb_addr(fuzzerstate, curr_isa_class, curr_addr):
                # Abort the bb
                fuzzerstate.instr_objs_seq.pop()
                fuzzerstate.bb_start_addr_seq.pop()
                fuzzerstate.intregpickstate.restore_state(fuzzerstate.saved_reg_states[-1])
                return False
            # print('exception at addr', hex(curr_addr), 'privstate', fuzzerstate.privilegestate.privstate)
            new_instrobj = gen_exception_instr(fuzzerstate)
            # print('  New priv:', fuzzerstate.privilegestate.privstate)
            fuzzerstate.instr_objs_seq[-1].append(new_instrobj)
            del new_instrobj # For safety, we prevent accidental reuse of this variable
            return True

        # Discriminate non-taken branches
        fuzzerstate.curr_branch_taken = False
        if curr_isa_class == ISAInstrClass.BRANCH:
            fuzzerstate.curr_branch_taken = random.random() < BRANCH_TAKEN_PROBA

        # Compute the address of the next basic block if we are exiting the current
        if curr_isa_class in (ISAInstrClass.JAL, ISAInstrClass.JALR) or fuzzerstate.curr_branch_taken:
            # If this was a JAL due to reaching the max authorized number of instructions
            if curr_isa_class == ISAInstrClass.JAL and fuzzerstate.has_reached_max_instr_num():
                gen_bb_addr_ret = gen_next_bb_addr(fuzzerstate, curr_isa_class, curr_addr)
                assert gen_bb_addr_ret, "We should have returned earlier if we reached the max number of instructions."
                instr_str = gen_next_instrstr_from_isaclass(curr_isa_class, fuzzerstate)
                assert instr_str == 'jal', f"Unexpected instruction string `{instr_str}`"
                fuzzerstate.instr_objs_seq[-1].append(create_instr("jal", fuzzerstate, curr_addr))
                return True
            # Gen the next bb addr
            if not gen_next_bb_addr(fuzzerstate, curr_isa_class, curr_addr):
                # Abort the bb
                fuzzerstate.instr_objs_seq.pop()
                fuzzerstate.bb_start_addr_seq.pop()
                fuzzerstate.intregpickstate.restore_state(fuzzerstate.saved_reg_states[-1])
                return False

        assert not fuzzerstate.has_reached_max_instr_num(), "We should have returned earlier if we reached the max number of instructions."

        # Get an instruction string for this ISA class
        # We have some special cases for instructions that are not entirely characterized by an instruction string
        next_instr = None # Just a safety measure to ensure we don't use a stale one by mistake
        if curr_isa_class == ISAInstrClass.MEDELEG:
            if DO_ASSERT:
                assert fuzzerstate.privilegestate.privstate == PrivilegeStateEnum.MACHINE, "medeleg can only be used in machine mode, and we do not an exception here."
            next_instr = gen_medeleg_instr(fuzzerstate)
        elif curr_isa_class == ISAInstrClass.TVECFSM:
            # print('tvec writer at addr', hex(curr_addr), 'privstate', fuzzerstate.privilegestate.privstate)
            next_instr = gen_tvecfill_instr(fuzzerstate)
        elif curr_isa_class == ISAInstrClass.EPCFSM:
            next_instr = gen_epcfill_instr(fuzzerstate)
        elif curr_isa_class == ISAInstrClass.RANDOM_CSR:
            next_instr = gen_random_csr_op(fuzzerstate)
        elif curr_isa_class == ISAInstrClass.AMO or curr_isa_class == ISAInstrClass.AMO64:
            
            #TO ensure amo is NOT last instr , for fence instr
            if fuzzerstate.memview.get_available_contig_space(curr_alloc_cursor)-4 > BASIC_BLOCK_MIN_SPACE:
                instr_str = gen_next_instrstr_from_isaclass(curr_isa_class, fuzzerstate)
                next_instr = create_instr(instr_str, fuzzerstate, curr_addr)
                #TODO 暂时禁用LR指令（原因：DUT在LR指令后不能跟随fence指令）
                while True:
                    if 'lr' in instr_str:
                        #print("next_instr:",instr_str)
                        instr_str = gen_next_instrstr_from_isaclass(curr_isa_class, fuzzerstate)
                        next_instr = create_instr(instr_str, fuzzerstate, curr_addr)
                    else:
                        break
            #print("next_instr:",next_instr)
                fence_need = True
            else:
                fuzzerstate.instr_objs_seq[-1].append(create_instr("fence", fuzzerstate, curr_addr))
                continue
        else:
            instr_str = gen_next_instrstr_from_isaclass(curr_isa_class, fuzzerstate)
            next_instr = create_instr(instr_str, fuzzerstate, curr_addr)
        fuzzerstate.instr_objs_seq[-1].append(next_instr)

        if curr_isa_class in (ISAInstrClass.JAL, ISAInstrClass.JALR) or fuzzerstate.curr_branch_taken:
            return True
        # If this is the end of the basic block, then we quit this function. The part after the loop is reserved for cases where we need to urgently change control flow.

    # This is reached if we need to urgently jump to the next basic block.
    # The algorithm is the following: if there is a possibility to jump immediately, then do so. Else, prepare the registers as fast as possible.

    curr_isa_class = random.choices([ISAInstrClass.JAL, ISAInstrClass.JALR, ISAInstrClass.BRANCH], [1, 1, 1], k=1)[0]
    curr_addr = fuzzerstate.curr_bb_start_addr + 4*len(fuzzerstate.instr_objs_seq[-1])

    # No need for any preparation if jal, because it has no true dependency
    if curr_isa_class in (ISAInstrClass.JAL, ISAInstrClass.BRANCH):
        # Gen the next bb addr
        if not gen_next_bb_addr(fuzzerstate, curr_isa_class, curr_addr):
            # Abort the bb
            fuzzerstate.instr_objs_seq.pop()
            fuzzerstate.bb_start_addr_seq.pop()
            fuzzerstate.intregpickstate.restore_state(fuzzerstate.saved_reg_states[-1])
            return False
        if curr_isa_class == ISAInstrClass.JAL:
            fuzzerstate.instr_objs_seq[-1].append(create_instr("jal", fuzzerstate, curr_addr))
        elif curr_isa_class == ISAInstrClass.BRANCH:
            fuzzerstate.curr_branch_taken = True
            # The branch type does not batter because it will be re-determined once the operand values are known
            fuzzerstate.instr_objs_seq[-1].append(create_instr("bne", fuzzerstate, curr_addr))
        else:
            raise ValueError(f"Unexpected isa class `{curr_isa_class}`")

    else:
        # For JALR, bring some reg to maturity, and then insert the control flow instruction
        if DO_ASSERT:
            assert curr_isa_class == ISAInstrClass.JALR

        fuzzerstate.intregpickstate.bring_some_reg_to_state(IntRegIndivState.CONSUMED, fuzzerstate)
        curr_addr = fuzzerstate.curr_bb_start_addr + 4*len(fuzzerstate.instr_objs_seq[-1]) # NO_COMPRESSED

        # Gen the next bb addr
        if not gen_next_bb_addr(fuzzerstate, curr_isa_class, curr_addr):
            # Abort the bb
            fuzzerstate.instr_objs_seq.pop()
            fuzzerstate.bb_start_addr_seq.pop()
            fuzzerstate.intregpickstate.restore_state(fuzzerstate.saved_reg_states[-1])
            return False
        fuzzerstate.instr_objs_seq[-1].append(create_instr('jalr', fuzzerstate, curr_addr))

# This must be done early, say, just after generating the first basic block, to ensure that we have enough space.
def gen_random_data_block(fuzzerstate):
    lenbytes = random.randrange(RANDOM_DATA_BLOCK_MIN_SIZE_BYTES, RANDOM_DATA_BLOCK_MAX_SIZE_BYTES)
    fuzzerstate.random_data_block_start_addr = fuzzerstate.memview.gen_random_free_addr(2, lenbytes, 0, fuzzerstate.memsize)
    fuzzerstate.random_data_block_end_addr = fuzzerstate.random_data_block_start_addr + lenbytes
    if DO_ASSERT:
        assert fuzzerstate.random_data_block_start_addr is not None, f"Maybe you should create the random data block earlier in the creation of the test case."
    fuzzerstate.memview.alloc_mem_range(fuzzerstate.random_data_block_start_addr, fuzzerstate.random_data_block_end_addr)
    # Generate the random data
    for _ in range(fuzzerstate.random_data_block_start_addr, fuzzerstate.random_data_block_end_addr, 4):
        fuzzerstate.random_block_content4by4bytes.append(random.randrange(0, 2**32))

# This must be done early, say, just after generating the first basic block, to ensure that we have enough space.
def alloc_final_basic_block(fuzzerstate):
    lenbytes = get_finalblock_max_size() * 4 # NO_COMPRESSED
    fuzzerstate.final_bb_base_addr = fuzzerstate.memview.gen_random_free_addr(2, lenbytes, 0, fuzzerstate.memsize)
    if DO_ASSERT:
        assert fuzzerstate.final_bb_base_addr is not None, f"Maybe you should create the final basic block earlier in the creation of the test case."
    fuzzerstate.memview.alloc_mem_range(fuzzerstate.final_bb_base_addr, fuzzerstate.final_bb_base_addr+lenbytes)

# This must be done early, say, just after generating the final basic block, to ensure that we have enough space.
def alloc_context_saver_bb(fuzzerstate):
    # For the contextsaver, we first want to know the base address before we generate the basic block because we do loads and stores, which require absolute addresses.
    fuzzerstate.ctxsv_bb_base_addr = fuzzerstate.memview.gen_random_free_addr(2, fuzzerstate.ctxsv_size_upperbound, 0, fuzzerstate.memsize)
    if fuzzerstate.ctxsv_bb_base_addr is None:
        return False
    fuzzerstate.memview.alloc_mem_range(fuzzerstate.ctxsv_bb_base_addr, fuzzerstate.ctxsv_bb_base_addr+fuzzerstate.ctxsv_size_upperbound)
    return True

# This function is a bit tricky. The objective is to remove the final basic blocks until we find a basic block that can reach the final block. For example, a far JAL may not be able to each the final block.
# This should be done once all the basic blocks have been inserted until a stop condition was met, such as no more space found for another bb, or memory usage above a certain percentage.
# @return True iff the insertion succeeded. If False, the whole test case generation is considered failed.
def pop_last_bbs_to_connect_with_final_block(fuzzerstate):
    popped_at_least_once = False
    while fuzzerstate.instr_objs_seq:
        # Check whether the last element can target the final bb
        last_cf_instr_base_addr = fuzzerstate.bb_start_addr_seq[-1] + (len(fuzzerstate.instr_objs_seq[-1])-1) * 4 # NO_COMPRESSED
        if isinstance(fuzzerstate.instr_objs_seq[-1][-1], JALInstruction):
            range_bits = get_range_bits_per_instrclass(ISAInstrClass.JAL)
        elif isinstance(fuzzerstate.instr_objs_seq[-1][-1], JALRInstruction):
            range_bits = get_range_bits_per_instrclass(ISAInstrClass.JALR)
        elif isinstance(fuzzerstate.instr_objs_seq[-1][-1], BranchInstruction) and fuzzerstate.instr_objs_seq[-1][-1].plan_taken:
            range_bits = get_range_bits_per_instrclass(ISAInstrClass.BRANCH)
        elif isinstance(fuzzerstate.instr_objs_seq[-1][-1], PrivilegeDescentInstruction):
            range_bits = get_range_bits_per_instrclass(ISAInstrClass.DESCEND_PRV)
        elif isinstance(fuzzerstate.instr_objs_seq[-1][-1], ExceptionInstruction):
            range_bits = get_range_bits_per_instrclass(ISAInstrClass.EXCEPTION)
        else:
            raise ValueError(f"Unexpectedly got instruction `{fuzzerstate.instr_objs_seq[-1][-1]}`")
        if fuzzerstate.final_bb_base_addr >= last_cf_instr_base_addr - (1 << range_bits) and fuzzerstate.final_bb_base_addr < last_cf_instr_base_addr + (1 << range_bits):
            # The last basic block of the series is a candidate for jumping to the final block.
            # The target address of the last cf instruction will be injected later.
            if popped_at_least_once:
                fuzzerstate.intregpickstate.restore_state(fuzzerstate.saved_reg_states[-1])
            return True
        # else, in case the last block could not reach the final block, then we discard it and try with the previous one.
        popped_at_least_once = True
        fuzzerstate.instr_objs_seq.pop()
        fuzzerstate.bb_start_addr_seq.pop()
        fuzzerstate.saved_reg_states.pop()
    return False

# @return a list of addresses for the memory operations, in their order of occurrence
def gen_memop_addrs(fuzzerstate):
    ret = []
    for bb_instrlist in fuzzerstate.instr_objs_seq:
        for bb_instr in bb_instrlist:
            if is_placeholder(bb_instr):
                continue
            elif bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEM] or bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEM64] or bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEMFPU] or bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEMFPUD]:
                ret.append(pick_memop_addr(fuzzerstate, is_instrstr_load(bb_instr.instr_str), get_alignment_bits(bb_instr.instr_str)))
    return ret

# @brief This function generates the producer_id_to_tgtaddr dictionary and the producer_id_to_noreloc_spike dictionaries.
def gen_producer_id_to_tgtaddr(fuzzerstate, memop_addrs):
    # Two steps. First, generate producer_id_to_tgtaddr. Then, use it to populate the producers with target addresses. The second step is done in another function.

    # Step 1
    index_in_memaddr_array = 0
    index_in_bb_start_addr_seq = 1 # This variable lets us know to which address we wish to jump when some CF instruction is taken
    producer_id_to_tgtaddr = dict() # producer_id_to_tgtaddr[producer_id] = tgt_addr
    producer_id_to_noreloc_spike = dict() # producer_id_to_noreloc_spike[producer_id] = bool, where bool is true if the value we want to specify should not be relocated for spike

    # To facilitate backward propagation of addresses during exceptions, we recall the tvec writes.
    # When they are consumed, we forget them.
    last_mtvec = None # last_mtvec is a tuple (bb_id, instr_id)
    last_stvec = None # last_stvec is a tuple (bb_id, instr_id)
    last_mepc = None  # last_mepc  is a tuple (bb_id, instr_id)
    last_sepc = None  # last_sepc  is a tuple (bb_id, instr_id)

    for bb_id, bb_instrlist in enumerate(fuzzerstate.instr_objs_seq):
        for bb_instr_id, bb_instr in enumerate(bb_instrlist):

            ###
            # For producer_id_to_noreloc_spike
            ###

            if isinstance(bb_instr, GenericCSRWriterInstruction) and bb_instr.csr_instr.csr_id == CSR_IDS.MEDELEG:
                producer_id_to_noreloc_spike[bb_instr.producer_id] = True

            ###
            # First check for instructions that do not have an instruction string, such as placeholder instructions or some CSR write instructions.
            ###

            if is_placeholder(bb_instr):
                continue

            # To facilitate backward propagation of addresses during exceptions
            if isinstance(bb_instr, TvecWriterInstruction):
                if bb_instr.is_mtvec:
                    last_mtvec = (bb_id, bb_instr_id)
                else:
                    last_stvec = (bb_id, bb_instr_id)
                continue

            # To facilitate backward propagation of addresses during trap returns
            if isinstance(bb_instr, EPCWriterInstruction):
                if bb_instr.is_mepc:
                    last_mepc = (bb_id, bb_instr_id)
                else:
                    last_sepc = (bb_id, bb_instr_id)
                continue

            # To facilitate backward propagation of addresses during exceptions
            if isinstance(bb_instr, GenericCSRWriterInstruction):
                if DO_ASSERT:
                    assert bb_instr.producer_id == -1 or not bb_instr.producer_id in producer_id_to_tgtaddr, "producer_id {} already in producer_id_to_tgtaddr".format(bb_instr.producer_id)
                producer_id_to_tgtaddr[bb_instr.producer_id] = bb_instr.val_to_write_cpu
                continue

            # In case of a privilege descent instruction
            if isinstance(bb_instr, PrivilegeDescentInstruction):
                # Extremely similar to handling exception instruction below
                # Check that a corresponding xepc has been setup
                if DO_ASSERT:
                    assert (bb_instr.is_mret and last_mepc) or (not bb_instr.is_mret and last_sepc), "No epc found for privilege descent instruction. Values are: last_mepc = {}, last_sepc = {}, bb_instr.is_mret = {}".format(last_mepc, last_sepc, bb_instr.is_mret)

                # Get the epc instr's producer id
                if bb_instr.is_mret:
                    epc_producer_id = fuzzerstate.instr_objs_seq[last_mepc[0]][last_mepc[1]].producer_id
                else:
                    epc_producer_id = fuzzerstate.instr_objs_seq[last_sepc[0]][last_sepc[1]].producer_id

                # Get the next bb's start address
                if index_in_bb_start_addr_seq == len(fuzzerstate.bb_start_addr_seq):
                    if DO_ASSERT:
                        assert fuzzerstate.final_bb_base_addr is not None and fuzzerstate.final_bb_base_addr >= 0
                    addr = fuzzerstate.final_bb_base_addr # Final basic block
                else:
                    addr = fuzzerstate.bb_start_addr_seq[index_in_bb_start_addr_seq]
                    index_in_bb_start_addr_seq += 1
                if DO_ASSERT:
                    assert epc_producer_id > 0

                if DO_ASSERT:
                    assert epc_producer_id == -1 or not epc_producer_id in producer_id_to_tgtaddr, "producer_id {} already in producer_id_to_tgtaddr".format(bb_instr.producer_id)
                producer_id_to_tgtaddr[epc_producer_id] = addr
                # Do not use twice the same epc value because we want to jump to a new basic block.
                if bb_instr.is_mret:
                    last_mepc = None
                else:
                    last_sepc = None

            # In case of an exception instruction, find the last corresponding tvec and transmit the target address
            if isinstance(bb_instr, ExceptionInstruction):
                # Check that a corresponding tvec has been setup
                if DO_ASSERT:
                    assert (bb_instr.is_mtvec and last_mtvec) or (not bb_instr.is_mtvec and last_stvec), "No tvec found for exception instruction. Values are: last_mtvec = {}, last_stvec = {}, bb_instr.is_mtvec = {}".format(last_mtvec, last_stvec, bb_instr.is_mtvec)

                # Get the tvec instr's producer id
                if bb_instr.is_mtvec:
                    tvec_producer_id = fuzzerstate.instr_objs_seq[last_mtvec[0]][last_mtvec[1]].producer_id
                else:
                    tvec_producer_id = fuzzerstate.instr_objs_seq[last_stvec[0]][last_stvec[1]].producer_id

                # Get the next bb's start address
                if index_in_bb_start_addr_seq == len(fuzzerstate.bb_start_addr_seq):
                    if DO_ASSERT:
                        assert fuzzerstate.final_bb_base_addr is not None and fuzzerstate.final_bb_base_addr >= 0
                    addr = fuzzerstate.final_bb_base_addr # Final basic block
                else:
                    addr = fuzzerstate.bb_start_addr_seq[index_in_bb_start_addr_seq]
                    index_in_bb_start_addr_seq += 1
                if DO_ASSERT:
                    assert tvec_producer_id > 0

                if DO_ASSERT:
                    assert tvec_producer_id == -1 or not tvec_producer_id in producer_id_to_tgtaddr, "producer_id {} already in producer_id_to_tgtaddr".format(bb_instr.producer_id)
                producer_id_to_tgtaddr[tvec_producer_id] = addr

                # Do not use twice the same tvec value because we want to jump to a new basic block.
                if bb_instr.is_mtvec:
                    last_mtvec = None
                else:
                    last_stvec = None

                # Some exceptions also require their own produced register, not only for tvec but also to make a targeted memory operation
                if bb_instr.producer_id is not None:
                    del addr
                    if isinstance(bb_instr, MisalignedMemInstruction):
                        addr = bb_instr.misaligned_addr
                    else:
                        raise Exception("We expected only MisalignedMemInstruction to have a producer_id.")

                    if DO_ASSERT:
                        assert bb_instr.producer_id == -1 or not bb_instr.producer_id in producer_id_to_tgtaddr, "producer_id {} already in producer_id_to_tgtaddr".format(bb_instr.producer_id)
                    producer_id_to_tgtaddr[bb_instr.producer_id] = addr

            ###
            # Else, check for "traditional" instructions, which have an instruction string.
            ###

            if bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.JALR]:
                if index_in_bb_start_addr_seq == len(fuzzerstate.bb_start_addr_seq):
                    if DO_ASSERT:
                        assert fuzzerstate.final_bb_base_addr is not None and fuzzerstate.final_bb_base_addr >= 0
                    addr = fuzzerstate.final_bb_base_addr # Final basic block
                else:
                    addr = fuzzerstate.bb_start_addr_seq[index_in_bb_start_addr_seq]
                    index_in_bb_start_addr_seq += 1
                if DO_ASSERT:
                    assert bb_instr.producer_id > 0
                    assert bb_instr.producer_id == -1 or not bb_instr.producer_id in producer_id_to_tgtaddr, "producer_id {} already in producer_id_to_tgtaddr".format(bb_instr.producer_id)
                producer_id_to_tgtaddr[bb_instr.producer_id] = addr

            elif bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEM] or bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEM64] or bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEMFPU] or bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.MEMFPUD]:
                if DO_ASSERT:
                    assert bb_instr.producer_id == -1 or not bb_instr.producer_id in producer_id_to_tgtaddr, "producer_id {} already in producer_id_to_tgtaddr".format(bb_instr.producer_id)
                producer_id_to_tgtaddr[bb_instr.producer_id] = memop_addrs[index_in_memaddr_array]
                index_in_memaddr_array += 1

            elif bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.JAL] or (bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.BRANCH] and bb_instr.plan_taken):
                # If this is the last before the final block, we need to steer toward the final block.
                if index_in_bb_start_addr_seq == len(fuzzerstate.bb_start_addr_seq):
                    if DO_ASSERT:
                        assert fuzzerstate.final_bb_base_addr is not None and fuzzerstate.final_bb_base_addr >= 0
                    curr_addr = fuzzerstate.bb_start_addr_seq[bb_id] + bb_instr_id * 4 # NO_COMPRESSED
                    bb_instr.imm = fuzzerstate.final_bb_base_addr - curr_addr
                index_in_bb_start_addr_seq += 1

            elif bb_instr.instr_str in INSTRUCTIONS_BY_ISA_CLASS[ISAInstrClass.SPECIAL]:
                pass

    if DO_ASSERT:
        index_in_memaddr_array = len(memop_addrs)

    return producer_id_to_tgtaddr, producer_id_to_noreloc_spike

# @brief Generates a series of basic blocks.
# Does not transmit the next bb address to the control flow instructions.
# @param fuzzerstate a freshly created fuzzerstate.
def gen_basicblocks(fuzzerstate):
    # Until the generation succeeds
    while True:

        fuzzerstate.reset()
        gen_initial_basic_block(fuzzerstate, SPIKE_STARTADDR)
        fuzzerstate.saved_reg_states.append(fuzzerstate.intregpickstate.save_curr_state())
        # Sanity checks
        assert fuzzerstate.get_num_fuzzing_instructions_sofar() == 0, "We should have generated only one basic block so far."
        assert fuzzerstate.has_reached_max_instr_num() == False, "We should not have reached the max number of instructions yet."

        # Reserve space for the second basic block (whose address is already fixed).
        fuzzerstate.memview.alloc_mem_range(fuzzerstate.next_bb_addr, fuzzerstate.next_bb_addr+BASIC_BLOCK_MIN_SPACE)

        # Generate the random data block
        gen_random_data_block(fuzzerstate)

        # Reserve space for the final basic block.
        alloc_final_basic_block(fuzzerstate)
        # Reserve space for the context setter basic block, but do not instantiate it because we do not know yet what it will look like until we have a concrete context to restore. Until then, we just know arbitrary bounds.
        if not alloc_context_saver_bb(fuzzerstate):
            continue

        # Finally, generate the store locations. This can be swapped with generating the final basic block.
        fuzzerstate.memstorestate.init_store_locations(fuzzerstate.num_store_locations, fuzzerstate.memview)

        while True:
            # print('len(fuzzerstate.instr_objs_seq)', len(fuzzerstate.instr_objs_seq))
            gen_basicblock(fuzzerstate)
            if fuzzerstate.next_bb_addr is None:
                # This corresponds to failing to find space for a new basic block. In this case, this block may also not have completed, and we drop it.
                break
            # Save the register states
            fuzzerstate.saved_reg_states.append(fuzzerstate.intregpickstate.save_curr_state())
            if fuzzerstate.nmax_bbs is not None and len(fuzzerstate.instr_objs_seq) >= fuzzerstate.nmax_bbs \
                  or fuzzerstate.memview.get_allocated_ratio() >= LIMIT_MEM_SATURATION_RATIO \
                  or fuzzerstate.has_reached_max_instr_num():
                break
            fuzzerstate.memview.alloc_mem_range(fuzzerstate.next_bb_addr, fuzzerstate.next_bb_addr+BASIC_BLOCK_MIN_SPACE)

            # print('Mem occupation:', fuzzerstate.memview.get_allocated_ratio(), end='\r')
        # print()

        pop_success = pop_last_bbs_to_connect_with_final_block(fuzzerstate)
        if pop_success:
            break
        # Staying in the external loop is typically extremely rare. Staying corresponds to not being able to jump to the final bb despite popping any number of bbs. This may happen mostly with large memories and with a very high prevalence of direct control flow instructions (JAL or branches)

    # Generate the content of the final basic block, now that we know the final privilege level.
    fuzzerstate.final_bb = finalblock(fuzzerstate, fuzzerstate.design_name)

    # Forbid loads from addresses where instructions change between spike resolution and RTL sim.
    blacklist_changing_instructions(fuzzerstate)
    blacklist_final_block(fuzzerstate) # Must be done once the bb is created, else we could also blacklist upper bounds over the basic block size.
    blacklist_context_setter(fuzzerstate)

    # Generate addresses for memory operations
    memop_addrs = gen_memop_addrs(fuzzerstate)

    fuzzerstate.producer_id_to_tgtaddr, fuzzerstate.producer_id_to_noreloc_spike = gen_producer_id_to_tgtaddr(fuzzerstate, memop_addrs)

    # Debug only
    # for bb_id, bb in enumerate(fuzzerstate.instr_objs_seq):
    #     for bb_instr_id, bb_instr in enumerate(bb):
    #         curr_addr = fuzzerstate.bb_start_addr_seq[bb_id] + bb_instr_id * 4 # NO_COMPRESSED
    #         if curr_addr == 0x4e198:
    #             print('BB id:', bb_instr_id)
    #             print('Instr type:', bb_instr)
    #             print('Plan taken:', bb_instr.plan_taken)
    # print('Start addr:', hex(fuzzerstate.bb_start_addr_seq[147]))

    return fuzzerstate
