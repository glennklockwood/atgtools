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
ost_num = 0
h5_dataset = f['FSMissingGroup/FSMissingDataSet']
for ost_row in h5_dataset:
    for timestep_num, value in enumerate( ost_row ):
        if value == 0:
            continue

        val_after = -1.0
        val_before= -1.0
        if timestep_num > 0:
            val_before= f['OSTReadGroup/OSTBulkReadDataSet'][ost_num,timestep_num-1]
        if timestep_num+1 < h5_dataset.shape[1]:
            val_after = f['OSTReadGroup/OSTBulkReadDataSet'][ost_num,timestep_num+1]

        # (57, 17270, 1455177550, 1, 1316454.3999999999, 55705.599999999999, 1344307.2)
        print "%3d %5d %10d %2d %12.2f %12.2f %12.2f" % ( 
            ost_num, 
            timestep_num,
            f['FSStepsGroup/FSStepsDataSet'][timestep_num],
            value,
            val_before,
            f['OSTReadGroup/OSTBulkReadDataSet'][ost_num,timestep_num],
            val_after
        )

    ost_num += 1
