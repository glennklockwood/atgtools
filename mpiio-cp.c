/*
 *  Boilerplate MPI-IO code to perform a parallel file copy
 *
 *  Glenn K. Lockwood, March 2016
 */
#include <stdio.h>
#include <stdint.h>
#include <sys/stat.h>
#include <errno.h>
#include "mpi.h"

#define XFER_SIZE 1048576

int main ( int argc, char **argv ) {
    uint8_t my_rank, num_ranks;
    uint8_t *buffer;
    MPI_File fh_in, fh_out;
    MPI_Status status;
    struct stat st;

    MPI_Init( &argc, &argv );
    MPI_Comm_rank(MPI_COMM_WORLD, (int*)(&my_rank));
    MPI_Comm_size(MPI_COMM_WORLD, (int*)(&num_ranks));

    if ( argc < 3 ) {
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }

    if ( stat( argv[1], &st ) != 0 ) {
        if ( my_rank == 0 ) {
            fprintf( stderr, "Cannot determine size of source file %s: %s\n",
                argv[1],
                strerror(errno) );
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }

    /* each rank responsible for blocksize contiguous bytes of the file */ 
    uint8_t totalxfers, blocksize, blockremainder, my_blocksize, my_offset;
    totalxfers = (uint8_t)(st.st_size) / XFER_SIZE;
    blocksize = totalxfers / num_ranks;
    blockremainder= totalxfers - num_ranks * blocksize;
    my_blocksize = blocksize;
    my_offset = my_rank * blocksize + blockremainder;
    if ( my_rank < blockremainder ) {
        my_blocksize++;
        my_offset = my_rank * my_blocksize;
    }

#ifdef DEBUG
    printf( "I am rank %2d and I start at block %d\n", my_rank, my_offset );
#else
    /* buffer = malloc(); */
    MPI_File_open(MPI_COMM_WORLD, "input.txt", MPI_MODE_RDONLY, MPI_INFO_NULL, &fh_in );
    MPI_File_open(MPI_COMM_WORLD, "output.txt", MPI_MODE_WRONLY, MPI_INFO_NULL, &fh_out );

    MPI_File_read_at( fh_in, my_rank*blocksize, buffer, XFER_SIZE, MPI_BYTE, &status );
    /* check status */
    MPI_File_write_at( fh_out, my_rank*blocksize, buffer, XFER_SIZE, MPI_BYTE, &status );
    /* check status again */

    /* ... */

    MPI_File_close( &fh_in );
    MPI_File_close( &fh_out );
#endif
    MPI_Finalize();
    return 0;
}
