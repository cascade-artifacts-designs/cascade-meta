// Copyright 2023 Flavien Solt, Tobias Kovats, ETH Zurich
// Licensed under the General Public License, Version 3.0, see LICENSE for details.
// SPDX-License-Identifier: GPL-3.0-only

#include "testbench.h"

void Testbench::apply_vinput(uint32_t* inputs){
    for(int i=0; i<N_COV_POINTS_b32; i++){
        this->module_->fuzz_in[i] = inputs[i];
    }
}

void Testbench::read_vcoverage(uint32_t* cov){
    for(int i=0; i<N_COV_POINTS_b32; i++){
        cov[i] = this->module_->auto_cover_out[i];
    }
    cov[N_COV_POINTS_b32-1] &= COV_MASK;

    // uint64_t sum = 0;
    // for(int i=0; i<N_COV_POINTS_b32; i++){
    //     sum += cov[i];
    // }
    // std::cout << "sum: " << sum << " N_COV_POINTS_b32: " << N_COV_POINTS_b32 << std::endl;
}

void Testbench::read_vasserts(uint32_t* asserts){
    #ifdef CHECK_ASSERTS
    for(int i=0; i<N_ASSERTS_b32; i++){
        asserts[i] = this->module_->assert_probes[i];
    }
    asserts[N_ASSERTS_b32-1] &= ASSERTS_MASK;
    #endif
}


void Testbench::reset(){
    uint32_t inputs[N_FUZZ_INPUTS_b32] = {0};

    this->module_->rst_ni = 1;
    this->module_->meta_rst_ni = 1;
    this->apply_vinput(inputs);

    this->tick(1);
    this->module_->rst_ni = 0;
    this->tick(N_RESET_TICKS);
    this->module_->rst_ni = 1;
}

void Testbench::meta_reset(){
    uint32_t inputs[N_FUZZ_INPUTS_b32] = {0};

    this->module_->meta_rst_ni = 1;
    this->module_->rst_ni = 1; // deassert normal reset while meta reset is running
    this->apply_vinput(inputs);
    this->tick(1);
    this->module_->meta_rst_ni = 0;
    this->tick(N_META_RESET_TICKS);
    this->module_->meta_rst_ni = 1;
}

void Testbench::push_input(dinput_t *input){
    this->scheduled_inputs.push_back(input);
}

void Testbench::push_inputs(std::deque<dinput_t *> *inputs){
    while(inputs->size()){
        this->push_input(inputs->front());
        inputs->pop_front();
    }
    assert(this->scheduled_inputs.size());
    assert(inputs->size()==0);
}

std::deque<doutput_t *> *Testbench::pop_outputs(){
    return &this->outputs;
}

bool Testbench::has_another_input(){
    return this->scheduled_inputs.size() != 0;
}
void Testbench::apply_next_input(){
    if(!this->has_another_input()){
        std::cout << "out of inputs!\n";
        return; 
    }
    this->apply_vinput(this->scheduled_inputs.front()->inputs);
    this->retired_inputs.push_back(this->scheduled_inputs.front());
    this->scheduled_inputs.pop_front();
}

void Testbench::read_new_output(){
    doutput_t *new_output = (doutput_t *) malloc(sizeof(doutput_t));
    this->read_vcoverage(new_output->coverage);
    this->read_vasserts(new_output->asserts);
    new_output->check_failed();
    new_output->check(); // sanity check
    this->outputs.push_back(new_output);
}   

void Testbench::close_trace(){
    #if VM_TRACE
    this->trace_->close();
    #endif
}

void Testbench::tick(int n_ticks, bool false_tick){
    for(int i=0; i<n_ticks; i++){
        this->tick_count_++;
        this->module_->clk_i = 0;
        this->module_->eval();
        #if VM_TRACE
        trace_->dump(5 * this->tick_count_ - 1);
        #endif // VM_TRACE
        this->module_->clk_i = !false_tick;
        this->module_->eval();
        #if VM_TRACE
        trace_->dump(5 * this->tick_count_);
        #endif // VM_TRACE
        this->module_->clk_i = 0;
        this->module_->eval();
         #if VM_TRACE
        trace_->dump(5 * this->tick_count_ + 1);
        trace_->flush();
        #endif // VM_TRACE
    }
}

void Testbench::print_next_input(){
    assert(this->scheduled_inputs.size());
    this->scheduled_inputs.front()->print();
}

void Testbench::print_last_output(){
    assert(this->outputs.size());
    this->outputs.back()->print();
}

void Testbench::finish(){
    while(this->scheduled_inputs.size()) this->scheduled_inputs.pop_front();
}

void Testbench::init(){
    while(this->outputs.size()) this->outputs.pop_front();
}

void Testbench::check_outputs(){
    for(auto &out: this->outputs) out->check();
}

std::deque<dinput_t *> *Testbench::pop_retired_inputs(){
    return &this->retired_inputs;
}

void Testbench::free_retired_inputs(){ // we dont need them anymore so free the allocated memory
    while(this->retired_inputs.size()){
        free(this->retired_inputs.front());
        this->retired_inputs.pop_front();
    }
}



