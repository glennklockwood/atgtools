#!/usr/bin/env python
"""
Find darshan logfiles corresponding to one or more IOR output logs
"""

import os
import glob
import argparse
import hpcparse

#edison-temp    edison_darshanlogs
_DARSHAN_PATHS = [
    "/global/cscratch1/sd/darshanlogs",
    "/global/cscratch1/sd/darshanlogs/edison-temp",
    "/global/cscratch1/sd/darshanlogs/edison_darshanlogs",
    "/global/cscratch1/sd/darshanlogs/edison_3.1.1",
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs='*', help="IOR outputs to process")
    args = parser.parse_args()

    for filename in args.files:
        jobid_str = filename.split('_')[-1].split('.')[0]
        ior_data = hpcparse.ior.parse(open(filename,'r'))
        yr = ior_data['start'].year
        mo = ior_data['start'].month
        dy = ior_data['start'].day

        for base_path in _DARSHAN_PATHS:
            matches = glob.glob( os.path.join( base_path, str(yr), str(mo), str(dy), "*id%s_*" % jobid_str ) )
            if len(matches) > 0:
                for darshan_log in matches:
                    print "cp darshan_log ."
