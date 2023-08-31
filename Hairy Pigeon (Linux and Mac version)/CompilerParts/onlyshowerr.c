#include "stdlib.h"
#include "stdio.h"
#include "unistd.h"
#include "string.h"

#define MAX 100000000 //lol
char mypipe[MAX + 10]; //just in case

int main(int argc, char* argv[]) {
  if (!isatty(fileno(stdin))) {
    int i = 0;
    while(i < MAX && -1 != (mypipe[i++] = getchar()));
    mypipe[i-1] = '\0';
    if (strstr(mypipe, "error") != NULL || strstr(mypipe, "Error") != NULL) {
      puts(mypipe);
    }
  }
}
