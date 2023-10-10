#ifndef AFL_H
#define AFL_H
/*********************
  * SOME AFL DEFINES *
  ********************/
#include <cstdint>
#define FLIP_BIT(_ar, _b)                  \
 do {                                      \
                                           \
   uint8_t *_arf = (uint8_t *)(_ar);       \
   uint32_t _bf = (_b);                    \
   _arf[(_bf) >> 3] ^= (128 >> ((_bf)&7)); \
                                           \
 } while (0)
// >>3 to index the correct byte,
// &7 to take lowest 3 bits that index within byte, 128==2^7 i.e. 1000 0000 -> bit 0 is leftmost bit?
#define SWAP16(_x)                         \
  ({                                       \
                                           \
    uint16_t _ret = (_x);                  \
    (uint16_t)((_ret << 8) | (_ret >> 8)); \
                                           \
  })

#define SWAP32(_x)                                                        \
  ({                                                                      \
                                                                          \
    uint32_t _ret = (_x);                                                 \
    (uint32_t)((_ret << 24) | (_ret >> 24) | ((_ret << 8) & 0x00FF0000) | \
          ((_ret >> 8) & 0x0000FF00));                                    \
                                                                          \
  })

#define ARITH_MAX 35

#define INTERESTING_8                                    \
  -128,    /* Overflow signed 8-bit when decremented  */ \
      -1,  /*                                         */ \
      0,   /*                                         */ \
      1,   /*                                         */ \
      16,  /* One-off with common buffer size         */ \
      32,  /* One-off with common buffer size         */ \
      64,  /* One-off with common buffer size         */ \
      100, /* One-off with common buffer size         */ \
      127                        /* Overflow signed 8-bit when incremented  */

#define INTERESTING_8_LEN 9

#define INTERESTING_16                                    \
  -32768,   /* Overflow signed 16-bit when decremented */ \
      -129, /* Overflow signed 8-bit                   */ \
      128,  /* Overflow signed 8-bit                   */ \
      255,  /* Overflow unsig 8-bit when incremented   */ \
      256,  /* Overflow unsig 8-bit                    */ \
      512,  /* One-off with common buffer size         */ \
      1000, /* One-off with common buffer size         */ \
      1024, /* One-off with common buffer size         */ \
      4096, /* One-off with common buffer size         */ \
      32767                      /* Overflow signed 16-bit when incremented */

#define INTERESTING_16_LEN 10

#define INTERESTING_32                                          \
  -2147483648LL,  /* Overflow signed 32-bit when decremented */ \
      -100663046, /* Large negative number (endian-agnostic) */ \
      -32769,     /* Overflow signed 16-bit                  */ \
      32768,      /* Overflow signed 16-bit                  */ \
      65535,      /* Overflow unsig 16-bit when incremented  */ \
      65536,      /* Overflow unsig 16 bit                   */ \
      100663045,  /* Large positive number (endian-agnostic) */ \
      2147483647                 /* Overflow signed 32-bit when incremented */

#define INTERESTING_32_LEN 8

#endif // AFL_H