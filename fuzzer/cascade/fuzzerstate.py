# Copyright 2023 Flavien Solt, ETH Zurich.
# Licensed under the General Public License, Version 3.0, see LICENSE for details.
# SPDX-License-Identifier: GPL-3.0-only

from params.runparams import DO_ASSERT
from params.fuzzparams import RELOCATOR_REGISTER_ID, RDEP_MASK_REGISTER_ID, FPU_ENDIS_REGISTER_ID, MIN_NUM_PICKABLE_REGS, MAX_NUM_PICKABLE_REGS, MIN_NUM_PICKABLE_FLOATING_REGS, MAX_NUM_PICKABLE_FLOATING_REGS, MPP_BOTH_ENDIS_REGISTER_ID, MPP_TOP_ENDIS_REGISTER_ID, SPP_ENDIS_REGISTER_ID, MAX_NUM_STORE_LOCATIONS
from common.designcfgs import is_design_32bit, design_has_float_support, design_has_double_support, design_has_muldiv_support, design_has_atop_support, design_has_misaligned_data_support, get_design_boot_addr, design_has_supervisor_mode, design_has_user_mode, design_has_compressed_support, design_has_pmp
from common.spike import SPIKE_STARTADDR

from cascade.util import ISAInstrClass, ExceptionCauseVal
from cascade.memview import MemoryView
from cascade.contextreplay import get_context_setter_max_size
from cascade.privilegestate import PrivilegeState
from cascade.randomize.pickstoreaddr import MemStoreState
from cascade.randomize.pickreg import IntRegPickState, FloatRegPickState
from cascade.randomize.pickisainstrclass import ISAINSTRCLASS_INITIAL_BOOSTERS
from cascade.randomize.pickexceptionop import EXCEPTION_OP_TYPE_INITIAL_BOOSTERS

import random

