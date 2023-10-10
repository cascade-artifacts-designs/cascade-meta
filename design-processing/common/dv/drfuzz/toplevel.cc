// Copyright 2023 Flavien Solt, ETH Zurich.
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only
#include <iostream>

#include "testbench.h"
#include "queue.h"
#include "ticks.h"
#include "dtypes.h"
#include "corpus.h"
#include "mutator.h"

// run one input that is split into a temporal sequence of inputs
static inline void fuzz_once(Testbench *tb, bool reset = true, bool print = false) {
	tb->init();

	if (reset){
		tb->meta_reset();
		tb->reset();
		assert(tb->outputs.size() == 0);
	}

	while(tb->has_another_input()){
		if(print){
			std::cout << "TB INPUT\n";
			 tb->print_next_input();
		}
		tb->apply_next_input();
		tb->tick();
		tb->read_new_output();
		if(print){
			std::cout << "TB OUTPUT\n";
			tb->print_last_output();
		}
	}

	tb->finish();
}

static long fuzz(){
	auto start = std::chrono::steady_clock::now();
	
	Testbench *tb = new Testbench(cl_get_tracefile());
	Corpus *corpus = new Corpus();

	Queue *rnd = new Queue();
	rnd->generate_inputs(1000);
	tb->push_inputs(rnd->pop_tb_inputs());
	fuzz_once(tb, true);
	rnd->push_tb_outputs(tb->pop_outputs());
	rnd->push_tb_inputs(tb->pop_retired_inputs());


	Queue *seed = new Queue();
	seed->seed();

	std::cout << "***SEED***\n";
	std::cout << "INPUT:\n";
	seed->print_inputs();

	tb->push_inputs(seed->pop_tb_inputs());
	fuzz_once(tb, true);
	seed->push_tb_outputs(tb->pop_outputs());
	std::cout << "OUTPUT: \n";
	seed->print_outputs();
	std::cout << "ACCUMULATED OUTPUT:\n";
	seed->get_accumulated_output()->print();
	std::cout << "COVERAGE:\n" << seed->get_coverage_amount() << "\n";
	
	if(seed->get_accumulated_output()->failed()){
		std::cout << "Invalid input seed!\n";
		exit(-1);
	}

	unsigned long milliseconds_since_epoch = std::chrono::system_clock::now().time_since_epoch() / std::chrono::milliseconds(1);
	std::cout << "Timestamp start: " << milliseconds_since_epoch << std::endl;

	seed->push_tb_inputs(tb->pop_retired_inputs());
	std::cout << "**********\n";
	std::cout << "***CORPUS***\n";
	corpus->add_q(seed);
	while(!corpus->empty()){
		Queue *q = corpus->pop_q(); // generate mutated children of q here and apply each to tb
		std::deque<Mutator *> *mutators = get_all_mutators(q->size());
		while(mutators->size()){
			Mutator *mut = mutators->front();
			mutators->pop_front();
			mut->print();
			while(!mut->is_done()){
				#ifdef WRITE_COVERAGE
				corpus->dump_current_cov(tb);
				#endif
				Queue *mut_q = mut->apply_next(q);
				tb->push_inputs(mut_q->pop_tb_inputs());
				fuzz_once(tb, true);
				mut_q->push_tb_outputs(tb->pop_outputs());
				mut_q->push_tb_inputs(tb->pop_retired_inputs()); // retrieve inputs back into q
				// mut_q->clear_tb_outputs(); // the individual outputs per cycle dont matter, we just care for the accumulated output
				if(corpus->is_interesting(mut_q)){
					corpus->add_q(mut_q);
				}
				else{
					delete mut_q;
				}
			}
		}
	}

	unsigned long milliseconds_since_epoch_stop = std::chrono::system_clock::now().time_since_epoch() / std::chrono::milliseconds(1);
	std::cout << "Timestamp stop: " << milliseconds_since_epoch_stop << std::endl;

	std::cout << "**********\n";
	std::cout << "RFUZZ max possible coverage: " << N_COV_POINTS << std::endl;
	std::cout << "RFUZZ achieved coverage: " << corpus->get_coverage_amount() << std::endl;
	std::cout << "RFUZZ total number of cycles: \n" << tb->tick_count_ << std::endl;
	std::cout << "RFUZZ final coverage map: \n";
	corpus->print_acc_coverage();

	auto stop = std::chrono::steady_clock::now();
	long ret = std::chrono::duration_cast<std::chrono::milliseconds>(stop - start).count();


	return ret;
}

int main(int argc, char **argv, char **env) {

	Verilated::commandArgs(argc, argv);
	Verilated::traceEverOn(VM_TRACE);
	
	long duration = fuzz();
	exit(0);

	Queue *q = new Queue();
	q->generate_inputs();

	Testbench *tb = new Testbench(cl_get_tracefile());
	
	tb->push_inputs(q->pop_tb_inputs());
	fuzz_once(tb, true);
	q->push_tb_outputs(tb->pop_outputs());
	q->push_tb_inputs(tb->pop_retired_inputs());
	std::cout << "INPUTS\n";
	q->print_inputs();
	std::cout << "OUTPUTS\n";
	q->print_outputs();
	std::cout << "ACCUMULATED OUTPUT\n";
	q->print_accumulated_output();
}
