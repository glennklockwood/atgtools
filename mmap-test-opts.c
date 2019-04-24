#define _XOPEN_SOURCE 600
#define _BSD_SOURCE 1

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/resource.h>

#include <fcntl.h>

int main( int argc, char **argv ) {
    struct stat st;
    size_t stride;
    void *values, *vptr;
    unsigned char value;
    struct rusage ru;
    int fd, i;

    if (argc < 2) {
        fprintf(stderr, "Syntax: %s <file to mmap>\n", argv[0]);
        return 0;
    }

    if (!(fd = open(argv[1], O_RDWR, 0))) return 1;

    fstat(fd, &st);

    values = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0 );
    if (values == MAP_FAILED)
        printf("PROT_READ and MAP_PRIVATE failed\n");
    else
        printf("PROT_READ and MAP_PRIVATE worked\n");

    values = mmap(NULL, st.st_size, PROT_WRITE, MAP_PRIVATE, fd, 0 );
    if (values == MAP_FAILED)
        printf("PROT_WRITE and MAP_PRIVATE failed\n");
    else
        printf("PROT_WRITE and MAP_PRIVATE worked\n");

    values = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0 );
    if (values == MAP_FAILED)
        printf("PROT_READ and MAP_SHARED failed\n");
    else
        printf("PROT_READ and MAP_SHARED worked\n");

    values = mmap(NULL, st.st_size, PROT_WRITE, MAP_SHARED, fd, 0 );
    if (values == MAP_FAILED)
        printf("PROT_WRITE and MAP_SHARED failed\n");
    else
        printf("PROT_WRITE and MAP_SHARED worked\n");


    if ( munmap( values, st.st_size ) != 0 )
        return 2;

    close(fd);
    return 0;
}
