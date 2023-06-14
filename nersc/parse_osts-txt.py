#!/usr/bin/env python
#
#  Parse and report on the osts.txt file dumped by the NERSC pyLMT
#  hourly_archive.sh script (which itself just dumps lctl dl -t with a
#  prefixed timestamp).  See
#
#    github.com/NERSC/pylmt/blob/master/share/nersc-deploy/hourly_archive.sh
#

import sys
import re

aggregate = { 'total': 0, 'used': 0, 'avail': 0 }
date = None

with open(sys.argv[1]) as ostfile:
    for line in ostfile:
        if line.startswith('BEGIN'):
            if date is None:
                date = line.split()[1]
            else:
                print date, aggregate['total'], aggregate['used'], aggregate['avail']
                date = line.split()[1]
                aggregate = { 'total': 0, 'used': 0, 'avail': 0 }
        elif line.startswith('snx11168-OST'):
            fields = line.split()
            aggregate['total'] += long(fields[1])
            aggregate['used']  += long(fields[2])
            aggregate['avail'] += long(fields[3])


    print date, aggregate['total'], aggregate['used'], aggregate['avail']
