# Disable echoing of commands
MAKEFLAGS += --silent

export CCFLAGS := $(CCFLAGS) -Wall -Wextra -pedantic -Wno-unused-parameter -fno-omit-frame-pointer -g -fPIC

source := $(shell find * -type f -name "*.c" -not -path "build/*")
headers := $(shell find * -type f -name "*.h" -not -path "build/*")

.PHONY: build library format clean

target: build/recorder build/tiny build/reader


build/recorder: perf.c recorder.c perf.h
	mkdir -p $(dir $@)
	$(CC) $(CCFLAGS) -o $@ -pthread perf.c recorder.c

build/tiny: tiny.c
	$(CC) -o0 -o $@ $<

build/reader: reader.c
	$(CC) -o0 -o $@ $<

clean:
	rm -rf build &>/dev/null || true