class FuzzerState:
    # @param randseed for identification purposes only.
    def __init__(self, design_base_addr: int, design_name: str, memsize: int, randseed: int, nmax_bbs: int, authorize_privileges: bool, nmax_instructions: int = None, nodependencybias: bool = False):
        # For identification
        self.randseed = randseed
        self.nmax_bbs = nmax_bbs
        self.nmax_instructions = nmax_instructions
        self.nodependencybias = nodependencybias
        self.memsize = memsize
        self.authorize_privileges = authorize_privileges

        self.design_name = design_name
        self.design_base_addr = design_base_addr
        self.is_design_64bit = not is_design_32bit(design_name)
        self.design_has_compressed_support     : bool = design_has_compressed_support(design_name)
        self.design_has_fpu                    : bool = design_has_float_support(design_name)
        self.design_has_fpud                   : bool = design_has_double_support(design_name)
        self.design_has_muldiv                 : bool = design_has_muldiv_support(design_name)
        self.design_has_amo                    : bool = design_has_atop_support(design_name)
        self.design_has_misaligned_data_support: bool = design_has_misaligned_data_support(design_name)
        self.design_has_supervisor_mode        : bool = design_has_supervisor_mode(design_name)
        self.design_has_user_mode              : bool = design_has_user_mode(design_name)
        self.design_has_pmp                    : bool = design_has_pmp(design_name)

        self.gen_pick_weights()
        self.reset()
        self.init_design_state()

    # @brief cleans up the fuzzerstate. Used in case of failed input generation.
    def reset(self):
        self.initial_block_data_start, self.initial_block_data_end = None, None
        self.random_block_content4by4bytes = []

        self.next_bb_addr = 0
        self.memview = MemoryView(self.memsize)
        self.memview_blacklist = MemoryView(self.memsize) # For load blacklist

        self.num_store_locations = random.randint(1, MAX_NUM_STORE_LOCATIONS)
        self.ctxsv_size_upperbound: int = get_context_setter_max_size(self) # Can be called once is_design_64bit, design_has_fpu and design_has_fpud are set, and the number of store locations is known.

        self.memstorestate = MemStoreState()
        self.intregpickstate = IntRegPickState(self.num_pickable_regs, self.nodependencybias)
        self.floatregpickstate = FloatRegPickState(self.num_pickable_floating_regs)
        self.privilegestate = PrivilegeState()

        # self.instr_objs_seq does NEVER contain the final basic block.
        self.instr_objs_seq = [] # List (queue) of (for each basic block) lists of instruction objects
        self.bb_start_addr_seq = [] # List (queue) of bb start addresses. Self-managed through init_new_bb.
        self.saved_reg_states = [] # List (queue) of register save objects, as saved by pickreg.py

        # Strictly increasing when we create new producer0, to ensure uniqueness
        self.next_producer_id = 0
        # As a second phase, we will populate the producers with addresses before the spike resolution
        self.producer_id_to_tgtaddr = None
        self.producer_id_to_noreloc_spike = None
        # Register initial data address and content
        self.initial_reg_data_addr = -1
        self.initial_reg_data_content = []
        # Register final data address and content. The final bb is responsible for dumping the the final integer and floating registers.
        self.final_bb = []
        self.final_bb_base_addr = -1
        # Context setter
        self.ctxsv_bb = []
        self.ctxsv_bb_base_addr = -1
        self.ctxsv_bb_jal_instr_id = -1 # Useful because the last elements in ctxsv_bb are data.
        self.ctxdmp_bb = []
        self.ctxdmp_bb_base_addr = -1
        self.ctxdmp_bb_jal_instr_id = -1 # Useful because the last elements in ctxdmp_bb are data.

        # Instructions after the basic blocks, called block tails
        self.block_tail_instrs = [] # List of pairs (instr_obj, instr_addr)

        # Rocket has some inaccuracy in minstret because of ebreak and ecall. Hence, we don't read instret after these 2 instructions.
        self.is_minstret_inaccurate_because_ecall_ebreak = False
        # To avoid having too many fences
        self.special_instrs_count = 0
        # Coordinates of the FPU enable/disable instructions. Only used in program reduction.
        self.fpuendis_coords = []

    # @brief adds instruction(s) to the latest basic block 
    # @param new_instrobjs: List of instructions or single instruction to 
    # be added to the latest basic block
    def add_instruction(self, new_instrobjs):
        if isinstance(new_instrobjs, list):
            self.instr_objs_seq[-1].extend(new_instrobjs)
        else:
            self.instr_objs_seq[-1].append(new_instrobjs)            
    
    # @brief registers the coordinates of a FPU enable/disable instruction
    def add_fpu_coord(self):
        bb_id = len(self.instr_objs_seq) - 1
        instr_id = len(self.instr_objs_seq[-1])
        self.fpuendis_coords.append((bb_id, instr_id))

    # @brief removes the current basic block for the generated program and
    # restores registers to their states in the previous basic block
    def restore_previous_state(self):
        self.instr_objs_seq.pop()
        self.bb_start_addr_seq.pop()
        self.intregpickstate.restore_state(self.saved_reg_states[-1])

    # @brief returns the current address for the next instruction to generate
    def get_current_addr(self):
        return self.curr_bb_start_addr + 4*len(self.instr_objs_seq[-1])
    
    # @brief stores the current states of registers
    def save_reg_state(self):
        self.saved_reg_states.append(self.intregpickstate.save_curr_state())

    # @brief initializes a new basic block
    def init_new_bb(self):
        self.instr_objs_seq.append([])

        self.curr_bb_start_addr = self.next_bb_addr
        self.next_bb_addr = None
        self.bb_start_addr_seq.append(self.curr_bb_start_addr)

    # @brief generates random weights to select instructions
    def gen_pick_weights(self):
        self.fpuweight = random.random() # Can decrease the overall FPU load to favor other types of instructions
        self.isapickweights = {
            ISAInstrClass.REGFSM:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.REGFSM],
            ISAInstrClass.FPUFSM:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.FPUFSM],
            ISAInstrClass.ALU:         (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.ALU],
            ISAInstrClass.ALU64:       (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.ALU64],
            ISAInstrClass.MULDIV:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MULDIV],
            ISAInstrClass.MULDIV64:    (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MULDIV64],
            ISAInstrClass.AMO:         (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.AMO],
            ISAInstrClass.AMO64:       (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.AMO64],
            ISAInstrClass.JAL :        (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.JAL],
            ISAInstrClass.JALR:        (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.JALR],
            ISAInstrClass.BRANCH:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.BRANCH],
            ISAInstrClass.MEM:         (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MEM],
            ISAInstrClass.MEM64:       (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MEM64],
            ISAInstrClass.MEMFPU:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MEMFPU]  * self.fpuweight,
            ISAInstrClass.FPU:         (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.FPU]     * self.fpuweight,
            ISAInstrClass.FPU64:       (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.FPU64]   * self.fpuweight,
            ISAInstrClass.MEMFPUD:     (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MEMFPUD] * self.fpuweight,
            ISAInstrClass.FPUD:        (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.FPUD]    * self.fpuweight,
            ISAInstrClass.FPUD64:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.FPUD64]  * self.fpuweight,
            ISAInstrClass.MEDELEG:     (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.MEDELEG],
            ISAInstrClass.TVECFSM:     (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.TVECFSM],
            ISAInstrClass.PPFSM:       (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.PPFSM],
            ISAInstrClass.EPCFSM:      (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.EPCFSM],
            ISAInstrClass.EXCEPTION:   (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.EXCEPTION],
            ISAInstrClass.RANDOM_CSR:  (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.RANDOM_CSR],
            ISAInstrClass.DESCEND_PRV: (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.DESCEND_PRV],
            ISAInstrClass.SPECIAL:     (random.random() + 0.05) * ISAINSTRCLASS_INITIAL_BOOSTERS[ISAInstrClass.SPECIAL],
        }
        self.exceptionoppickweights = {
            ExceptionCauseVal.ID_INSTR_ADDR_MISALIGNED:        (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_INSTR_ADDR_MISALIGNED],
            ExceptionCauseVal.ID_INSTR_ACCESS_FAULT:           (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_INSTR_ACCESS_FAULT],
            ExceptionCauseVal.ID_ILLEGAL_INSTRUCTION:          (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_ILLEGAL_INSTRUCTION],
            ExceptionCauseVal.ID_BREAKPOINT:                   (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_BREAKPOINT],
            ExceptionCauseVal.ID_LOAD_ADDR_MISALIGNED:         (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_LOAD_ADDR_MISALIGNED],
            ExceptionCauseVal.ID_LOAD_ACCESS_FAULT:            (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_LOAD_ACCESS_FAULT],
            ExceptionCauseVal.ID_STORE_AMO_ADDR_MISALIGNED:    (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_STORE_AMO_ADDR_MISALIGNED],
            ExceptionCauseVal.ID_STORE_AMO_ACCESS_FAULT:       (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_STORE_AMO_ACCESS_FAULT],
            ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_U_MODE: (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_U_MODE],
            ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_S_MODE: (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_S_MODE],
            ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_M_MODE: (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_ENVIRONMENT_CALL_FROM_M_MODE],
            ExceptionCauseVal.ID_INSTRUCTION_PAGE_FAULT:       (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_INSTRUCTION_PAGE_FAULT],
            ExceptionCauseVal.ID_LOAD_PAGE_FAULT:              (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_LOAD_PAGE_FAULT],
            ExceptionCauseVal.ID_STORE_AMO_PAGE_FAULT:         (random.random() + 0.05) * EXCEPTION_OP_TYPE_INITIAL_BOOSTERS[ExceptionCauseVal.ID_STORE_AMO_PAGE_FAULT]
        }

        if self.design_has_fpu:
            # Probability to change rounding mode instead of turning the FPU off
            self.proba_change_rm = random.random()
        self.proba_ebreak_instead_of_ecall = random.random()

        # Numbers of pickable registers
        if self.nodependencybias:
            self.num_pickable_regs = MAX_NUM_PICKABLE_REGS
        else:
            self.num_pickable_regs = random.randint(MIN_NUM_PICKABLE_REGS, MAX_NUM_PICKABLE_REGS)
        if DO_ASSERT:
            assert self.num_pickable_regs < RELOCATOR_REGISTER_ID, f"Required self.num_pickable_regs ({self.num_pickable_regs}) < RELOCATOR_REGISTER_ID ({RELOCATOR_REGISTER_ID})"
            assert self.num_pickable_regs < RDEP_MASK_REGISTER_ID, f"Required self.num_pickable_regs ({self.num_pickable_regs}) < RDEP_MASK_REGISTER_ID ({RDEP_MASK_REGISTER_ID})"
            assert self.num_pickable_regs < FPU_ENDIS_REGISTER_ID, f"Required self.num_pickable_regs ({self.num_pickable_regs}) < FPU_ENDIS_REGISTER_ID ({FPU_ENDIS_REGISTER_ID})"
            assert self.num_pickable_regs < MPP_BOTH_ENDIS_REGISTER_ID, f"Required self.num_pickable_regs ({self.num_pickable_regs}) < MPP_BOTH_ENDIS_REGISTER_ID ({MPP_BOTH_ENDIS_REGISTER_ID})"
            assert self.num_pickable_regs < MPP_TOP_ENDIS_REGISTER_ID, f"Required self.num_pickable_regs ({self.num_pickable_regs}) < MPP_TOP_ENDIS_REGISTER_ID ({MPP_TOP_ENDIS_REGISTER_ID})"
            assert self.num_pickable_regs < SPP_ENDIS_REGISTER_ID, f"Required self.num_pickable_regs ({self.num_pickable_regs}) < SPP_ENDIS_REGISTER_ID ({SPP_ENDIS_REGISTER_ID})"
        if self.design_has_fpu:
            # We impose self.num_pickable_floating_regs <= self.num_pickable_regs just because initialblock is easier to write. It also has no impact on the fuzzing quality overall.
            self.num_pickable_floating_regs = random.randint(MIN_NUM_PICKABLE_FLOATING_REGS, min(MAX_NUM_PICKABLE_FLOATING_REGS, self.num_pickable_regs))
        else:
            self.num_pickable_floating_regs = 0 # Just for compatibility. This variable is not used if self.design_has_fpu is False.

        # Registers' initial values
        self.proba_reg_starts_with_zero = random.random() / 10
        if DO_ASSERT:
            assert self.proba_reg_starts_with_zero >= 0.0
            assert self.proba_reg_starts_with_zero <= 1.0

    # @brief intializes the design states
    def init_design_state(self):
        if self.design_has_fpu:
            self.is_fpu_activated = True
            self.proba_turn_on_off_fpu_again = random.random()*0.1 # Proba that we re-turn the FPU into the mode it is already in (on or off)

    # @brief return a string identifier of the current program
    def instance_to_str(self):
        return f"{self.memview.memsize}_{self.design_name}_{self.randseed}_{self.nmax_bbs}"

    # @brief returns true if the current program has reached the maximal number 
    # of instructions
    def has_reached_max_instr_num(self):
        if self.nmax_instructions is None:
            return False
        assert self.nmax_instructions > 0, f"self.nmax_instructions ({self.nmax_instructions}) <= 0"
        # Do not make this check because we still add a JAL after that.
        # assert self.get_num_fuzzing_instructions_sofar() <= self.nmax_instructions, f"self.get_num_fuzzing_instructions_sofar() ({self.get_num_fuzzing_instructions_sofar()}) > self.nmax_instructions ({self.nmax_instructions})"
        return self.get_num_fuzzing_instructions_sofar() >= self.nmax_instructions
    
    # @brief counts the number of generated intruction, does not count the 
    # initial and final blocks
    def get_num_fuzzing_instructions_sofar(self):
        if len(self.instr_objs_seq) <= 1:
            return 0
        return sum([len(bb) for bb in self.instr_objs_seq[1:]])
