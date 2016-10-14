#!/usr/bin/env python
"""
Parses a collection of IOR outputs, determine which H5LMT files contain the data
for those files, then copy the relevant data out of those h5lmt files int
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
import shutil
import datetime
import subprocess
import argparse

### template string for h5lmt file locations
H5LMT_PATH_TEMPLATE = os.path.join( "/", "global", "project", "projectdirs", "pma", "www", "daily", "%s", "%s.h5lmt")

### map mount points to h5lmt file basenames
FS_MAP = {
    "scratch1": "edison_snx11025",
    "scratch2": "edison_snx11035",
    "scratch3": "edison_snx11036",
}

### the datasets we want to extract and save to new HDF5 files
RELEVANT_DATASETS = [
    "FSMissingGroup/FSMissingDataSet",
    "FSStepsGroup/FSStepsDataSet",
    "OSTReadGroup/OSTBulkReadDataSet",
    "OSTWriteGroup/OSTBulkWriteDataSet",
]

def main(args):
    source_files = set()
    ### build a list of hdf5 files to process
    files_to_process = {}
    for ior_output_file in args.files:
        date_0 = None
        date_f = None
        fs = None
        ### assume multiple IOR outputs can be concatenated in a single output file
        with open(ior_output_file, 'r') as fp:
            source_files.add(ior_output_file)
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
                        h5_input = H5LMT_PATH_TEMPLATE % (d, FS_MAP[fs])
                        source_files.add(h5_input)
                        h5_output = "%s_%s.h5lmt" % (fs, d)
                        files_to_process[h5_input] = ( h5_output, ior_output_file )
                        d += datetime.timedelta(days=1)

    ### copy the relevant datasets from the input h5lmt files into new
    ### intermediate HDF5 files
    failed_files = set()
    success_files = set()
    for original_hdf5, (intermediate_hdf5, ior_output_file) in files_to_process.iteritems():
        for dset in RELEVANT_DATASETS:
            ### copy only the relevant datasets
            cmd_args = ["h5copy", "-i", original_hdf5, "-o", intermediate_hdf5, "-s", dset, "-d", dset, "-p"]
            print ' '.join(cmd_args)
            if not args.dryrun:
                ret = subprocess.call( cmd_args )
                if ret != 0:
                    sys.stderr.write("ERROR (%d): %s" % (ret, ' '.join(cmd_args)))
                    failed_files.add(ior_output_file)
                    failed_files.add(intermediate_hdf5)
                    continue
                else:
                    success_files.add(ior_output_file)
                    success_files.add(intermediate_hdf5)

    ### repack the intermediate HDF5 files using compression and the latest file format
    for intermediate_hdf5 in filter(lambda x: x.endswith('.h5lmt'), success_files):
        new_hdf5 = intermediate_hdf5.split('.',1)[0] + ".hdf5"
        cmd_args = ["h5repack", "-L", "-v", "-f", "GZIP=1", intermediate_hdf5, new_hdf5]
        print ' '.join(cmd_args)
        if not args.dryrun:
            ret = subprocess.call( cmd_args )
            if ret != 0:
                sys.stderr.write("ERROR (%d): %s" % (ret, ' '.join(cmd_args)))
                failed_files.add(ior_output_file)
                failed_files.add(intermediate_hdf5)
                failed_files.add(new_hdf5)
                continue
            else:
                success_files.add(ior_output_file)
                success_files.add(intermediate_hdf5)
                success_files.add(new_hdf5)
            os.unlink(intermediate_hdf5)

    ### Find newly created HDF5 files that should be dropped because they
    ### correspond exclusively to failed runs or corrupt original HDF5 files
    for file in failed_files ^ (failed_files & success_files):
        if file not in source_files: # hdf5 files are ones we create.  they are never a source file
            if os.path.isfile(file):
                print "rm %s" % file

    ### Copy the original IOR output files that we used to generate these new
    ### HDF5 files to this directory
    for file in success_files:
        if file in source_files and not file.endswith('h5lmt'): # files that we don't create, but we want
            print "cp %s ." % file

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", help="only simulate what will really happen", action="store_true")
    parser.add_argument("-v", "--verbose", help="print additional messages about what is happening", action="store_true")
    parser.add_argument("files", nargs='*', help="IOR outputs to process")
    args = parser.parse_args()
    main(args)
