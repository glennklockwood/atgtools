/*
 *  Boilerplate MPI-IO code to perform a parallel file copy
 *
 *  Glenn K. Lockwood, March 2016
 */

#define _XOPEN_SOURCE 600
#define _FILE_OFFSET_BITS 64

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>
#include <string.h>
#include "mpi.h"

#define XFER_SIZE 1048576

int main ( int argc, char **argv ) {
    int my_rank, num_ranks, ret;
    uint8_t *buffer;
    struct stat st;
    struct timespec t0, tf, dt;
    off_t bytes_copied = 0;
    char *f_in, *f_out;
    double walltime, max_walltime;
    MPI_File fh_in, fh_out;
    MPI_Status status;

    MPI_Init( &argc, &argv );
    MPI_Comm_rank(MPI_COMM_WORLD, &my_rank);
    MPI_Comm_size(MPI_COMM_WORLD, &num_ranks);

    if ( argc < 3 ) {
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }
    f_in = argv[1];
    f_out = argv[2];

    if ( stat( f_in, &st ) != 0 ) {
        if ( my_rank == 0 ) {
            fprintf( stderr, "Cannot determine size of source file %s: %s\n",
                f_in,
                strerror(errno) );
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }
    else {
        printf( "Copying %s to %s (%ld bytes)\n", f_in, f_out, st.st_size );
    }

    /* each rank responsible for blocksize contiguous bytes of the file */ 
    off_t totalxfers, blocksize, blockremainder, my_blocksize, my_offset;
    totalxfers = st.st_size / XFER_SIZE;
    blocksize = totalxfers / num_ranks;
    blockremainder= totalxfers - num_ranks * blocksize;
    my_blocksize = blocksize;
    my_offset = my_rank * blocksize + blockremainder;
    if ( my_rank < blockremainder ) {
        my_blocksize++;
        my_offset = my_rank * my_blocksize;
    }

    if ( my_rank == 0 ) {
        printf( "Total file size: %ld\nTotal blocks: %ld (%ld bytes)\n",
            st.st_size,
            totalxfers,
            totalxfers * XFER_SIZE );
    }

    MPI_Barrier(MPI_COMM_WORLD);

    printf( "I am rank %2d and I cover bytes %12ld - %12ld\n", 
        my_rank, 
        my_offset*XFER_SIZE, 
        (my_offset + my_blocksize)*XFER_SIZE-1 );

    MPI_Barrier(MPI_COMM_WORLD);

    if ( my_rank == 0 ) {
        if ( st.st_size > totalxfers*XFER_SIZE ) {
            printf( "Rank %d will copy the residual bytes %ld to %ld\n",
                my_rank,
                totalxfers*XFER_SIZE,
                totalxfers*XFER_SIZE + (st.st_size - totalxfers*XFER_SIZE - 1) );
        }
    }

    MPI_Barrier(MPI_COMM_WORLD);

#ifndef DEBUG
    clock_gettime(CLOCK_MONOTONIC, &t0);

    MPI_File_open(MPI_COMM_WORLD, f_in, MPI_MODE_RDONLY, MPI_INFO_NULL, &fh_in );
    MPI_File_open(MPI_COMM_WORLD, f_out, MPI_MODE_WRONLY|MPI_MODE_CREATE, MPI_INFO_NULL, &fh_out );

    buffer = malloc(XFER_SIZE);
    for ( int i = my_offset; i < my_offset + my_blocksize; i++ ) {
        MPI_File_read_at( fh_in, i*XFER_SIZE, buffer, XFER_SIZE, MPI_BYTE, &status );
        /* check status */
        MPI_File_write_at( fh_out, i*XFER_SIZE, buffer, XFER_SIZE, MPI_BYTE, &status );
        bytes_copied += XFER_SIZE;
        /* check status again */
    }

    MPI_Barrier(MPI_COMM_WORLD);

    /* copy the last piece of the file */
    if ( my_rank == 0
    &&   st.st_size > totalxfers*XFER_SIZE ) {
        MPI_File_read_at( fh_in, totalxfers*XFER_SIZE, buffer, (st.st_size - totalxfers*XFER_SIZE), MPI_BYTE, &status );
        /* check status */
        MPI_File_write_at( fh_out, totalxfers*XFER_SIZE, buffer, (st.st_size - totalxfers*XFER_SIZE), MPI_BYTE, &status );
        bytes_copied += (st.st_size - totalxfers*XFER_SIZE);
        /* check status again */
    }

    MPI_File_close( &fh_in );
    MPI_File_close( &fh_out );

    clock_gettime(CLOCK_MONOTONIC, &tf);

    free(buffer);

    if ( (tf.tv_nsec - t0.tv_nsec) < 0 ) {
        dt.tv_sec = tf.tv_sec - t0.tv_sec - 1;
        dt.tv_nsec = 1000000000 + tf.tv_nsec - t0.tv_nsec;
    } 
    else {
        dt.tv_sec = tf.tv_sec - t0.tv_sec;
        dt.tv_nsec = tf.tv_nsec - t0.tv_nsec;
    }
    walltime = dt.tv_sec + dt.tv_nsec / 1e9;

    printf( "Rank %4d copied %12ld bytes in %f sec (%.2f MiB/sec)\n",
        my_rank,
        bytes_copied,
        walltime, 
        bytes_copied / 1024 / 1024 / walltime );
#endif

    /* implicit barrier here */
    MPI_Reduce( &walltime, &max_walltime, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD );

    if ( my_rank == 0 ) {
        printf( "Overall copied %ld bytes in %f seconds (%.2f MiB/sec)\n",
            st.st_size,
            max_walltime,
            (double)st.st_size / max_walltime / 1024.0 / 1024.0 );
    }

    MPI_Finalize();
    return 0;
}
