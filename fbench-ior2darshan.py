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

#edison-temp    edison_darshanlogs
_DARSHAN_PATHS = [
    "/global/cscratch1/sd/darshanlogs",
    "/global/cscratch1/sd/darshanlogs/edison-temp",
    "/global/cscratch1/sd/darshanlogs/edison_darshanlogs",
    "/global/cscratch1/sd/darshanlogs/edison_3.1.1",
]

_ARGS = None

def main():
    ### track all of the filesystem, date tuples that trigger matches for the
    ### --all option
    found_files = set([])
    found_dirs = {}
    for base_path in _DARSHAN_PATHS:
        found_dirs[base_path] = set([])

    for filename in _ARGS.files:
        jobid_str = filename.split('_')[-1].split('.')[0]
        ior_data = hpcparse.ior.parse(open(filename,'r'))
        yr = ior_data['start'].year
        mo = ior_data['start'].month
        dy = ior_data['start'].day
        start_date = datetime.date(year=yr, month=mo, day=dy)
        end_date = datetime.date(year=ior_data['stop'].year,
                                 month=ior_data['stop'].month,
                                 day=ior_data['stop'].day)

        for base_path in _DARSHAN_PATHS:
            matches = glob.glob( os.path.join( base_path, str(yr), str(mo), str(dy), "*id%s_*" % jobid_str ) )
            if len(matches) > 0:
                for darshan_log in matches:
                    found_files.add( (darshan_log, start_date) )
                    found_dirs[base_path].add( start_date )
                    if end_date != start_date:
                        tmp_date = start_date
                        while tmp_date <= end_date:
                            found_dirs[base_path].add( tmp_date )
                            tmp_date += datetime.timedelta(days=1)

    madedirs = set([])
    for found_file, date in found_files:
        dest_dir = mk_output_dir(date, madedirs)
        madedirs.add(dest_dir)
        cp(found_file, dest_dir)
            

    if _ARGS.all:
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
                    cp(matching_file, dest_dir)

def mk_output_dir(date, madedirs):
    if _ARGS.binbydate:
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

    sys.stdout.write("cp %s %s" % (src, dest))
    if _ARGS.srsly:
        shutil.copyfile(src, dest)
        sys.stdout.write("...done\n")
    else:
        sys.stdout.write("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all", help="copy ALL Darshan logs for the day, not just the IOR one", action="store_true")
    parser.add_argument("--binbydate", help="bin darshan logs into YYYY-MM-DD directories", action="store_true")
    parser.add_argument("--srsly", help="actually create dirs and copy files rather than dryrun", action="store_true")
    parser.add_argument("files", nargs='*', help="IOR outputs to process")
    _ARGS = parser.parse_args()
    main()
