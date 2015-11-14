#!/usr/bin/env python
#
# Given an h5lmt file, returns the total MiB moved as well as peak transfer rate
#

import datetime
import h5py
import sys
import os

### Transposing gives per-time maxes instead of per-OST, but it is VERY slow
_TRANSPOSE = False

_BYTES_TO_MIB = 1.0 / 1024.0 / 1024.0

### Decode some additional metadata from the file path.  This will not work
### outside of NERSC systems.  Assumes paths that look like
###     YYYY-MM_DD/filesystem.h5lmt
filepath = os.path.abspath( sys.argv[1] )
date_str, fs_str = filepath.split( os.sep )[-2:]
date = datetime.datetime.strptime( date_str, "%Y-%m-%d" )
fs_str = fs_str.rsplit('.', 1)[0]

f = h5py.File( filepath, 'r' )

write_bytes = 0.0
read_bytes = 0.0
max_write_bytes = 0.0
max_read_bytes = 0.0

if _TRANSPOSE:
    for j in range( len(f['OSTReadGroup/OSTBulkReadDataSet'][0]) ): # loop over time
        i = f['OSTReadGroup/OSTBulkReadDataSet'][:,j]
        read_bytes += sum(i) # sum the reads for all OSTs
        aggr_read = sum(i)
        if aggr_read > max_read_bytes:
            max_read_bytes = aggr_read
        max_read_bytes /= 5.0 # 5 seconds per time slice gets us MB/s

    for j in range( len(f['OSTWriteGroup/OSTBulkWriteDataSet'][0]) ):
        i = f['OSTWriteGroup/OSTBulkWriteDataSet'][:,j]
        write_bytes += sum(i)
        aggr_write = max(i)
        if aggr_write > max_write_bytes:
            max_write_bytes = aggr_write
        max_writes_bytes /= 5.0 # 5 seconds per time slice gets us MB/s
else:
    for i in f['OSTReadGroup/OSTBulkReadDataSet']:  # loop over OSTs
        read_bytes += sum(i) # sum the day's reads for this OST
        aggr_read = sum(i)
        if aggr_read > max_read_bytes:
            max_read_bytes = aggr_read

    for i in f['OSTWriteGroup/OSTBulkWriteDataSet']: 
        write_bytes += sum(i)
        aggr_write = max(i)
        if aggr_write > max_write_bytes:
            max_write_bytes = aggr_write

print "%s %s %.2f %.2f %.2f %.2f" % (
    fs_str,
    date.strftime("%s"),
    read_bytes * _BYTES_TO_MIB,
    write_bytes * _BYTES_TO_MIB,
    max_read_bytes * _BYTES_TO_MIB,
    max_write_bytes * _BYTES_TO_MIB )
