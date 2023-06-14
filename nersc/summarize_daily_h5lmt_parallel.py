#!/usr/bin/env python
"""
Scrape large numbers of h5lmt files to determine how much data was read and
written to Lustre over the lifetime of a file system.
"""

import sys
import json
import argparse
import datetime
import warnings
import multiprocessing
import h5py

BYTES_TO_GIBS = 2.0**-30

METADATA_OPS = [ 'open', 'close', 'getattr', 'rename', 'unlink', 'rmdir', 'link' ]
RW_ADD_KEYS = [ 'read_gibs', 'write_gibs', 'missing_pct' ]

HEADER_KEYS = {
    'date': 'Date',
    'read_gibs': 'GiB Read',
    'write_gibs': 'GiB Write',
    'missing_pct': "% Missing",
    'open': "open",
    'close': "close",
    'getattr': 'stat',
    'rename': 'rename',
    'unlink': 'unlink',
    'rmdir': 'rmdir',
    'link': 'link',
}


def summarize_h5lmt_rw(h5lmt_file):
    sys.stderr.write("Processing %s\n" % h5lmt_file)
    try:
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
    except (IOError, KeyError, ValueError) as error:
        warnings.warn("%s: %s" % (h5lmt_file, error))
        return {}

def summarize_h5lmt_metadata(h5lmt_file):
    sys.stderr.write("Processing %s\n" % h5lmt_file)
    try:
        f = h5py.File(h5lmt_file, 'r')
        timestep = f['/FSStepsGroup/FSStepsDataSet'][1] - f['/FSStepsGroup/FSStepsDataSet'][0]
        date = f['/FSStepsGroup/FSStepsDataSet'].attrs['day']
        result = {
            'date': date,
            'datetime_date': datetime.datetime.strptime(date, "%Y-%m-%d"),
        }
        for op in METADATA_OPS:
            op_index = list(f['/MDSOpsGroup/MDSOpsDataSet'].attrs['OpNames']).index(op)
            result[op] = f['/MDSOpsGroup/MDSOpsDataSet'][op_index,:].sum() * timestep
        return result
    except (IOError, KeyError, ValueError) as error:
        warnings.warn("%s: %s" % (h5lmt_file, error))
        return {}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='aggregate bytes in/out from h5lmt')
    parser.add_argument('file', type=str, nargs='+', help='h5lmt file(s) to process')
    parser.add_argument('-t', '--threads', type=int, default=8, help='number of threads to use')
    parser.add_argument('-m', '--metadata', action='store_true', help='report on metadata instead of data')
    parser.add_argument('-j', '--json', action='store_true', help='output in json instead of a text table')
    parser.add_argument('--reduce-on', type=str, default='date', help='reduce on (date|week|month|year)')
    parser.add_argument('-s', '--summary', action='store_true', help='print final summary of totals')
    args = parser.parse_args()

    if args.metadata:
        process_function = summarize_h5lmt_metadata
        metrics = METADATA_OPS
    else:
        process_function = summarize_h5lmt_rw
        metrics = RW_ADD_KEYS

    pool = multiprocessing.Pool(args.threads)
    results = pool.map(process_function, args.file)

    ### results contains one record per h5lmt file; now reduce based on day,
    ### week, month, etc
    reduced_results = {}
    for result in results:
        if 'datetime_date' not in result:
            continue
        if args.reduce_on == 'week':
            key = datetime.datetime.strptime(result['datetime_date'].strftime("%Y %W 1"), "%Y %W %w").strftime("%Y-%m-%d")
        elif args.reduce_on == 'month':
            key = result['datetime_date'].strftime("%Y-%m")
        elif args.reduce_on == 'date':
            key = result['datetime_date'].strftime("%Y-%m-%d")
        elif args.reduce_on == 'year':
            key = result['datetime_date'].strftime("%Y")
        else:
            raise Exception("reduce_on must be week|month|date|year")
        if key not in reduced_results:
            reduced_results[key] = { 'n': 0, }
            for metric in metrics:
                reduced_results[key][metric] = 0.0
        reduced_results[key]['n'] += 1
        reduced_results[key]['date'] = str(key)
        for metric in metrics:
            reduced_results[key][metric] += result[metric]

    if args.json:
        print json.dumps(reduced_results, indent=4, sort_keys=True)
    else:
        ### Print column header
        header_str = "%(date)10s"
        for metric in metrics:
            header_str += " %%(%s)12s" % metric
        print header_str % HEADER_KEYS

        ### Print data
        missing_pct_bogus = False
        metric_totals = {}
        last_print_str = ""
        for key in sorted(reduced_results.keys()):
            result = reduced_results[key]
            if result['n'] > 1:
                missing_pct_bogus = True
            print_str = "%(date)10s"
            for metric in metrics:
                print_str += " %%(%s)12.2f" % metric
                ### calculate summary of each metric
                if metric not in metric_totals:
                    metric_totals[metric] = 0.0
                metric_totals[metric] += result[metric]
            print print_str % result
            last_print_str = print_str

        if args.summary:
            metric_totals['date'] = "summary"
            print
            print last_print_str % metric_totals

        ### The logic to recalculate missing data percentages based on reduced data
        ### isn't included, so just throw a warning if reduction corrupted the
        ### meaning of this field
        if not args.metadata and missing_pct_bogus:
            warnings.warn("Reduced one or more days' outputs; missing_pct is no longer a percent")
