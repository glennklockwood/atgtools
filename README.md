These are various tools I've created and used in my life as a computational
scientist in NERSC's Advanced Technologies Group.  Use at your own risk.

Generally Useful Tools
--------------------------------------------------------------------------------

- `mpiio-cp.c` - a tool to copy a large file in parallel using MPI-IO
- `timer.c` - boilerplate code to perform high-resolution timing
- `is_file_in_page_cache.c` - boilerplate code demonstrating how to check if a
   file is in page cache
- `drop_file_from_page_cache.c` - boilerplate code demonstrating how
  `posix_fadvise` may be used to drop files from page cache as an unprivileged
   user
- `mmap-vs-posix.c` - boilerplate code demonstrating how to perform POSIX
  file-based and mmap-based I/O
- `mmap-test.c` - a simple tool to measure mmap I/O performance


Tools Specific to NERSC Infrastructure
--------------------------------------------------------------------------------

- `aggregate-h5lmt.py` - boilerplate code to parse LMT HDF5 files
- `archive_darshan.sh` - script to back up Darshan logs to HPSS.  Run using
  `NERSC_HOST=cori ./archive_darshan.sh ~/darshanlogs/` or something similar.
- `build-darshan.sh` - compile and cross-compile Darshan in the NERSC
   environment
- `ior-sequence.py` - boilerplate code to prototype new IOR kernels
- `missingdata-h5lmt.py` - boilerplate code to work with pyLMT's
  `FSMissingDataSet`
- `parse_dvs_counters.py` - boilerplate code to parse DVS client counters

Tools for the BLAST I/O Performance Analysis
--------------------------------------------------------------------------------

- `ncbi-blast-2.2.31-traces.patch` - patch needed to make NCBI's blast report
  detailed I/O telemetry
- `parse_instrumented_blast.py` - tool to parse the output from a BLAST job
  instrumented with the above patch

License/Disclaimer
--------------------------------------------------------------------------------

This software was developed in the course of prime contract No. 
DE-AC02-05CH11231 between the U.S. Department of Energy and the University of
California but __has not been licensed for public use__.  If you would like to
use any of this software and require a license, please contact me and I can
arrange for a proper public-use license.
