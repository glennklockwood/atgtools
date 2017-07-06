#!/usr/bin/env python
"""
Scrape large numbers of h5lmt files to determine how much data was read and
written to Lustre over the lifetime of a file system.
"""

import argparse
import h5py
import multiprocessing

BYTES_TO_GIBS = 2.0**-30

def summarize_h5lmt_file(h5lmt_file):
    print "Processing", h5lmt_file
    f = h5py.File(h5lmt_file, 'r')
    timestep = f['/FSStepsGroup/FSStepsDataSet'][1] - f['/FSStepsGroup/FSStepsDataSet'][0]
    return {
        'date': f['/FSStepsGroup/FSStepsDataSet'].attrs['day'],
        'read_gibs': f['/OSTReadGroup/OSTBulkReadDataSet'][:,:].sum() * timestep * BYTES_TO_GIBS,
        'write_gibs': f['/OSTWriteGroup/OSTBulkWriteDataSet'][:,:].sum() * timestep * BYTES_TO_GIBS,
        'missing_pct': float(f['/FSMissingGroup/FSMissingDataSet'][:,:].sum()) / (f['/FSMissingGroup/FSMissingDataSet'].shape[0]*f['/FSMissingGroup/FSMissingDataSet'].shape[1]),
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='aggregate bytes in/out from h5lmt')
    parser.add_argument('file', type=str, nargs='+', help='h5lmt file(s) to process')
    parser.add_argument('-t', '--threads', type=int, default=8, help='number of threads to use')
    args = parser.parse_args()

    pool = multiprocessing.Pool(args.threads)
    results = pool.map(summarize_h5lmt_file, args.file)
    for result in sorted(results, key=lambda x: x['date']):
        print "%(date)10s %(read_gibs)9.0f %(write_gibs)9.0f %(missing_pct).4f" % result
