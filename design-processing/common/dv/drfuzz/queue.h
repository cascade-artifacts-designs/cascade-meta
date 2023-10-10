#ifndef QUEUE_H
#define QUEUE_H

#include <deque>

#include "macros.h"
#include "dtypes.h"


// this Queue class represents one set of inputs to be applied in succession to the DUT
class Queue {
    private:
        dinput_t *last_input;
        doutput_t *last_output;
        doutput_t *acc_output;
        doutput_t *ini_output;
        void accumulate_output(doutput_t *);

    public:
        std::deque<dinput_t *> inputs; // inputs to DUT, FIFO
        std::deque<doutput_t *> outputs; // outputs from DUT, FIFO

        bool has_another_input();
        dinput_t *pop_tb_input();
        std::deque<dinput_t *> *pop_tb_inputs();
        void push_tb_output(doutput_t *tb_output);
        void push_tb_outputs(std::deque<doutput_t *> *outputs);
        void push_tb_input(dinput_t *tb_input);
        void push_tb_inputs(std::deque<dinput_t *> *inputs);
        void clear_tb_outputs();
        void clear_tb_inputs();
        void generate_inputs(int n_inputs = N_MAX_INPUTS);
        void seed();
        void print_inputs();
        void print_outputs();
        void print_accumulated_output();
        doutput_t *get_accumulated_output();
        void clear_accumulated_output();
        int get_coverage_amount();
        Queue *copy();
        size_t size();
        bool is_equal(Queue* other);
        void print_diff(Queue *other);
        ~Queue(){
            this->clear_tb_inputs();
            this->clear_tb_outputs();
        }
};
#endif // QUEUE_H