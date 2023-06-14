#!/usr/bin/env python
#
#  Very hacky script to parse a file that contains one or more concatenations of
#  the following two files:
#
#    /proc/fs/dvs/mounts/[0-9]/stats
#    /proc/fs/dvs/ipc/stats
#
#  To test it out, just do:
#    $ cat /proc/fs/dvs/mounts/0/stats /proc/fs/dvs/ipc/stats > somefile.txt
#    $ dd if=/dev/zero of=/mnt/dvs/garbage bs=1m count=1024
#    $ cat /proc/fs/dvs/mounts/0/stats /proc/fs/dvs/ipc/stats > somefile.txt
#    $ parse_dvs_counters.py somefile.txt
#
#  Copy and paste each generated json (which corresponds to one pair of proc
#  files) into its own file, then diff the files to get an idea of which
#  counters changed.
#

import sys
import json

# Need to mask out unknown threads because the DVS IPC stats file contains
# random garbage after each Instance block
_VALID_INSTANCE_KEYS = [
    'Total Threads',
    'Created Threads',
    'Active Threads',
    'Idle Threads',
    'Blocked Threads',
    'Thread Limit',
    'Total Queues',
    'Active Queues',
    'Free Queues',
    'Queued Messages',
]

def parse_dvs_stats_line( line, counters ):
    k, v = line.split(':')
    counters[k] = v.strip()

def parse_dvs_ipc_counters( line, counters ):
    k, v = line.strip().rsplit(None, 1)
    counters[k] = v.strip()

def main():
    # state = 0 :: looking for RQ_LOOKUP line (first line in dvs stats)
    # = 1, parsing dvs stats file, looking for "DVS IPC Transport" header
    # = 2, parsing dvs ipc file, looking for "Refill Stats:" header
    # = 3, parsing refill stats, looking for "Instance \d:" header.  THIS WILL BREAK IF THERE IS NO INSTANCE HEADER
    # = 4, parsing instance stats on valid keys only, looking for "Size Distributions"
    # = 5, parsing size distributions

    state = 0
    this_instance = 'default'

    data = {}
    fp = open( sys.argv[1] )
    for line in fp:
        if state == 0 and line.startswith("RQ_LOOKUP"):
            state += 1
            data['counters'] = {}
            parse_dvs_stats_line( line, data['counters'] )
        elif state == 1:
            if line.startswith('DVS IPC Transport Statistics'):
                state += 1
                data['ipc_counters'] = {}
            else:
                parse_dvs_stats_line( line, data['counters'] )
        elif state == 2:
            if line.startswith('Refill Stats:'):
                data['ipc_refill_stats'] = []
                state += 1
            else:
                parse_dvs_ipc_counters( line, data['ipc_counters'] )
        elif state == 3:
            if line.startswith('Instance'):
                state += 1
                this_instance = line.rsplit(None, 1)[-1].strip(': \n')
                data['ipc_instances'] = {}
                data['ipc_instances'][this_instance] = {}
            else:
                data['ipc_refill_stats'] += line.strip().split()
        elif state == 4:
            if line.startswith("Size Distributions"):
                state += 1
            elif line.startswith('Instance'):
                this_instance = line.rsplit(None, 1)[-1].strip(': \n')
                data['ipc_instances'][this_instance] = {}
            else:
                # handle all the garbage that can appear after an Instance: block
                try:
                    k, v = line.strip().rsplit(None, 1)
                except ValueError:
                    pass
                else:
                    if k in _VALID_INSTANCE_KEYS:
                        data['ipc_instances'][this_instance][k] = v.strip()
        elif state == 5:
            print json.dumps( data, sort_keys=True, indent=4 )
            state = 0

if __name__ == '__main__':
    main()
