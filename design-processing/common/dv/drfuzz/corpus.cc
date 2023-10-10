#include <cstring>

#include "corpus.h"
void Corpus::add_q(Queue *q){
    this->qs.push_back(q);
    this->accumulate_output(q);
    assert(this->qs.size());
}

void Corpus::dump_current_cov(Testbench *tb){
    #ifdef WRITE_COVERAGE
    this->acc_output->dump(tb);
    #else
    std::cout << "enable WRITE_COVERAGE compile flag!\n";
    #endif
}

Queue *Corpus::pop_q(){
    assert(this->qs.size());
    Queue *front = this->qs.front();
    assert(front != nullptr);
    this->qs.pop_front();
    return front;
}

bool Corpus::empty(){
    return this->qs.size()==0;
}

void Corpus::accumulate_output(Queue *q){ // we don't need initial coverage here since all the queues are already accumulated
    doutput_t *output = q->get_accumulated_output();
    if(output == nullptr) return;
    if(this->acc_output == nullptr){
        this->acc_output = (doutput_t *) malloc(sizeof(doutput_t));
        memcpy(this->acc_output, output, sizeof(doutput_t));
    }
    else{
        for(int i=0; i<N_COV_POINTS_b32; i++){
            this->acc_output->coverage[i] |= this->acc_output->coverage[i] ^ output->coverage[i];
        }

        for(int i=0; i<N_ASSERTS_b32; i++){
            this->acc_output->asserts[i] |= output->asserts[i];
        }
        this->acc_output->check();
    }
}

bool Corpus::is_interesting(Queue *q){
    bool is_interesting = false;
    if(this->acc_output==nullptr) return true;
    doutput_t *new_output = q->get_accumulated_output();
    std::deque<size_t> new_toggles_idx;;
    for(int i=0; i<N_COV_POINTS_b32; i++){
        uint32_t check = (~this->acc_output->coverage[i]) & new_output->coverage[i];
        if(check != 0){
            is_interesting = true;
            for(int j=0; j<32; j++){
                if(check & (1<<j)){
                    new_toggles_idx.push_back(31-j+i*N_COV_POINTS_b32*sizeof(uint32_t)); // maybe need the indices sometime later
                }
            }
        } 
    }
    if(is_interesting){
        std::cout << "Toggled " << new_toggles_idx.size() << " new coverage point(s) \n";
        unsigned long milliseconds_since_epoch = std::chrono::system_clock::now().time_since_epoch() / std::chrono::milliseconds(1);
        std::cout << "Timestamp toggle: " << milliseconds_since_epoch << std::endl;
        std::cout << "New total coverage: " << this->get_coverage_amount() + new_toggles_idx.size() << std::endl;
        this->acc_output->print_increase(new_output);
    }
    return is_interesting;
}

int Corpus::get_coverage_amount() {
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

void Corpus::print_acc_coverage(){
    this->acc_output->print();
}

doutput_t *Corpus::get_accumulated_output(){
    return this->acc_output;
}

