#!/usr/bin/env python
#
#  basic code to identify missing data in h5lmt and associate it with a timestamp
#

import h5py
import sys
import os

filepath = os.path.abspath( sys.argv[1] )
f = h5py.File( filepath, 'r' )

read_bytes = 0
ost = 0
for ost_row in f['FSMissingGroup/FSMissingDataSet']:
    for timestep, value in enumerate( ost_row ):
        if value != 0:
            print ost, timestep, f['FSStepsGroup/FSStepsDataSet'][timestep], value

    ost += 1
