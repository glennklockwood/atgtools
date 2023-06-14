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

Alternatively, you can explicitly reprocess a single h5lmt file using

    ./this_script --h5in /path/to/rawfile.h5lmt --h5out ./my_processed_data.hdf5
"""
import os
import sys
import datetime
import tempfile
import subprocess
import argparse
import StringIO
import warnings
import hpcparse

### template string for h5lmt file locations
H5LMT_PATH_TEMPLATE = os.path.join( "/", "global", "project", "projectdirs", "pma", "www", "daily", "%s", "%s.h5lmt")

### the datasets we want to extract and save to new HDF5 files
RELEVANT_DATASETS = [
    "FSMissingGroup/FSMissingDataSet",
    "FSStepsGroup/FSStepsDataSet",
    "OSTReadGroup/OSTBulkReadDataSet",
    "OSTWriteGroup/OSTBulkWriteDataSet",
    "OSSCPUGroup/OSSCPUDataSet",
]

def ior_to_hdf5_files( ior_outputs ):
    """
    input: a list of file names containing IOR's stdout messages
    output: tuple containing
        1. list of h5lmt file names corresponding to input files
        2. subset of input that was used to generate output #1

    Can handle files that contain concatenated IOR outputs.
    """
    valid_inputs = set()
    h5lmt_files = set()
    for filename in ior_outputs:
        stdout_str = ""
        with open(filename, 'r') as fp:
            for line in fp:
                if line.startswith("Run began"):
                    stdout_str = line
                elif line.startswith("Run finished"):
                    stdout_str += line
                    ior_data = hpcparse.ior.parse(StringIO.StringIO(stdout_str))
                    stdout_str = ""

                    ### deal with malformed outputs
                    try:
                        date = ior_data['start'].date()
                        date_stop = ior_data['stop'].date()
                        fs = ior_data['path'].strip(os.sep).split(os.sep)[0]
                    except KeyError:
                        warnings.warn("Malformed IOR output %s" % filename)
                        continue

                    ### register the h5lmt file(s) for this run
                    while date <= date_stop:
                        h5input = H5LMT_PATH_TEMPLATE % (date, hpcparse.FS_MAP[fs])
                        if os.path.isfile(h5input):
                            h5lmt_files.add(h5input)
                            valid_inputs.add(filename)
                        date += datetime.timedelta(days=1)
                elif len(stdout_str) > 0:
                    stdout_str += line

    return h5lmt_files, valid_inputs


def convert_and_copy( src, dest, datasets, srsly=False ):
    """
    Take a source hdf5 file and a set of datasets and produce a dest hdf5 file
    that contains only those datasets and that has been repacked.
    """
    if not os.path.isfile(src):
        return -1

    temp = tempfile.NamedTemporaryFile()
    for dset in datasets:
        ### copy only the relevant datasets
        cmd_args = ["h5copy", "-i", src, "-o", temp.name, "-s", dset, "-d", dset, "-p"]
        if args.dryrun:
            print ' '.join(cmd_args)
            ret = 0
        else:
            ret = subprocess.call( cmd_args )

    cmd_args = ["h5repack", "-L", "-v", "-f", "GZIP=1", temp.name, dest]
    if args.dryrun:
        print ' '.join(cmd_args)
        ret = 0
    else:
        ret += subprocess.call( cmd_args )
    temp.close()

    return ret

def suggest_name( src ):
    """
    Suggest a new name for an h5lmt file.
    """
    date = src.split(os.sep)[-2]
    basename = os.path.basename(src).split('.', 2)[0]
    if basename in hpcparse.FS_MAP_REV:
        return hpcparse.FS_MAP_REV[basename] + "_" + date + ".hdf5"
    else:
        return basename + "_" + date + ".hdf5"


def mine_ior_and_convert(args):
    """
    Receive a bunch of IOR output logs, extract the relevant dates, find H5LMT
    files corresponding to those dates, then convert+repack+copy those H5LMT
    files
    """
    h5lmt_files, valid_inputs = ior_to_hdf5_files( args.files )

    failed_files = set()
    for h5lmt_file in h5lmt_files:
        new_file = suggest_name(h5lmt_file)
        ret = convert_and_copy(h5lmt_file, new_file, RELEVANT_DATASETS, not args.dryrun)
        if ret != 0:
            failed_files.add(new_file)

    for failed_file in failed_files:
        print "rm " + failed_file

    for valid_input in valid_inputs:
        print "cp %s ." % valid_input

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", help="only simulate what will really happen", action="store_true")
    parser.add_argument("-v", "--verbose", help="print additional messages about what is happening", action="store_true")
    parser.add_argument("--h5in", help="hdf5 file to convert; must specify with --h5out")
    parser.add_argument("--h5out", help="output file of --h5in")
    parser.add_argument("files", nargs='*', help="IOR outputs to process")
    args = parser.parse_args()

    if args.h5in is not None and args.h5out is None:
        sys.exit("--h5out must be specified with --h5in")
    elif args.h5in is not None and args.h5out is not None:
        ret = convert_and_copy(args.h5in, args.h5out, RELEVANT_DATASETS, srsly=True)
        if ret != 0:
            sys.exit("convert_and_copy returned error %d" % ret)
    else:
        mine_ior_and_convert(args)
