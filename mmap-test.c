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

struct config_args {
    int random;
    int page_stride;
    int num_pages;
};

/*
 * Prototypes
 */
unsigned long get_cached_page_ct(void *file_mmap, long st_size);
int drop_cached_pages( int fd );
int get_config_args( int argc, char **argv, struct config_args *configs, char ***other_args );

/*
 * Principal test
 */
int main( int argc, char **argv ) {
    struct stat st;
    size_t stride;
    void *values, *vptr;
    unsigned char value;
    struct rusage ru;
    struct config_args configs;
    char **other_args;
    int fd, i;

    get_config_args( argc, argv, &configs, &other_args );

    if ( !(fd = open( other_args[0], O_RDWR, 0 )) ) return 1;
    fstat( fd, &st );
    values = mmap(NULL, st.st_size, PROT_READ, MAP_PRIVATE, fd, 0 );

    if ( values == MAP_FAILED ) {
        close(fd);
        fprintf( stderr, "mmap of %s failed :(\n", other_args[0] );
        return 1;
    }

    printf( "%ld pages of the input file are currently in cache\n", 
        get_cached_page_ct( values, st.st_size ) );

    printf( "\nFlushing file from page cache now\n" );
    drop_cached_pages( fd );

    printf( "%ld pages of the input file are currently in cache\n", 
        get_cached_page_ct( values, st.st_size ) );

    getrusage( RUSAGE_SELF, &ru );
    printf( "%ld major, %ld minor page faults before reading values\n",
        ru.ru_majflt,
        ru.ru_minflt );

    if ( configs.random ) {
        time_t t;
        srand( (unsigned)time(&t) );
        printf( "\nPage size is %ld bytes, access will be random within %ld bytes\n",
            getpagesize(), st.st_size );
    }
    else {
        size_t page_size = getpagesize();
/*      madvise( values, st.st_size, MADV_SEQUENTIAL ); */
/*      stride = PAGE_STRIDE * page_size + 1024 + 256 + 64 + 16 + 4 + 1; // readahead works on 3.0.101-0.46 */
/*      stride = PAGE_STRIDE * page_size + 1024 + 256 + 64 + 16 + 4 + 2; // readahead doesn't work */
        stride = configs.page_stride * page_size;
        printf( "\nPage size is %ld bytes, stride is %ld bytes\n", page_size, stride );
    }

    printf( "\n%5s   %12s  %4s %5s %5s %12s\n",
        "iter",
        "address",
        "val",
        "major",
        "minor",
        "cached pages" );

    for ( vptr = values, i = 0; i < configs.num_pages ; i++ ) 
    { 
        long offset;
        if ( !configs.random )
            offset = i * stride;
        else
            offset = (long)(st.st_size * rand() / RAND_MAX);

        vptr = values + offset;
        /* following line triggers a page fault */
        value = *((unsigned char*)(vptr));
        getrusage( RUSAGE_SELF, &ru );

        if ( configs.num_pages < 1000 || (i % 1000) == 0 ) {
            printf( "%5d   %12ld  %#04x %5ld %5ld %4ld\n", 
                i,
                offset,
                value,
                ru.ru_majflt,
                ru.ru_minflt,
                get_cached_page_ct( values, st.st_size ) );
        }
    }

    printf( "%ld pages of the input file are currently in cache\n", 
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

int get_config_args( int argc, char **argv, struct config_args *configs, char ***other_args )
{
    int aflag = 0;
    int bflag = 0;
    char *cvalue = NULL;
    int index;
    int c;

    *other_args = NULL;

    configs->random = 0;
    configs->page_stride = 1;
    configs->num_pages = 100;

    opterr = 0;
    while ((c = getopt(argc, argv, "rp:n:")) != -1)
        switch (c)
        {
        case 'r':
            configs->random = 1;
            break;
        case 'p':
            configs->page_stride = atoi(optarg);
            if ( configs->page_stride < 1 )
                configs->page_stride = 1;
            break;
        case 'n':
            configs->num_pages = atoi(optarg);
            if ( configs->num_pages < 0 )
                configs->num_pages = 1;
            break;
        case '?':
            if (optopt == 'c' || optopt == 'p' )
                fprintf(stderr, "Option -%c requires an argument.\n", optopt);
            else if (isprint (optopt))
                fprintf(stderr, "Unknown option `-%c'.\n", optopt);
            else
                fprintf(stderr, "Unknown option character `\\x%x'.\n", optopt);
            return 1;
        default:
            abort();
    }

    *other_args = &argv[optind];
    return 0;
}
