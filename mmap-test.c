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

/*
 * Prototypes
 */
unsigned long get_cached_page_ct(void *file_mmap, long st_size);
int drop_cached_pages( int fd );

/*
 * Principal test
 */
int main( int *argc, char **argv ) {
    struct stat st;
    size_t page_size;
    size_t stride;
    void *values, *vptr;
    unsigned char value;
    int fd, i;
    struct rusage ru;
    int use_random_offset = 1;

    if ( !(fd = open( argv[1], O_RDWR, 0 )) ) return 1;
    fstat( fd, &st );
    values = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0 );

    printf( "%ld pages of the input file are currently in cache.\n", 
        get_cached_page_ct( values, st.st_size ) );

    printf( "\nFlushing file from page cache now.\n" );
    drop_cached_pages( fd );

    printf( "%ld pages of the input file are currently in cache.\n", 
        get_cached_page_ct( values, st.st_size ) );

    if ( values == MAP_FAILED ) {
        close(fd);
        fprintf( stderr, "mmap failed :(\n" );
        return 1;
    }

    getrusage( RUSAGE_SELF, &ru );
    printf( "%ld major, %ld minor page faults before reading values\n",
        ru.ru_majflt,
        ru.ru_minflt );

    page_size = getpagesize();
/*  stride = 8 * page_size + 1024 + 256 + 64 + 16 + 4 + 1; // readahead works on 3.0.101-0.46 */
/*  stride = 8 * page_size + 1024 + 256 + 64 + 16 + 4 + 2; // readahead doesn't work */
    stride = 8 * page_size;
    printf( "\nPage size is %ld bytes, stride is %ld bytes\n", page_size, stride );

/*  madvise( values, st.st_size, MADV_SEQUENTIAL ); */
    if ( use_random_offset ) {
        time_t t;
        srand( (unsigned)time(&t) );
        printf( "File is %12ld bytes; will choose random offsets to read.\n",
            st.st_size );
    }

    printf( "\n%5s   %12s  %4s %5s %5s %12s\n",
        "iter",
        "address",
        "val",
        "major",
        "minor",
        "cached pages" );

    for ( vptr = values, i = 0; i < 100; i++ ) 
    { 
        long offset;
        if ( !use_random_offset ) {
            offset = i*stride;
        }
        else {
            offset = (long)(st.st_size * rand() / RAND_MAX);
        }
        vptr = values + offset;
        /* following line triggers a page fault */
        value = *((unsigned char*)(vptr));
        getrusage( RUSAGE_SELF, &ru );

/*      printf( "%5d   %#010x  %#04x %5ld %5ld %4ld\n",  */
        printf( "%5d   %12ld  %#04x %5ld %5ld %4ld\n", 
            i,
            offset,
            value,
            ru.ru_majflt,
            ru.ru_minflt,
            get_cached_page_ct( values, st.st_size ) );
    }

    printf( "%ld pages of the input file are currently in cache.\n", 
        get_cached_page_ct( values, st.st_size ) );

    if ( munmap( values, st.st_size ) != 0 )
        return 2;

    close(fd);
    return 0;
}

/* 
 * use mincore(2) to determine how many pages comprising a file are resident
 * in memory 
 */
unsigned long get_cached_page_ct(void *file_mmap, long st_size) {
    size_t page_size = getpagesize();
    size_t page_index;
    unsigned char *mincore_vec;
    unsigned long nblocks = 0;

    mincore_vec = calloc(1, (st_size + page_size - 1) / page_size);
    mincore( file_mmap, st_size, mincore_vec );
    for ( page_index = 0; page_index <= st_size/page_size; page_index++)
        if ( mincore_vec[page_index] & 1 )
            nblocks++;

    free(mincore_vec);
    return nblocks;
}

/*
 * use posix_fadvise(2) to signal that a file's pages can be evicted
 */
int drop_cached_pages( int fd ) {
    fdatasync(fd);
    return posix_fadvise(fd, 0, 0, POSIX_FADV_DONTNEED);
}
