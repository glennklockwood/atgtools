/*
 *  Demonstrate how to read a value from a file via both POSIX read() and
 *  dereferencing an mmapped file
 *
 */
#define _XOPEN_SOURCE 600
#define _BSD_SOURCE 1

#define FILE_OFFSET 12345
#define READ_LENGTH 1048576

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/resource.h>

#include <fcntl.h>

long get_majflt( void ) {
    struct rusage ru;

    getrusage( RUSAGE_SELF, &ru );

    return ru.ru_majflt;
}

int read_via_mmap( const char *file, off_t offset, char *output, long n ) {
    struct stat stat_buf;
    void *map;
    int fd;

    fd = open( file, O_RDONLY );
    if ( fd < 0 ) {
        perror( "open failed" );
        return 1;
    }

    if ( fstat( fd, &stat_buf ) != 0 ) {
        close(fd);
        perror( "stat failed" );
        return 1;
    }

    map = mmap(NULL, stat_buf.st_size, PROT_READ, MAP_PRIVATE, fd, 0 );
    if ( map == MAP_FAILED ) {
        close(fd);
        perror( "mmap failed" );
        return 1;
    }

    /* read byte via mmap - no explicit seek necessary */
    memcpy( output, ((char*)map + offset), n );

    if ( munmap( map, stat_buf.st_size ) != 0 ) {
        perror( "munmap failed" );
        return 2;
    }
    close(fd);

    return 0;
}

int read_via_read( const char *file, off_t offset, char *output, long n ) {
    int fd;

    fd = open( file, O_RDONLY );
    if ( fd < 0 ) {
        perror( "open failed" );
        return 1;
    }

    /* seek via posix */
    if ( lseek( fd, offset, SEEK_SET ) == -1 ) {
        perror( "lseek failed" );
        close(fd);
        return 1;
    }

    /* read via posix */
    if ( read(fd, output, n) < 0 ) {
        perror( "read failed" );
        close(fd);
        return 1;
    }

    close(fd);
    return 0;
}

int main( int argc, char **argv ) {
    int i;
    unsigned char value[READ_LENGTH];

    for ( i = 0; i < READ_LENGTH; i++ ) value[i] = 0;

    printf( "%ld major faults before reading %ld bytes via mmap\n", get_majflt(), READ_LENGTH );
    read_via_mmap( argv[1], FILE_OFFSET, value, READ_LENGTH );
    printf( "mmap value   %ld is %#8x\n", FILE_OFFSET, *value );
    printf( "%ld major faults after reading\n", get_majflt() );

    for ( i = 0; i < READ_LENGTH; i++ ) value[i] = 0;

    printf( "%ld major faults before reading %ld bytes via read(2)\n", get_majflt(), READ_LENGTH );
    read_via_read( argv[1], FILE_OFFSET, value, READ_LENGTH );
    printf( "posix value  %ld is %#8x\n", FILE_OFFSET, *value );
    printf( "%ld major faults after reading\n", get_majflt() );

    return 0;
}
