#include "mutator.h"
#include "corpus.h"

#include <cstring>
#include <deque>

void Mutator::init(){
    this->done = false;
    this->idx = -1;
}

void Mutator::print(){
    std::cout << "Running mutator " << this->name << "\n";
}

bool Mutator::is_done(){
    return this->done;
}

Queue *Mutator::apply_next(Queue *in_q){
    this->next();
    return this->apply(in_q);
}

Queue *Mutator::apply(Queue *in_q) {
    assert(in_q->size());
    size_t input_size = in_q->inputs.size() * N_FUZZ_INPUTS_b32 * sizeof(uint32_t); // total number of bytes 
    uint8_t *inp_buf = (uint8_t *) malloc(input_size);
    for(int i=0; i<in_q->inputs.size(); i++){ // copy all inputs in queue to contigous memory
        memcpy(inp_buf + i * N_FUZZ_INPUTS_b32 * sizeof(uint32_t), in_q->inputs[i]->inputs,  N_FUZZ_INPUTS_b32 * sizeof(uint32_t));
    }
    this->permute(inp_buf);
    Queue *out_q = new Queue();
    for(int i=0; i<in_q->inputs.size(); i++){
        dinput_t *new_input = (dinput_t *) malloc(sizeof(dinput_t));
        memcpy(new_input->inputs, inp_buf + i * N_FUZZ_INPUTS_b32 * sizeof(uint32_t),  N_FUZZ_INPUTS_b32 * sizeof(uint32_t));
        new_input->clean();
        out_q->push_tb_input(new_input);
    }
    free(inp_buf);
    assert(out_q->size());
    return out_q;
}

void DetMutator::next(){
            assert(!this->done);
            size_t i = this->idx;
            this->idx++;
            if(this->idx == this->max) this->done=true;
}

void RandMutator::next(){
            assert(!this->done);
            this->idx = rand()%this->max;
            this->done=true; // change this back
}

void SingleBitFlipMutator::permute(uint8_t *buf){
    FLIP_BIT(buf, this->idx);
}

void DoubleBitFlipMutator::permute(uint8_t *buf){
    FLIP_BIT(buf, this->idx);
    FLIP_BIT(buf, this->idx+1);
}

void NibbleFlipMutator::permute(uint8_t *buf){
    FLIP_BIT(buf, this->idx);
    FLIP_BIT(buf, this->idx+1);
    FLIP_BIT(buf, this->idx+2);
    FLIP_BIT(buf, this->idx+3);
}

void SingleByteFlipMutator::permute(uint8_t *buf){
    buf[this->idx] ^= 0xFF;
}

void DoubleByteFlipMutator::permute(uint8_t *buf){
    buf[this->idx] ^= 0xFF;
    buf[this->idx+1] ^= 0xFF;
}

void QuadByteFlipMutator::permute(uint8_t *buf){
    buf[this->idx] ^= 0xFF;
    buf[this->idx+1] ^= 0xFF;
    buf[this->idx+2] ^= 0xFF;
    buf[this->idx+3] ^= 0xFF;

}

void AddSingleByteMutator::permute(uint8_t *buf){
    size_t rand_v = rand()% 35; // [0,35] as in rfuzz paper
    if(rand()%2){
        buf[this->idx] += rand_v;
    }
    else{
        buf[this->idx] -= rand_v;
    }
}

void AddDoubleByteMutator::permute(uint8_t *buf){
    uint16_t rand_v = rand() % 35; // [0,35] as in rfuzz paper
    switch(rand()%4){
        case 0: 
            buf[idx] += rand_v&0xFF;
            buf[idx+1] += (rand_v&0xFF00)>>8;
            break;
        case 1: 
            buf[idx] -= rand_v&0xFF;
            buf[idx+1] -= (rand_v&0xFF00)>>8;
            break;
        case 2: 
            rand_v = SWAP16(SWAP16(((uint16_t *) buf)[idx]) + rand_v);
            buf[idx] = rand_v&0xFF; 
            buf[idx+1] = (rand_v&0xFF00)>>8; 
            break;
        case 3: 
            rand_v = SWAP16(SWAP16(((uint16_t *) buf)[idx]) - rand_v);
            buf[idx] = rand_v&0xFF; 
            buf[idx+1] = (rand_v&0xFF00)>>8;  // is this right or should idx be switched?
            break;
    }
}


void AddQuadByteMutator::permute(uint8_t *buf){
    uint32_t rand_v = rand() % 35; // [0,35] as in rfuzz paper
    switch(rand()%4){
        case 0: 
            buf[idx] += rand_v&0xFF;
            buf[idx+1] += (rand_v&0xFF00)>>8;
            buf[idx+2] += (rand_v&0xFF0000)>>16;
            buf[idx+3] += (rand_v&0xFF000000)>>24;
            break;
        case 1: 
            buf[idx] -= rand_v&0xFF;
            buf[idx+1] -= (rand_v&0xFF00)>>8;
            buf[idx+2] -= (rand_v&0xFF0000)>>16;
            buf[idx+3] -= (rand_v&0xFF000000)>>24;
            break;
        case 2: 
            rand_v = SWAP16(SWAP16(((uint16_t *) buf)[idx]) + rand_v);
            buf[idx] = rand_v&0xFF;
            buf[idx+1] = (rand_v&0xFF00)>>8;
            buf[idx+2] = (rand_v&0xFF0000)>>16;
            buf[idx+3] = (rand_v&0xFF000000)>>24;
            break;
        case 3: 
            rand_v = SWAP16(SWAP16(((uint16_t *) buf)[idx]) - rand_v);
            buf[idx] = rand_v&0xFF;
            buf[idx+1] = (rand_v&0xFF00)>>8;
            buf[idx+2] = (rand_v&0xFF0000)>>16;
            buf[idx+3] = (rand_v&0xFF000000)>>24;
            break;
    }
}


