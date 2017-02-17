#!/usr/bin/env python
#
# For a Sandy Bridge E5-2670 node,
#   ./flops-per-cycle 2.6 8 16
#    2.6    = GHz, 
#    8      = dp flops per cycle (AVX=4 flops * (1 add + 1 mult))
#    16     = cores/node
#

import sys

if len(sys.argv) < 4:
    sys.stderr.write('Syntax: %s <ghz> <flopsPerCycle> <cores>\n' % sys.argv[0])
    sys.exit(1)

ghz = float(sys.argv[1])
flopsPerCycle= float(sys.argv[2])
cores = float(sys.argv[3])

secondsPerCycle= 1.0 / ghz

gflop = flopsPerCycle / secondsPerCycle

print "%f cycles per second, %f flops per second, %f GFLOPs" % ( ghz, gflop, gflop*cores )
print "%d cores * %.4f GHz * %d flops/cycle = %f GFLOPs" % ( cores, ghz, flopsPerCycle, cores*ghz*flopsPerCycle )
