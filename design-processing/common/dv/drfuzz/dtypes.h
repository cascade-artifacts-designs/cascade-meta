#ifndef DTYPES_H
#define DTYPES_H
#include <cstdint>
#include <cstddef>

#include "macros.h"
class Testbench; // forward declaration to break cyclic dependencies in headers

struct dinput_t { // TODO: should we make these classes? They got kind of bloated now...
    public:
        uint32_t inputs[N_FUZZ_INPUTS_b32];
        void print();

        void check();
        void clean();
        void print_diff(dinput_t *other);
};

struct doutput_t {
    public:
        uint32_t coverage[N_COV_POINTS_b32];
        uint32_t asserts[N_ASSERTS_b32];

        #ifdef WRITE_COVERAGE
        void dump(Testbench *tb);
        #endif
        void print();
        bool failed();
        void check_failed();
        void check();
        void print_diff(doutput_t *other);
        void print_asserts_diff(doutput_t *other);
        void print_increase(doutput_t *other);
        void add_or(doutput_t *other);
        void init();
};

#endif
