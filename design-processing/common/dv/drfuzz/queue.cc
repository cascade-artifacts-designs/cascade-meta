#include <cassert>
#include <iostream>
#include <cstring>

#include "queue.h"
#include "dtypes.h"
#include "macros.h"

void Queue::generate_inputs(int n_inputs){ // will move this to mutation engine
    for(size_t i = 0; i<n_inputs; i++){
        dinput_t *new_input = (dinput_t *) malloc(sizeof(dinput_t)); // allocates memory for inputs -> do this in mutator?
        for(size_t j = 0; j<N_FUZZ_INPUTS_b32; j++){
            new_input->inputs[j] = rand()%MAX_b32_VAL;
        }
        new_input->inputs[N_FUZZ_INPUTS_b32-1] &= FUZZ_INPUT_MASK;
        this->inputs.push_back(new_input);
    }
}

void Queue::seed(){
    for(int i=0; i<N_ZEROS_SEED; i++){
        dinput_t *new_input = (dinput_t *) malloc(sizeof(dinput_t));
        for(size_t j = 0; j<N_FUZZ_INPUTS_b32; j++){
            new_input->inputs[j] = 0;
        }
        new_input->inputs[N_FUZZ_INPUTS_b32-1] &= FUZZ_INPUT_MASK;
        this->inputs.push_back(new_input);
    }
}

bool Queue::has_another_input(){
    return this->inputs.size() != 0;
}

dinput_t *Queue::pop_tb_input(){
    assert(this->inputs.size());
    this->last_input = this->inputs.front();
    this->inputs.pop_front();
    return this->last_input;
}

std::deque<dinput_t *> *Queue::pop_tb_inputs(){
    return &this->inputs;
}

void Queue::accumulate_output(doutput_t *output){
    if(this->ini_output == nullptr){
        this->acc_output = (doutput_t *) malloc(sizeof(doutput_t));
        for(int i=0; i<N_COV_POINTS_b32; i++){
            this->acc_output->coverage[i] = 0; 
        }
        for(int i=0; i<N_ASSERTS_b32; i++){
            this->acc_output->asserts[i] = 0;
        }
        this->acc_output->check();

        this->ini_output = (doutput_t *) malloc(sizeof(doutput_t));
        memcpy(this->ini_output, output, sizeof(doutput_t));
    }
    else{
        for(int i=0; i<N_COV_POINTS_b32; i++){
            this->acc_output->coverage[i] |= this->ini_output->coverage[i] ^ output->coverage[i];
        }
        for(int i=0; i<N_ASSERTS_b32; i++){
            this->acc_output->asserts[i] |= output->asserts[i];
        }
        this->acc_output->check();
    }
}


void Queue::push_tb_output(doutput_t *output){
    output->check();
    this->accumulate_output(output);
    this->outputs.push_back(output);
}

void Queue::push_tb_outputs(std::deque<doutput_t *> *outputs){
    while(outputs->size()){
        this->push_tb_output(outputs->front());
        outputs->pop_front();
    }
    assert(this->outputs.size());
    assert(outputs->size()==0);
}

void Queue::push_tb_input(dinput_t *input){
    input->check();
    this->inputs.push_back(input);
}

void Queue::push_tb_inputs(std::deque<dinput_t *> *inputs){
    while(inputs->size()){
        this->push_tb_input(inputs->front());
        inputs->pop_front();
    }
    assert(this->inputs.size());
    assert(inputs->size()==0);
}

void Queue::print_inputs(){
    for(auto &inp: this->inputs) inp->print();
}

void Queue::print_outputs(){
    for(auto &out: this->outputs) out->print();
}

doutput_t *Queue::get_accumulated_output(){
    return this->acc_output;
}

void Queue::clear_accumulated_output(){
    free(this->ini_output);
    this->ini_output = nullptr;
    free(this->acc_output);
    this->acc_output = nullptr;
}

void Queue::print_accumulated_output(){
    this->acc_output->print();
}

Queue *Queue::copy(){ // deep cpy
    Queue *cpy = new Queue();
    for(auto &inp: this->inputs){
        dinput_t *cpy_inp = (dinput_t *) malloc(sizeof(dinput_t));
        memcpy(cpy_inp->inputs, inp->inputs, N_FUZZ_INPUTS_b32 * sizeof(uint32_t));
        cpy_inp->check();
        cpy->inputs.push_back(cpy_inp);
    }
    for(auto &out: this->outputs){
        doutput_t *cpy_out = (doutput_t *) malloc(sizeof(doutput_t));
        memcpy(cpy_out->coverage, out->coverage, N_COV_POINTS_b32 * sizeof(uint32_t));
        memcpy(cpy_out->asserts, out->asserts, N_ASSERTS_b32 * sizeof(uint32_t));
        cpy_out->check();
        cpy->outputs.push_back(cpy_out);
    }
    return cpy;
}

size_t Queue::size(){
    return this->inputs.size();
}

int Queue::get_coverage_amount(){
    assert((this->acc_output->coverage[N_COV_POINTS_b32-1] & ~COV_MASK) == 0);
    // Count the bits equal to 1.
    int ret = 0;
    for (int i = 0; i < N_COV_POINTS_b32; i++) {
        ret += __builtin_popcount(this->acc_output->coverage[i]);
    }
    assert(ret >= 0);
    assert(ret <= N_COV_POINTS);
    return ret;
}

void Queue::clear_tb_outputs(){
    while(this->outputs.size()){
        free(this->outputs.front());
        this->outputs.pop_front();
    }
}

void Queue::clear_tb_inputs(){
    while(this->inputs.size()){
        free(this->inputs.front());
        this->inputs.pop_front();
    }
}

bool Queue::is_equal(Queue* other){
    if(this->size() != other->size()) return false;
    if(this->outputs.size() != other->outputs.size()) return false;
    for(int i=0; i<this->inputs.size(); i++){
        this->inputs[i]->check();
        other->inputs[i]->check();
        for(int j=0; j<N_FUZZ_INPUTS_b32; j++){
            if(this->inputs[i]->inputs[j] != other->inputs[i]->inputs[j]) return false;
        }
    }
    for(int i=0; i<this->outputs.size(); i++){
        this->outputs[i]->check();
        other->outputs[i]->check();
        for(int j=0; j<N_COV_POINTS_b32; j++){
            if(this->outputs[i]->coverage[j] != other->outputs[i]->coverage[j]) return false;
        }
        for(int j=0; j<N_ASSERTS_b32; j++){
            if(this->outputs[i]->asserts[j] != other->outputs[i]->asserts[j]) return false;
        }
    }
    return true;
}

void Queue::print_diff(Queue *other){
    assert(this->size() == other->size());
    assert(this->outputs.size() == other->outputs.size());

    std::cout << "INPUT DIFF\n";
    for(int i=0; i<this->inputs.size(); i++){
        this->inputs[i]->check();
        other->inputs[i]->check();
        this->inputs[i]->print_diff(other->inputs[i]);
    }
    std::cout << "OUTPUT DIFF\n";
    for(int i=0; i<this->outputs.size(); i++){
        this->outputs[i]->check();
        other->outputs[i]->check();
        this->outputs[i]->print_diff(other->outputs[i]);
    }
}