#!/usr/bin/env python
"""
Interpets the stdout of IOR runs and prints out a table of the results.
Syntax:

    ./summarize-ior.py <ior-stdout.0> [ior-stdout.1 [...]]

Relies on the hpcparse Python package available at

    https://www.github.com/glennklockwood/atgtools
"""
import sys
import json
import hpcparse.ior

if __name__ == '__main__':
    input_files = sys.argv[1:]
    jobs_table = {}
    for input_file in input_files:
        raw_data = hpcparse.ior.parse(open(input_file, 'r'))
        for i in raw_data['run_summary']:
            run_key = "%d-%d" % (raw_data['input_summary']['nodes'], raw_data['input_summary']['ppn'])
            if run_key not in jobs_table:
                jobs_table[run_key] = {}
            for run_record in raw_data['run_summary']:
                op_key = run_record['operation']
                jobs_table[run_key][op_key] = run_record['avg_mibs']

    print json.dumps(jobs_table, indent=4)
