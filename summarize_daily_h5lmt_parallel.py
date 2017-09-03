#!/usr/bin/env python
"""
Scrape large numbers of h5lmt files to determine how much data was read and
written to Lustre over the lifetime of a file system.
"""

import argparse
import h5py
import multiprocessing
import warnings
import datetime

BYTES_TO_GIBS = 2.0**-30

def summarize_h5lmt_file(h5lmt_file):
    print "Processing", h5lmt_file
    f = h5py.File(h5lmt_file, 'r')
    timestep = f['/FSStepsGroup/FSStepsDataSet'][1] - f['/FSStepsGroup/FSStepsDataSet'][0]
    date = f['/FSStepsGroup/FSStepsDataSet'].attrs['day']
    return {
        'date': date,
        'datetime_date': datetime.datetime.strptime(date, "%Y-%m-%d"),
        'read_gibs': f['/OSTReadGroup/OSTBulkReadDataSet'][:,:].sum() * timestep * BYTES_TO_GIBS,
        'write_gibs': f['/OSTWriteGroup/OSTBulkWriteDataSet'][:,:].sum() * timestep * BYTES_TO_GIBS,
        'missing_pct': float(f['/FSMissingGroup/FSMissingDataSet'][:,:].sum()) / (f['/FSMissingGroup/FSMissingDataSet'].shape[0]*f['/FSMissingGroup/FSMissingDataSet'].shape[1]),
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='aggregate bytes in/out from h5lmt')
    parser.add_argument('file', type=str, nargs='+', help='h5lmt file(s) to process')
    parser.add_argument('-t', '--threads', type=int, default=8, help='number of threads to use')
    parser.add_argument('--reduce-on', type=str, default='date', help='reduce on (date|week|month)')
    args = parser.parse_args()

    pool = multiprocessing.Pool(args.threads)
    results = pool.map(summarize_h5lmt_file, args.file)

    ### results contains one record per h5lmt file; now reduce based on day,
    ### week, month, etc
    reduced_results = {}
    for result in results:
        if args.reduce_on == 'week':
            key = datetime.datetime.strptime(result['datetime_date'].strftime("%Y %W 1"), "%Y %W %w").strftime("%Y-%m-%d")
        elif args.reduce_on == 'month':
            key = result['datetime_date'].strftime("%Y-%m")
        else:
            key = result['datetime_date'].strftime("%Y-%m-%d")
        if key not in reduced_results:
            reduced_results[key] = {
                'read_gibs': 0.0,
                'write_gibs': 0.0,
                'missing_pct': 0.0,
                'n': 0,
            }
        reduced_results[key]['read_gibs'] += result['read_gibs']
        reduced_results[key]['write_gibs'] += result['write_gibs']
        reduced_results[key]['missing_pct'] += result['missing_pct']
        reduced_results[key]['n'] += 1
        reduced_results[key]['date'] = str(key)

    ### Print column header
    print "%(date)10s %(read_gibs)9s %(write_gibs)9s %(missing_pct)s" % {
        'date': 'Date',
        'read_gibs': 'GiB Read',
        'write_gibs': 'GiB Write',
        'missing_pct': "% Missing",
    }

    ### Print data
    missing_pct_bogus = False
    for key in sorted(reduced_results.keys()):
        result = reduced_results[key]
        if result['n'] > 1:
            missing_pct_bogus = True
        print "%(date)10s %(read_gibs)9.0f %(write_gibs)9.0f %(missing_pct).4f" % result

    ### The logic to recalculate missing data percentages based on reduced data
    ### isn't included, so just throw a warning if reduction corrupted the
    ### meaning of this field
    if missing_pct_bogus:
        warnings.warn("Reduced one or more days' outputs; missing_pct is no longer a percent")
