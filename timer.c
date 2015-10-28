/******************************************************************************
 *  Demonstrate the use of high-resolution timers.  Link with -lrt
 *
 *  Glenn K. Lockwood                                           October 2015
 ******************************************************************************/

#include <stdio.h>
#include <time.h>
#include <math.h>
#include <stdlib.h>

#define ARRAY_SIZE 4 * 1024 * 1024
 
int main( int argc, char **argv )
{
    struct timespec t0, tf, dt;
    long stride;
    long i;
    double *array, value;

    if ( argc < 2 || !(stride = atol( argv[1] )) ) {
        fprintf( stderr, "Syntax: %s <stride>\n", argv[0] );
        return 1;
    }

    if ( !(array = malloc( sizeof(*array) * ARRAY_SIZE * stride)) ) {
        perror( "malloc failed" );
        return 1;
    }

    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t0);

    /* 
     * do some work here 
     */
    for (i = 0; i < ARRAY_SIZE; i++ )
        value = array[i*stride] * 2.0e6;

    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &tf);

    if ( (tf.tv_nsec - t0.tv_nsec) < 0 ) {
        dt.tv_sec = tf.tv_sec - t0.tv_sec - 1;
        dt.tv_nsec = 1000000000 + tf.tv_nsec - t0.tv_nsec;
    } 
    else {
        dt.tv_sec = tf.tv_sec - t0.tv_sec;
        dt.tv_nsec = tf.tv_nsec - t0.tv_nsec;
    }

    printf( "%f sec in %ld steps with %ld-byte stride\n",
        dt.tv_sec + dt.tv_nsec / 1e9, 
        i, 
        stride*sizeof(*array) );

    return 0;
}
