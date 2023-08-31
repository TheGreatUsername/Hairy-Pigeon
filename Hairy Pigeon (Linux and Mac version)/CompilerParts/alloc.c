#include "stdlib.h"

#define tapesize 2000000000//20000000000
#define SIZETOL 128
#define ABS(n) ((n) < 0 ? -(n) : (n))
#define GETSIZE(m) (((long*)m)[-1])
#define NULLDEREF(p) ((p) ? *(p) : NULL)

char *tape = NULL; //tape[tapesize];
long tapeind = 0;
void *freed = NULL;

typedef long sizetype;

void *freshalloc(long size) {
    if (!tape) tape = malloc(tapesize);
    if (size < sizeof(void*)) size = sizeof(void*);
    void *result = tape + tapeind;
    tapeind += size + sizeof(sizetype);
    *(sizetype*)result = size;
    result += sizeof(sizetype);
    return result;
}

long afree(void *m) {
    *(void**)m = freed;
    freed = m;
    return 0;
}

void *getfreed(long size) {
    void *lastp = NULL;
    for (void *p = freed; p; p = *(void**)p) {
        long sp = GETSIZE(p);
        if (size >= sp - SIZETOL && size <= sp) {
            if (!lastp) {
                freed = NULLDEREF((void**)p);
            } else {
                *(void**)lastp = NULLDEREF((void**)p);
            }
            return p;
        }
        lastp = p;
    }
    return NULL;
}

void *aalloc(long size) {
    void *result = getfreed(size);
    if (!result) {
        return freshalloc(size);
    }
    return result;
}