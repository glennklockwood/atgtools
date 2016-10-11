#!/usr/bin/env python
"""
Parses a collection of IOR outputs, determine which H5LMT files contain the data
for those files, then copy the relevant datasets out of those h5lmt files into
new HDF5 files that are compressed and optimized for sharing.

Syntax:
    ./this_script <ior stdout 1> [ior stdout 2 [ior stdout 3 [...]]]

Output:
    New *.hdf5 files in $PWD containing a subset of datasets relevant to
    correlating with IOR.  Any day that an IOR job touches is copied in whole,
    but only a subset of datasets in each H5LMT are transferred.
"""
import os
import sys
import datetime
import subprocess

### set to False to actually generate new HDF5 files
_DRY_RUN = True

### template string for h5lmt file locations
h5lmt_path_template = os.path.join( "/", "global", "project", "projectdirs", "pma", "www", "daily", "%s", "%s.h5lmt")

### map mount points to h5lmt file basenames
fs_map = {
    "scratch1": "edison_snx11025",
    "scratch2": "edison_snx11035",
    "scratch3": "edison_snx11036",
}

### the datasets we want to extract and save to new HDF5 files
relevant_datasets = [
    "FSMissingGroup/FSMissingDataSet",
    "FSStepsGroup/FSStepsDataSet",
    "OSTReadGroup/OSTBulkReadDataSet",
    "OSTWriteGroup/OSTBulkWriteDataSet",
]

### build a list of hdf5 files to process
files_to_process = {}
for output_file in sys.argv[1:]:
    date_0 = None
    date_f = None
    fs = None
    ### assume multiple IOR outputs can be concatenated in a single output file
    with open(output_file, 'r') as fp:
        for line in fp:
            if line.startswith("Run began"):
                date_0 = datetime.datetime.strptime(line.split(':',1)[1].strip(), "%c").date()
            elif line.startswith('Path'):
                fs = line.split()[1].split(os.sep)[1]
            elif line.startswith("Run finished"):
                date_f = datetime.datetime.strptime(line.split(':',1)[1].strip(), "%c").date()
                ### register the h5lmt file(s) for this run
                d = date_0
                while d <= date_f:
                    h5_input = h5lmt_path_template % (d, fs_map[fs])
                    h5_output = "%s_%s.h5lmt" % (fs, d)
                    files_to_process[h5_input] = h5_output
                    d += datetime.timedelta(days=1)

### copy the relevant datasets from the input h5lmt files into new HDF5 files
### for redistribution
for h5_input, h5_output in files_to_process.iteritems():
    for dset in relevant_datasets:
        ### copy only the relevant datasets
        cmd_args = ["h5copy", "-i", h5_input, "-o", h5_output, "-s", dset, "-d", dset, "-p"]
        print ' '.join(cmd_args)
        if not _DRY_RUN:
            ret = subprocess.call( cmd_args )
            if ret != 0:
                sys.stderr.write("ERROR (%d): %s" % (ret, ' '.join(cmd_args)))
                continue

        ### repack the HDF5 file using compression and the latest file format
        cmd_args = ["h5repack", "-L", "-v", "-f", "GZIP=1", h5_output, h5_output.split('.',1)[0] + ".hdf5"]
        print ' '.join(cmd_args)
        if not _DRY_RUN:
            ret = subprocess.call( cmd_args )
            if ret != 0:
                sys.stderr.write("ERROR (%d): %s" % (ret, ' '.join(cmd_args)))
                continue
            os.unlink(h5_output)
