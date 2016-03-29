#!/usr/bin/env python
#
#  Parses the debugging output that is emitted by my instrumented BLAST
#
#  Glenn K. Lockwood,                                            November 2015
#

import sys
import os

#!/bin/bash
# Code      secs    nanosec  oid addr           cached?
# CSeqDBVol 4858543 16896912 182 0x2aab552bb84c 0
# CSeqDBVol 4858543 16899100 183 0x2aab552bb894 0
# CSeqDBVol 4858543 16901257 184 0x2aab552bb8c4 0
#
_LEGIT_KEYS = [ 'CSeqDBVol', 'CSeqDBImpl', 'BlastNaWordFinder', 'BNAWF-Loop' ]
_PAGE_SIZE = 4096

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit("Syntax: %s <blastn stdout>" % sys.argv[0] )
    input = open( sys.argv[1], 'r' )

    output_files = {}

    base_sec = -1L
    base_nsec = -1L
    base_addr = -1L
    access_num = 0L
    for line in input:
        field = line.split()
        if len(field) != 6 or field[0] not in _LEGIT_KEYS:
            continue
        try:
            key = field[0]
            sec = long(field[1])
            nsec = long(field[2])
            oid = int(field[3])
            addr = long(field[4], 16)
            cached = int(field[5])
        except ValueError:
            continue

        if base_sec < 0:
            base_sec = sec
        if base_nsec < 0:
            base_nsec = nsec
        if base_addr < 0:
            base_addr = addr
            base_page = addr - ( addr % _PAGE_SIZE )

        rel_addr = addr - base_addr
        page_addr = addr - ( addr % _PAGE_SIZE ) - base_page

        # really filthy recast of two longs into a float
        if (nsec - base_nsec) < 0:
            dt_sec = sec - base_sec - 1
            dt_nsec = 1000000000 + nsec - base_nsec
        else:
            dt_sec = sec - base_sec
            dt_nsec = nsec - base_nsec
        dt = float( "%ld" % dt_sec + "." + "%09ld" % dt_nsec )

        output_file_key = "%s.%d" % (key.lower(), cached)
        if output_file_key not in output_files:
            output_files[output_file_key] = {}
            output_files[output_file_key]['addresses'] = open( 'addresses.%s' % output_file_key, 'w' )
            output_files[output_file_key]['addresses-10th'] = open( 'addresses.%s-10th' % output_file_key, 'w' )
            output_files[output_file_key]['addresses-100th'] = open( 'addresses.%s-100th' % output_file_key, 'w' )
            output_files[output_file_key]['pages'] = open( 'pages.%s' % output_file_key, 'w' )
            output_files[output_file_key]['pages-10th'] = open( 'pages.%s-10th' % output_file_key, 'w' )
            output_files[output_file_key]['pages-100th'] = open( 'pages.%s-100th' % output_file_key, 'w' )
            output_files[output_file_key]['n'] = 0

        output_line = "%ld %s %.9f %d %ld %d\n" % ( access_num, key, dt, oid, rel_addr, cached )

        output_files[output_file_key]['addresses'].write( output_line )
        if (output_files[output_file_key]['n'] % 10) == 0:
            output_files[output_file_key]['addresses-10th'].write( output_line )
        if (output_files[output_file_key]['n'] % 100) == 0:
            output_files[output_file_key]['addresses-100th'].write( output_line )

        output_line = "%ld %s %.9f %d %ld %d\n" % ( access_num, key, dt, oid, page_addr, cached )

        output_files[output_file_key]['pages'].write( output_line )
        if (output_files[output_file_key]['n'] % 10) == 0:
            output_files[output_file_key]['pages-10th'].write( output_line )

        if (output_files[output_file_key]['n'] % 100) == 0:
            output_files[output_file_key]['pages-100th'].write( output_line )
 
        output_files[output_file_key]['n'] += 1
        access_num += 1
        
        if access_num % 100000 == 0:
            sys.stdout.write('.')
            sys.stdout.flush()

    print "ok usa"
    for _, k in output_files.iteritems():
        for _, fp in k.iteritems():
            if hasattr(fp, 'close'):
                fp.close()
