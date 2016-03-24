/*
 *  Boilerplate MPI-IO code to perform a parallel file copy
 *
 *  Glenn K. Lockwood, March 2016
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/stat.h>
#include <errno.h>
#include "mpi.h"

#define XFER_SIZE 1048576

int main ( int argc, char **argv ) {
    int my_rank, num_ranks, ret;
    uint8_t *buffer;
    MPI_File fh_in, fh_out;
    MPI_Status status;
    struct stat st;

    MPI_Init( &argc, &argv );
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &num_ranks);

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
    else {
        printf( "Copying %s to %s\n", argv[1], argv[2] );
    }

    /* each rank responsible for blocksize contiguous bytes of the file */ 
    int totalxfers, blocksize, blockremainder, my_blocksize, my_offset;
    totalxfers = (int)(st.st_size) / XFER_SIZE;
    blocksize = totalxfers / num_ranks;
    blockremainder= totalxfers - num_ranks * blocksize;
    my_blocksize = blocksize;
    my_offset = my_rank * blocksize + blockremainder;
    if ( my_rank < blockremainder ) {
        my_blocksize++;
        my_offset = my_rank * my_blocksize;
    }

    if ( my_rank == 0 ) {
        printf( "Total file size: %d\nTotal blocks: %d (%d bytes)\n",
            st.st_size,
            totalxfers,
            totalxfers * XFER_SIZE );
    }

    MPI_Barrier(MPI_COMM_WORLD);

    printf( "I am rank %2d and I cover bytes %9d - %9d\n", 
        my_rank, 
        my_offset*XFER_SIZE, 
        (my_offset + my_blocksize)*XFER_SIZE-1 );

    MPI_Barrier(MPI_COMM_WORLD);

    if ( my_rank == 0 ) {
        if ( st.st_size > totalxfers*XFER_SIZE ) {
            printf( "Rank %d will copy the residual bytes %d to %d\n",
                my_rank,
                totalxfers*XFER_SIZE,
                totalxfers*XFER_SIZE + (st.st_size - totalxfers*XFER_SIZE - 1) );
        }
    }

#ifndef DEBUG
    ret = MPI_File_open(MPI_COMM_WORLD, argv[1], MPI_MODE_RDONLY, MPI_INFO_NULL, &fh_in );
    if ( ret != 0 ) fprintf( stderr, "MPI_File_open of %s returned %d\n", argv[1], ret );
    ret = MPI_File_open(MPI_COMM_WORLD, argv[2], MPI_MODE_WRONLY, MPI_INFO_NULL, &fh_out );
    if ( ret != 0 ) fprintf( stderr, "MPI_File_open of %s returned %d\n", argv[1], ret );

    buffer = malloc(XFER_SIZE);
    for ( int i = my_offset; i < my_offset + my_blocksize; i++ ) {
        MPI_File_read_at( fh_in, i*XFER_SIZE, buffer, XFER_SIZE, MPI_BYTE, &status );
        /* check status */
        MPI_File_write_at( fh_out, i*XFER_SIZE, buffer, XFER_SIZE, MPI_BYTE, &status );
        /* check status again */
    }

    MPI_Barrier(MPI_COMM_WORLD);

    /* copy the last piece of the file */
    if ( my_rank == 0
    &&   st.st_size > totalxfers*XFER_SIZE ) {
        MPI_File_read_at( fh_in, totalxfers*XFER_SIZE, buffer, (st.st_size - totalxfers*XFER_SIZE), MPI_BYTE, &status );
        /* check status */
        MPI_File_write_at( fh_out, totalxfers*XFER_SIZE, buffer, (st.st_size - totalxfers*XFER_SIZE), MPI_BYTE, &status );
        /* check status again */
    }
    free(buffer);

    MPI_File_close( &fh_in );
    MPI_File_close( &fh_out );
#endif
    MPI_Finalize();
    return 0;
}
