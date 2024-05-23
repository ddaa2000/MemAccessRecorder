#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#include <argp.h>
#include <time.h>
#include <pthread.h>

#include <unistd.h>
#include <sys/mman.h>
#include <sys/fcntl.h>
#include <sys/syscall.h>
#include <sys/ioctl.h>
#include <signal.h>

#include "perf.h"



/* Program documentation. */
static char doc[] = "A tiny memory access recorder";

/* A description of the arguments we accept. */
static char args_doc[] = "";

/* The options we understand. */
static struct argp_option options[] = {
    {"buffer-size", 'b', "int", 0, "The 2^buffer-size number of pages will be used", 0 },
    {"sample-period", 's', "int", 0, "How many events to take one sample", 0  },
    {"read-period", 'r', "int", 0, "How many nanoseconds between results-reading in the buffer", 0  },
    {"pid", 'p', "pid", 0, "The pid of the target program", 0  },
    {"write-buffer-num", 'n', "int", 0, "The number of disk write buffers", 0 },
    {"write-buffer-size", 'm', "int", 0, "The number of records per write buffer", 0 },
    {"output-dir", 'o', "string", 0, "Where to put the output files", 0}
};

typedef struct{
    __u64 tid;
    __u64 addr;
    __u64 time;
    __u32 cpu;
} record;

static record** write_buffer;

static volatile int64_t last_full_buffer = -1;
static volatile int64_t last_stored_buffer = -1;

/* Used by main to communicate with parse_opt. */
struct arguments {
    int buffer_size;
    int sample_period;
    int read_period;
    pid_t pid;
    int write_buffer_num;
    int write_buffer_size;
    char* output_dir;
};

static struct arguments arguments;

static error_t parse_opt(int key, char *arg, struct argp_state *state) {
    struct arguments *arguments = state->input;

    switch (key) {
        case 'b':
            arguments->buffer_size = atoi(arg);
            break;
        case 's':
            arguments->sample_period = atoi(arg);
            break;
        case 'r':
            arguments->read_period = atoi(arg);
            break;
        case 'p':
            arguments->pid = atoi(arg);
            break;
        case 'n':
            arguments->write_buffer_num = atoi(arg);
            break;
        case 'm':
            arguments->write_buffer_size = atoi(arg);
            break;
        case 'o':
            arguments->output_dir = arg;
            break;
        case ARGP_KEY_ARG:
            if (state->arg_num > 0){
                /* Too many arguments. */
                argp_usage(state);
                return ARGP_ERR_UNKNOWN;
            }  
            break;
        case ARGP_KEY_END:
            break;
        default:
            return ARGP_ERR_UNKNOWN;
    }
    return 0;
}

static struct argp argp = { options, parse_opt, args_doc, doc, NULL, NULL, NULL };



struct perf_sample {
  struct perf_event_header header;
  __u64 ip;
  __u32 pid, tid;    /* if PERF_SAMPLE_TID */
  __u64 time;
  __u64 addr;        /* if PERF_SAMPLE_ADDR */
  __u32 cpu, res;    /* if PERF_SAMPLE_CPU */
  __u64 weight;      /* if PERF_SAMPLE_WEIGHT */
  /* __u64 data_src;    /\* if PERF_SAMPLE_DATA_SRC *\/ */
  __u64 phy_addr;
};


static volatile sig_atomic_t sigterm_received = 0;
static volatile int scanner_finished = 0;

void handle_sigterm(int sig) {
    printf("Received SIGTERM (signal number %d), cleaning up...\n", sig);
    // Perform any cleanup operations here
    sigterm_received = 1;
}


static int startup(__u64 config, pid_t pid, int sample_period)
{
    struct perf_event_attr attr;
    memset(&attr,0,sizeof(struct perf_event_attr));

    attr.type = PERF_TYPE_RAW;
    attr.size = sizeof(struct perf_event_attr);
    attr.config = config;
    attr.config1 = 0;
    attr.sample_period = sample_period;
    attr.sample_type = PERF_SAMPLE_IP | PERF_SAMPLE_TID | PERF_SAMPLE_WEIGHT | PERF_SAMPLE_ADDR | PERF_SAMPLE_PHYS_ADDR | PERF_SAMPLE_TIME | PERF_SAMPLE_CPU;
    attr.disabled = 0;
    //attr.inherit = 1;
    attr.exclude_kernel = 1;
    attr.exclude_hv = 1;
    attr.exclude_callchain_kernel = 1;
    attr.exclude_callchain_user = 1;
    attr.precise_ip = 1; // when i set attr.precise_ip = 0 , all the addr = 0;

    int fd=perf_event_open(&attr,pid,-1,-1,0);
    if(fd<0)
    {
        perror("Cannot open perf fd!");
        return -1;
    }
    return fd;
}

static void write_to_file(char* path, ssize_t number_of_records, char* record_head){
    int fd;
    while((fd = open(path, O_RDWR | O_CREAT | O_TRUNC)) == -1){
        printf("failed to open %s", path);
    }

    ssize_t file_size = sizeof(record) * number_of_records;
    ssize_t total_bytes_written = 0;

    while (total_bytes_written < file_size) {
        ssize_t bytes_written = write(fd, record_head + total_bytes_written, file_size - total_bytes_written);
        if (bytes_written == -1) {
            if (errno == EINTR) {
                // Write was interrupted by a signal, retry
                continue;
            } else {
                perror("Error writing to file");
                close(fd);
                exit(-1);
            }
        }
        total_bytes_written += bytes_written;
    }
    close(fd);
}

