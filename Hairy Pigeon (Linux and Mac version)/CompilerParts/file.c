#include "stdio.h"
#include "stdlib.h"
#include "unistd.h"
#include "string.h"

#include "alloc.c"

char * readfile(char * fname) {
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

void writefile(char * fname, char * s) {
    FILE * f = fopen(fname, "w");
    fwrite(s, 1, strlen(s), f);
    fclose(f); //this is erroring
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