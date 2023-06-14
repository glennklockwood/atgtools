#!/usr/bin/env python
#
#  Tool to scan Lustre for OSSes that have an abnormal number of OSTs.  Good for
#  detecting OSSes whose OSTs have failed over and are causing performance
#  variation.
#

import os
import subprocess
import socket # for sorting IP addresses

for lctl in '/usr/sbin/lctl', '/sbin/lctl':
    if os.path.isfile( lctl ):
        _LCTL = lctl
        break

p = subprocess.Popen( [ _LCTL, 'dl', '-t' ], stdout=subprocess.PIPE )

oss_ct = {}

for line in p.stdout:
    args = line.strip().split()
    if len(args) < 3 or args[2] != 'osc':
        continue

    ost_name = '-'.join( args[3].split('-', 3)[0:2] )
    oss_name = args[6].split('@')[0]
    fs_id = args[3].split('-', 2)[0]

    if fs_id not in oss_ct:
        oss_ct[fs_id] = {}

    if oss_name in oss_ct[fs_id]:
        oss_ct[fs_id][oss_name].append( ost_name )
    else:
        oss_ct[fs_id][oss_name] = [ ost_name ]

for fs_id in oss_ct:
    num_osts = {}
    max_ost_ct = 0
    max_ost_val = None
    for oss_name in oss_ct[fs_id]:
        key = len(oss_ct[fs_id][oss_name])
        ### increment the bin representing this OST count
        if key not in num_osts:
            num_osts[key] = 1
        else:
            num_osts[key] += 1
        ### update the consensus OST count
        if num_osts[key] > max_ost_ct:
            max_ost_ct = num_osts[key]
            max_ost_val = len(oss_ct[fs_id][oss_name])

    print "Filesystem %s appears to have %d OSTs per OSS" % ( fs_id, max_ost_val )
    for oss_name in sorted(oss_ct[fs_id], key=lambda x: socket.inet_aton(x)):
        if len(oss_ct[fs_id][oss_name]) != max_ost_val:
            print "  %s has %d OSTs" % ( oss_name, len(oss_ct[fs_id][oss_name]) )
            for ost_name in oss_ct[fs_id][oss_name]:
                print "    " + ost_name
