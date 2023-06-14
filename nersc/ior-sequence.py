#!/usr/bin/env python
#
#  ior-sequence.py - a tool to generate the sequence of IO offsets that will
#    be carried out by IOR.  Meant to be a method to rapidly prototype new
#    IOR access patterns.
#
#  Glenn K. Lockwood, October 2015
#

import sys
import random

_numTasks = 4
_segmentCount = 51
_blockSize = 10
_transferSize = 1
_filePerProc = False

def GetOffsetArrayRandom( pretendRank, seed ):
    fileSize = _blockSize * _segmentCount
    if not _filePerProc:
        fileSize *= _numTasks

    random.seed( seed )

    # count needed offsets (pass 1)
    offsets = 0
    i = 0
    while i < fileSize:
        if _filePerProc or ( random.randint( 0, _numTasks-1 ) == pretendRank ):
            offsets += 1
        i += _transferSize

    # setup empty array
    offsetArray = [ 0 for x in range( offsets ) ]

    offsetCnt = 0
    if _filePerProc:
        i = 0
        while i < offset:
            offsetArray[i] = i * _transferSize
            i += 1
    else:
        random.seed( seed ) # need same seed
        i = 0
        while i < fileSize:
            if random.randint( 0, _numTasks-1 ) == pretendRank:
                offsetArray[offsetCnt] = i
                offsetCnt += 1
            i += _transferSize

    # reorder array
    i = 0
    while i < offsets:
        value = random.randint( 0, offsets-1 )
        tmp = offsetArray[value]
#       offsetArray[value] = offsetArray[i]
#       offsetArray[i] = tmp
        i += 1

    return offsetArray


def GetOffsetArraySequential( pretendRank, seed ):
    # calculate number of offsets
    offsets = _blockSize / _transferSize * _segmentCount;
    offsetArray = [ 0 for x in range( offsets ) ]

    i = 0
    k = 0
    while i < _segmentCount:
        print ""
        j = 0
        while j < ( _blockSize / _transferSize ):
            offsetArray[k] = j * _transferSize
            if _filePerProc:
                offsetArray[k] += i * _blockSize
            else:
                offsetArray[k] += \
                    ( i * _numTasks * _blockSize ) \
                    + (pretendRank * _blockSize)
            print "%2d %3d %d" % ( pretendRank, k, offsetArray[k] )
            k += 1
            j += 1
        i += 1

    return offsetArray


if __name__ == '__main__':
    function = GetOffsetArrayRandom
#   function = GetOffsetArraySequential

    seed = random.random()

    maxrow = 0
    data = []
    for rank in range( _numTasks ):
        offsetArray = function( rank, seed )
        maxrow = max( maxrow, len(offsetArray) )
        data.append( offsetArray )

    for row in range( maxrow ):
        for rank, offsetArray in enumerate(data):
            if row >= len(offsetArray):
                value = "%10d" % 0
            else:
                value = "%10d" % offsetArray[row]
            sys.stdout.write( value )
        sys.stdout.write("\n")