static void scan_thread(struct perf_event_mmap_page *p, volatile int* present_index)
{
    char *pbuf = (char *)p + p->data_offset;
    __sync_synchronize();

    if(p->data_head == p->data_tail) {
        return;
    }

    int present_buffer_index = (last_full_buffer + 1) % arguments.write_buffer_num;

    __u64 head = p->data_head;
    __u64 tail = p->data_tail;
    printf("\n\nhead  %llu tail %llu delta %llu\n\n", head % p->data_size , tail % p->data_size, head - tail);
    for(__u64 present = tail + 1; present != head; present += 1){
        struct perf_event_header *ph = (void *)(pbuf + (present % p->data_size));
        struct perf_sample* ps;
        switch(ph->type) {
            case PERF_RECORD_SAMPLE:
                ps = (struct perf_sample*)ph;
                if(ps!= NULL &&  ps->addr != 0) {
                    write_buffer[present_buffer_index][*present_index].tid = ps->tid;
                    write_buffer[present_buffer_index][*present_index].addr = ps->addr;
                    write_buffer[present_buffer_index][*present_index].time = ps->time;
                    write_buffer[present_buffer_index][*present_index].cpu = ps->cpu;
                    (*present_index) += 1;
                    if((*present_index) >= arguments.write_buffer_size){
                        (*present_index) = 0;
                        last_full_buffer += 1;
                        present_buffer_index = (last_full_buffer + 1) % arguments.write_buffer_num;
                        printf("switch to buffer %lu\n", last_full_buffer);
                    }
                }
                break;
            default:
                break;
        }
    }
    p->data_tail = head;
}

static void *scanner(void *arg){

    int fd1 = startup(0x82d0, arguments.pid, arguments.sample_period);
    int fd2 = startup(0x81d0, arguments.pid, arguments.sample_period);
    size_t perf_pages = (1ul + (1ul << arguments.buffer_size));
    size_t mmap_size = sysconf(_SC_PAGESIZE) * perf_pages;
    struct perf_event_mmap_page *p1 = mmap(NULL, mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd1, 0);
    struct perf_event_mmap_page *p2 = mmap(NULL, mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED, fd2, 0);
    // start to perf
    ioctl(fd1,PERF_EVENT_IOC_ENABLE,0);
    ioctl(fd2,PERF_EVENT_IOC_ENABLE,0);
    volatile int present_index = 0;
    while(1)
    {
        struct timespec req, rem;
        req.tv_sec = 0;
        req.tv_nsec = arguments.read_period;
        scan_thread(p1, &present_index);
        scan_thread(p2, &present_index);
        nanosleep(&req, &rem);
        if(sigterm_received){
            printf("start to terminate scanner\n");
            break;
        }
    }

    //handling the last record
    if( present_index != 0 ){
        char* file_dir = malloc(strlen(arguments.output_dir) + 100);
        __u64 present_index_to_store = last_full_buffer + 1;
        printf("scanner storing incomplete buffer %llu\n", present_index_to_store);
        sprintf(file_dir, "%s/%llu", arguments.output_dir, present_index_to_store);
        

        char* present_write_buffer = (char*)write_buffer[present_index_to_store % arguments.write_buffer_num];

        write_to_file(file_dir, present_index, present_write_buffer);

        free(file_dir);
    }

    printf("scanner finished\n");
    scanner_finished = 1;


    return NULL;
}

static void writer(){
    char* file_dir = malloc(strlen(arguments.output_dir) + 100);
    while(1){
        if(last_stored_buffer < last_full_buffer){
            printf("we need to store, remaining: %ld\n", last_full_buffer - last_stored_buffer);
            
            last_stored_buffer++;
            __u64 present_index_to_store = last_stored_buffer;
            printf("storing buffer %llu\n", present_index_to_store);
            sprintf(file_dir, "%s/%llu", arguments.output_dir, present_index_to_store);
            

            char* present_write_buffer = (char*)write_buffer[present_index_to_store % arguments.write_buffer_num];

            write_to_file(file_dir, arguments.write_buffer_size, present_write_buffer);

        } else {
            if(scanner_finished && last_stored_buffer == last_full_buffer){
                printf("writer received scanner finished\n");
                break;
            }
            usleep(10);
            // printf("no need to store\n");
        }
    }
    free(file_dir);

}

int main(int argc, char **argv)
{
    argp_parse(&argp, argc, argv, 0, 0, &arguments);
    signal(SIGTERM, handle_sigterm);

    write_buffer = (record**)malloc(sizeof(record*)*arguments.write_buffer_num);
    for(int i = 0; i < arguments.write_buffer_num; i++){
        write_buffer[i] = (record*)malloc(sizeof(record)*arguments.write_buffer_size);
    }

    pthread_t scanner_thread;
    pthread_create(&scanner_thread, NULL, scanner, NULL);

    writer();

    //actually this should be redundant
    pthread_join(scanner_thread, NULL);

    exit(-1);
}