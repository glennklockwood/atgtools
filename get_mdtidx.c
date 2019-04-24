#include <stdio.h>
#include <fcntl.h>
#include <lustre/lustreapi.h>

int main( int *argc, char **argv ) {
    int fd;
    int mdtidx;

    if ( *argc < 2 ) {
        fprintf( stderr, "Syntax: %s <file>\n", argv[0] );
        return 1;
    }
    fd = open( argv[1], 0 );
    if ( fd < 0 ) {
        fprintf( stderr, "Could not open file %s\n", argv[1] );
        return 1;
    }
    llapi_file_fget_mdtidx( fd, &mdtidx );

    printf( "mdxidx: %d\n", mdtidx );
    return 0;
}
