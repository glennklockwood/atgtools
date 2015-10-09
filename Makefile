BINARIES=drop_file_from_page_cache is_file_in_page_cache mmap-test-rand mmap-test-stride1 mmap-test-stride8

all: $(BINARIES)

clean:
	-rm $(BINARIES) 2>/dev/null

mmap-test-rand: mmap-test.c
	$(CC) -o $@ $< -DRANDOM_OFFSET=1
mmap-test-stride1: mmap-test.c
	$(CC) -o $@ $< -DPAGE_STRIDE=1
mmap-test-stride8: mmap-test.c
	$(CC) -o $@ $< -DPAGE_STRIDE=8
