#include "stdio.h"
#include "stdlib.h"
#include "unistd.h"
#include "string.h"
#include "math.h"

#include "alloc.c"

#define longify(n) (*(long*)&n)
#define dubify(n) (*(double*)&n)

#ifdef __APPLE__
    int ismac() {return 1;}
    int islinux() {return 0;}
#elif __linux
    int ismac() {return 0;}
    int islinux() {return 1;}
#endif

char * readfileold(char * fname) {
    FILE * f = fopen(fname, "r");
    if (f == NULL) {
        printf("ERROR couldn't open '%s'\n", fname);
        exit(1);
    }
    fseek(f, 0L, SEEK_END); // seek to end
    int size = ftell(f); // find size of file by checking end
    rewind(f); // back to the beginning for reading
    char * buffer = calloc(1, size+1); // allocate enough memory.
    int read = fread(buffer, 1, size, f);  // read in the file
    fclose(f);
    return buffer;
}

char * readfile(char * fname) {
    FILE *f = fopen(fname, "rb");
    fseek(f, 0, SEEK_END);
    int64_t fsize = ftell(f);
    fseek(f, 0, SEEK_SET);  /* same as rewind(f); */

    char *string = malloc(fsize + 1 + sizeof(fsize));
    *(int64_t*)string = fsize;
    int read = fread(string + sizeof(fsize), fsize, 1, f);
    fclose(f);

    // string[fsize + sizeof(fsize)] = 0;

    return string;
}

void oldwritefile(char * fname, char * s) {
    FILE * f = fopen(fname, "w");
    fwrite(s, 1, strlen(s), f);
    fclose(f);
}

void writefile(char * fname, char * s) {
    FILE * f = fopen(fname, "w");
    fwrite(s+8, 1, *(int64_t*)s, f);
    fclose(f);
}

long dubtolong(long n) {
    return (long)(*(double*)&n);
}

long longtodub(long n) {
    double d = n;
    return *(long*)&d;
}

void printdub(long d) {
    printf("%f", *(double*)&d);
}

void noop(long e) {}

long hpcos(long n) {
    double d = cos(dubify(n));
    return longify(d);
}

long hpsin(long n) {
    double d = sin(dubify(n));
    return longify(d);
}

long hpacos(long n) {
    double d = acos(dubify(n));
    return longify(d);
}

long hpasin(long n) {
    double d = asin(dubify(n));
    return longify(d);
}

long hpatan2(long n, long o) {
    double d = atan2(dubify(n), dubify(o));
    return longify(d);
}

long hpsqrt(long n) {
    double d = sqrt(dubify(n));
    return longify(d);
}

long hppi() {
    double d = M_PI;
    return longify(d);
}
