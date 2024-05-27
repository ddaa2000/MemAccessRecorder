#include <stdio.h>
#include <stdlib.h>
#include <fcntl.h>
#include <unistd.h>
#include <inttypes.h>
#include <stdint.h>

typedef struct {
    uint64_t tid;
    uint64_t addr;
    uint64_t core_time;
    uint32_t cpu;
    // uint64_t sampler_time;
    uint64_t sampler_s;
    uint64_t sampler_ns;
    // uint64_t sampler_local_clock;
} record;

void print_record(const record* rec) {
    printf("Record:\n");
    printf("  TID:  %" PRIu64 "\n", rec->tid);
    printf("  Addr: %lx \n", rec->addr);
    printf("  Core Time: %" PRIu64 "\n", rec->core_time);
    printf("  CPU:  %" PRIu32 "\n", rec->cpu);
    // printf("  Sampler Time:  %" PRIu64 "\n", rec->sampler_time);
    printf("  Sampler Time(s):  %" PRIu64 "\n", rec->sampler_s);
    printf("  Sampler Time(ns):  %" PRIu64 "\n", rec->sampler_ns);
}

int main(int argc, char* argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <binary file>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char* filename = argv[1];
    int fd = open(filename, O_RDONLY);
    if (fd == -1) {
        perror("open");
        return EXIT_FAILURE;
    }

    record rec;
    ssize_t bytesRead;
    while ((bytesRead = read(fd, &rec, sizeof(record))) > 0) {
        if (bytesRead != sizeof(record)) {
            fprintf(stderr, "Incomplete read\n");
            close(fd);
            return EXIT_FAILURE;
        }
        print_record(&rec);
    }

    if (bytesRead == -1) {
        perror("read");
    }

    close(fd);
    return EXIT_SUCCESS;
}
