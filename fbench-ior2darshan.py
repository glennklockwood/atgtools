#!/usr/bin/env python
"""
Find darshan logfiles corresponding to one or more IOR output logs
"""

import os
import sys
import glob
import shutil
import argparse
import datetime
import hpcparse

_DARSHAN_PATHS = [
    "/global/cscratch1/sd/darshanlogs",
    "/global/cscratch1/sd/darshanlogs/edison-temp",
    "/global/cscratch1/sd/darshanlogs/edison_darshanlogs",
    "/global/cscratch1/sd/darshanlogs/edison_3.1.1",
]

_ARGS = None

def main():
    ### found_files = set of darshan logs generated directly by IOR runs
    found_files = set([])
    ### found_dirs = hash of sets keyed by Darshan log paths; each set contains
    ###              dates which contain one or more found_files
    found_dirs = {}
    for base_path in _DARSHAN_PATHS:
        found_dirs[base_path] = set([])

    for filename in _ARGS.files:
        ### parse each IOR output file to extract date(s) and Slurm jobids
        jobid_str = filename.split('_')[-1].split('.')[0]
        ior_data = hpcparse.ior.parse(open(filename,'r'))
        yr = ior_data['start'].year
        mo = ior_data['start'].month
        dy = ior_data['start'].day
        start_date = datetime.date(year=yr, month=mo, day=dy)
        end_date = datetime.date(year=ior_data['stop'].year,
                                 month=ior_data['stop'].month,
                                 day=ior_data['stop'].day)

        ### search for the Slurm jobid for each IOR output file in all of the
        ### possible Darshan log directories
        for base_path in _DARSHAN_PATHS:
            matches = glob.glob( os.path.join( base_path, str(yr), str(mo), str(dy), "*id%s_*" % jobid_str ) )
            if len(matches) > 0:
                for darshan_log in matches:
                    ### add the IOR job's Darshan log to found_files
                    found_files.add( (darshan_log, start_date) )
                    ### add all dates covered by the Darshan log
                    found_dirs[base_path].add( start_date )
                    if end_date != start_date:
                        tmp_date = start_date
                        while tmp_date <= end_date:
                            found_dirs[base_path].add( tmp_date )
                            tmp_date += datetime.timedelta(days=1)

    madedirs = set([])  ### track which dirs have already be mkdir'ed; do this
                        ### instead of repeatedly os.path.isdir to prevent MDS
                        ### overload and for dryruns
    failures = set([])  ### darshan logs which failed to copy (permission
                        ### issues, etc)

    ### copy all Darshan logs directly corresponding to an IOR log
    for found_file, date in found_files:
        dest_dir = mk_output_dir(date, madedirs)
        madedirs.add(dest_dir)
        try:
            cp(found_file, dest_dir)
        except IOError:
            failures.add(found_file)

    if _ARGS.all:
        ### copy ALL darshan logs for days during which IOR was run
        for base_path, dates in found_dirs.iteritems():
            for date in dates:
                src_dir = os.path.join( base_path, 
                                        str(date.year),
                                        str(date.month),
                                        str(date.day) )
                dest_dir = mk_output_dir(date, madedirs)
                madedirs.add(dest_dir)
                matches = glob.glob(os.path.join(src_dir, "*.darshan*"))
                for matching_file in matches:
                    try:
                        cp(matching_file, dest_dir)
                    except IOError:
                        failures.add(matching_file)

    if len(failures) > 0:
        print "The following source files failed to copy:"
        for failure in failures:
            print "  %s" % failure

def mk_output_dir(date, madedirs):
    if _ARGS.bin_by_date:
        dest_dir = os.path.join( ".", date.strftime("%Y-%m-%d") )
    else:
        dest_dir = "."
    if not os.path.exists(dest_dir) and dest_dir not in madedirs:
        mkdir(dest_dir)
    return dest_dir 

def mkdir(path):
    sys.stdout.write("mkdir -p %s" % path)
    if _ARGS.srsly:
        os.makedirs(path)
        sys.stdout.write("...done\n")
    else:
        sys.stdout.write("\n")

def cp(src, dest):
    if os.path.isdir(dest):
        dest = os.path.join( dest, os.path.basename(src) )

    if _ARGS.ignore_existing and os.path.exists(dest):
        return

    sys.stdout.write("cp %s %s" % (src, dest))
    if _ARGS.srsly:
        shutil.copyfile(src, dest)
        sys.stdout.write("...done\n")
    else:
        sys.stdout.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all", help="copy ALL Darshan logs for the day, not just the IOR one", action="store_true")
    parser.add_argument("--bin-by-date", help="bin darshan logs into YYYY-MM-DD directories", action="store_true")
    parser.add_argument("--srsly", help="actually create dirs and copy files rather than dryrun", action="store_true")
    parser.add_argument("--ignore-existing", help="don't copy files if they already exist in dest", action="store_true")
    parser.add_argument("files", nargs='*', help="IOR outputs to process")
    _ARGS = parser.parse_args()
    main()
