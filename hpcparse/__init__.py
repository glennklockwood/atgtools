#!/usr/bin/env python
"""
Collection of Python tools to parse common forms of string output
"""

import ior

FS_MAP = {
    "scratch1": "edison_snx11025",
    "scratch2": "edison_snx11035",
    "scratch3": "edison_snx11036",
    "cscratch": "cori_snx11168",
}

FS_MAP_REV = {val: key for key, val in FS_MAP.iteritems()}