void OverwriteInterestingSingleByteMutator::permute(uint8_t *buf){
    int8_t interesting[] = {INTERESTING_8};
    buf[this->idx] = interesting[rand() % (INTERESTING_8_LEN-1)];
}

void OverwriteInterestingDoubleByteMutator::permute(uint8_t *buf){
    int16_t interesting[] = {INTERESTING_16};
    int16_t rand_v = interesting[rand() % (INTERESTING_16_LEN-1)];
    buf[this->idx] = rand_v&0xFF;
    buf[this->idx+1] = (rand_v&0xFF00)>>8;
}

void OverwriteInterestingQuadByteMutator::permute(uint8_t *buf){
    int32_t interesting[] = {INTERESTING_32};
    int32_t rand_v = interesting[rand() % (INTERESTING_32_LEN-1)];
    buf[idx] = rand_v&0xFF;
    buf[idx+1] = (rand_v&0xFF00)>>8;
    buf[idx+2] = (rand_v&0xFF0000)>>16;
    buf[idx+3] = (rand_v&0xFF000000)>>24;
}

void OverwriteRandomByteMutator::permute(uint8_t *buf){
    buf[this->idx] = rand()%255;
}

void DeleteRandomBytesMutator::permute(uint8_t *buf){
    size_t n_bytes = rand()%this->max;
    for(int i=0; i<n_bytes; i++){
        buf[(this->idx+i)%(this->max-1)] = 0x00;
    }
}

void CloneRandomBytesMutator::permute(uint8_t *buf){
    size_t n_bytes = rand()%(this->max/2);
    size_t src_idx = rand()%(this->max-n_bytes);
    size_t dst_idx = rand()%(this->max-n_bytes);
    memcpy(&buf[dst_idx], &buf[src_idx], n_bytes);
}

void OverwriteRandomBytesMutator::permute(uint8_t *buf){
    size_t n_bytes = rand()%this->max;
    for(int i=0; i<n_bytes; i++){
        buf[(this->idx+i)%(this->max-1)] = rand()%255;
    }
}


std::deque<Mutator *> *get_det_mutators(size_t max){
    Mutator *det_mutators[] = {
                            new DetSingleBitFlipMutator(max),
                            new DetDoubleBitFlipMutator(max),
                            new DetNibbleFlipMutator(max),
                            new DetSingleByteFlipMutator(max),
                            new DetDoubleByteFlipMutator(max),
                            new DetQuadByteFlipMutator(max),
                            new DetAddSingleByteMutator(max),
                            new DetAddDoubleByteMutator(max),
                            new DetAddQuadByteMutator(max),
                            };

    std::deque<Mutator *> *mutators = new std::deque<Mutator *>();
    for(int i=0; i<N_DET_MUTATORS; i++){
        mutators->push_back(det_mutators[i]);
    }
    return mutators;
}

std::deque<Mutator *> *get_rand_mutators(size_t max){
    Mutator *rand_mutators[] = {
                            new RandSingleBitFlipMutator(max),
                            new RandAddSingleByteMutator(max),
                            new RandAddDoubleByteMutator(max),
                            new RandAddQuadByteMutator(max),
                            new RandOverwriteInterestingSingleByteMutator(max),
                            new RandOverwriteInterestingDoubleByteMutator(max),
                            new RandOverwriteInterestingQuadByteMutator(max),
                            new RandOverwriteRandomByteMutator(max),
                            new RandDeleteRandomBytesMutator(max),
                            new RandCloneRandomBytesMutator(max),
                            new RandOverwriteRandomBytesMutator(max)
                            };

    std::deque<Mutator *> *mutators = new std::deque<Mutator *>();
    for(int i=0; i<N_RAND_MUTATORS; i++){
        mutators->push_back(rand_mutators[i]);
    }
    return mutators;
}

std::deque<Mutator *> *get_all_mutators(size_t max){
   std::deque<Mutator *> *det_mutators = get_det_mutators(max);
   std::deque<Mutator *> *rand_mutators = get_rand_mutators(max);
   std::deque<Mutator *> *mutators = new std::deque<Mutator *>();

   while(det_mutators->size()){
    mutators->push_back(det_mutators->front());
    det_mutators->pop_front();
   }

   while(rand_mutators->size()){
    mutators->push_back(rand_mutators->front());
    rand_mutators->pop_front();
   }

   return mutators;
}










    
