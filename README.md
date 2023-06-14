These are various tools I've created and used in my life as a computational
scientist.  Use at your own risk.

## Generally Useful Tools

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
