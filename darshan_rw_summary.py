#!/usr/bin/env python
"""
In the absence of quarshan, this script will tear through a summary file
generated by the following bash/awk script based on darshan-2.x logs:

    for i in *.darshan.gz; do 
        echo "BEGIN $i"
        darshan-parser $i | awk '
            /(CP_BYTES_READ|CP_BYTES_WRITTEN).*/ {
                if ( $3 == "CP_BYTES_READ" ) { sum_read[$6] += $4; }
                else if ( $3 == "CP_BYTES_WRITTEN" ) { sum_write[$6] += $4 }
            }
            END {
                for (fs in sum_read) {
                    printf("%s %d %d\n", fs, sum_read[fs], sum_write[fs]);
                }
            }'
    done

and print summary metrics about the read/write activity.
"""

import sys
import json

data = {}
with open(sys.argv[1], 'r') as fp:
    for line in fp:
        """
        BEGIN aae109_vasp_edison_normal_id21057_5-1-78490-8167977107149723115_1.darshan.gz
        /scratch2 103024896 57412973
        """
        if line.startswith('BEGIN'):
            log_name = line.split(None,1)[1]
            user = log_name.split('_',1)[0]
        else:
            fs, read, write = line.split(None)
            read = int(read)
            write = int(write)

            if fs not in data:
                data[fs] = { 'read': 0, 'write': 0 }
            data[fs]['read'] += read
            data[fs]['write'] += write

            if 'user_writes' not in data[fs]:
                data[fs]['user_writes'] = {}
            if 'user_reads' not in data[fs]:
                data[fs]['user_reads'] = {}

            if user not in data[fs]['user_writes']:
                data[fs]['user_writes'][user] = 0
            if user not in data[fs]['user_reads']:
                data[fs]['user_reads'][user] = 0

            data[fs]['user_reads'][user] += read
            data[fs]['user_writes'][user] += write


for fs in data.keys():
    d = data[fs]['user_reads']
    data[fs]['max_read_user'] = max(d, key=d.get)
    d = data[fs]['user_writes']
    data[fs]['max_write_user'] = max(d, key=d.get)
    data[fs]['read_gibs'] = data[fs]['read'] / 2.0 ** 30.0
    data[fs]['write_gibs'] = data[fs]['write'] / 2.0 ** 30.0


print json.dumps(data, indent=4)
