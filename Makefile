BINARIES=drop_file_from_page_cache is_file_in_page_cache mmap-test timer mmap-vs-posix

all: $(BINARIES)

clean:
	-rm $(BINARIES) 2>/dev/null

mmap-test: mmap-test.c
	$(CC) $(CFLAGS) -o $@ $< -lm

timer: timer.c
	$(CC) $(CFLAGS) -o $@ $< -lrt
