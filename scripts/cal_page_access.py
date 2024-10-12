import json
import matplotlib.pyplot as plt
import sys
import os
import re
import pickle
import numpy as np
import multiprocessing
from utils import *

# input
pkl_path = '/home/huaziyue/eval-disagg-gc/logs/a-large-wss-10000/data'
gclog_path = '/home/huaziyue/eval-disagg-gc/logs/a-large-wss-10000/logs-raw'
output_path = '/home/huaziyue/MemAccessRecorder/outputs'
figures_path = '/home/huaziyue/MemAccessRecorder/figures'
# step = int(sys.argv[2])

target_window = 3000000000
sample_rate = 1000
sample_window = target_window / sample_rate

# localrates = ['25', '100']
localrates = ['100']
sizes = ['large']
heapsizes = ['32']
iters = ['1']
benchmarks = [
    # {'name': 'graphchi', 'apps': ['kc']},
    {'name': 'graphchi', 'apps': ['wcc']},
    {'name': 'spark', 'apps': ['km', 'nb']},
    # {'name': 'dacapo', 'apps': ['h2']},
    {'name': 'corenlp', 'apps': ['kbp']},
    # {'name': 'quickcached', 'apps': ['yqrdh', 'yqrdu']}
]
# benchmarks = [
#     # {'name': 'graphchi', 'apps': ['kc']},
#     {'name': 'graphchi', 'apps': ['wcc']},
#     # {'name': 'spark', 'apps': ['km', 'nb']},
#     # {'name': 'dacapo', 'apps': ['h2']},
#     {'name': 'corenlp', 'apps': ['kbp']},
#     # {'name': 'quickcached', 'apps': ['yqrdh', 'yqrdu']}
# ]
# gcs = ['ps', 'psnew', 'psmc', 'g1', 'ps_young4g', 'g1_young4g', 'genshen']
gcs = ['g1_no_adaptive_young4g_conc04']
steps = [1, 5, 10, 20]

def calc_page_access(data, start_addr, end_addr):
    """
    data all 
    {
        'time1': {
            'page1': access_count,
            'page2':...
        }
        'time2':...
    }
    """
    page_counts = {}
    for (timestamp, pages) in data.items():
        print(f'processing timestamp {timestamp}')
        for (page, count) in pages.items():
            # key is page
            # print(f'page {page} count {count}')
            if page >= start_addr and page < end_addr:
                if page not in page_counts:
                    page_counts[page] = 0
                page_counts[page] += count
    return page_counts

def app_work(localrate, size, heapsize, it, benchmark, app):
    for gc in gcs:
        start_addr, end_addr = parse_gclog(gclog_path, gc, localrate, size, heapsize, it, benchmark, app)
        start_addr = start_addr >> 12
        end_addr = end_addr >> 12
        data_all, data_gc, data_mutator, data_njt = load_data(pkl_path, gc, localrate, size, heapsize, it, benchmark, app)
        wss_all = calc_page_access(data_all, start_addr, end_addr)
        with open(f'{output_path}/wss_{benchmark}_{app}.json', 'w+') as f:
            check_data_sanity(wss_all)
            json.dump(wss_all, f)

def check_data_sanity(data):
    """
    {
        'page1': total_count,
        'page2': total_count,
        ...
    }
    """
    pages = [int(d) for d in data.keys()]
    pages.sort()
    print(f'len(pages) = {len(pages)}')
    print(f'pages span = {pages[-1] - pages[0]}')
 
def app_check(localrate, size, heapsize, it, benchmark, app):
    for gc in gcs:
        with open(f'{output_path}/wss_{benchmark}_{app}.json', 'r') as f:
            pages_data = json.load(f)
            check_data_sanity(pages_data)
            
            
def _divide_groups(data):
    # 定义分组范围
    groups = {
        '0-10': (0, 10),
        '10-20': (10, 20),
        '20-30': (20, 30),
        '30-40': (30, 40),
        '40-50': (40, 50),
        '50-100': (50, 100),
        '100-200': (100, 200),
        '200-500': (200, 500),
        '500-1000': (500, 1000),
        '1000-10000': (1000, 10000),
        '10000-inf': (10000, float("inf")),
    }
    # 初始化分组统计
    group_counts = {group: 0 for group in groups}
    # 遍历每个页面并分组
    for page, total_count in data.items():
        for group, (start, end) in groups.items():
            if start <= total_count < end:
                group_counts[group] += 1
                break

    # 打印结果
    print(group_counts)
        
def divide_groups(data, name, start_addr, end_addr):
    """
    {
        'page1': total_count,
        'page2': total_count,
        ...
    }
    """
    
    def down_sample_1(d, log):
        result = {}
        for key in d.keys():
            new_key = windowed(int(key), log)
            if new_key not in result:
                result[new_key] = 0
            result[new_key] += d[key]
        return result
    data = down_sample_1(data, 12) # 16M page
    
    end_page = end_addr >> 12
    start_page = end_page - 1048576
    print(f'start_page = {start_page}, end_page = {end_page}')

    young_gen_data = {int(k): v for k, v in data.items() if start_page <= int(k) <= end_page }
    counts = list(young_gen_data.values())
    for acc in [0.9, 0.95, 0.97, 0.99]:
        counts = sorted(counts)[0: int(len(counts) * acc)]
        plt.figure()
        plt.hist(counts, bins=100, color='skyblue', edgecolor='black')
        # plt.hist(counts)
        # plt.tight_layout()
        plt.xlabel('Count')
        plt.ylabel('Number of Pages')
        plt.title('Histogram of Page Counts')
        plt.savefig(f'{name}_young_16M_{acc}.png')
        plt.savefig(f'{name}_young_16M_{acc}.pdf')
        plt.close()
        
    bottom_page = start_addr >> 12
    old_gen_data = {int(k): v for k, v in data.items() if bottom_page <= int(k) <= start_page }
    counts = list(old_gen_data.values())
    for acc in [0.9, 0.95, 0.97, 0.99]:
        counts = sorted(counts)[0: int(len(counts) * acc)]
        plt.figure()
        plt.hist(counts, bins=10, color='skyblue', edgecolor='black')
        # plt.hist(counts)
        # plt.tight_layout()
        plt.xlabel('Count')
        plt.ylabel('Number of Pages')
        plt.title('Histogram of Page Counts')
        plt.savefig(f'{name}_old_16M_{acc}.png')
        plt.savefig(f'{name}_old_16M_{acc}.pdf')
        plt.close()
    
    # # Sort by keys
    # data = dict(sorted(data.items()))
    
    # end_page = end_addr >> 12
    # start_page = end_page - 1048576

    # # Get young gen pages
    # young_gen_data = {int(k): v for k, v in data.items() if start_page <= int(k) <= end_page }
    
    # keys = list(young_gen_data.keys())
    # values = list(young_gen_data.values())
    # print(keys[len(young_gen_data) // 2], values[len(young_gen_data) // 2])
    # print(keys[len(young_gen_data) // 4], values[len(young_gen_data) // 4])
    # print(keys[len(young_gen_data) // 8], values[len(young_gen_data) // 8])
    # print(keys[len(young_gen_data) // 16], values[len(young_gen_data) // 16])

    # for acc in [0.9, 0.95, 0.97, 0.99]:
    #     counts = list(young_gen_data.values())
    #     counts = sorted(counts)[0: int(len(counts) * acc)]
        
    #     plt.figure()
    #     plt.hist(counts, bins=100, color='skyblue', edgecolor='black')
    #     # plt.hist(counts)
    #     # plt.tight_layout()
    #     plt.xlabel('Count')
    #     plt.ylabel('Number of Pages')
    #     plt.title('Histogram of Page Counts')
    #     plt.savefig(f'{name}_{acc}.png')
    #     plt.savefig(f'{name}_{acc}.pdf')
    #     plt.close()
    
        
def app_calculate(localrate, size, heapsize, it, benchmark, app):
    for gc in gcs:
        start_addr, end_addr = parse_gclog(gclog_path, gc, localrate, size, heapsize, it, benchmark, app)
        with open(f'{output_path}/wss_{benchmark}_{app}.json', 'r') as f:
            pages_data = json.load(f)
            divide_groups(pages_data, f'{figures_path}/wss_{benchmark}_{app}', start_addr, end_addr)

# procs = []
for localrate in localrates:
    for size in sizes:
        for heapsize in heapsizes:
            for it in iters:
                for benchmark_data in benchmarks:
                    benchmark = benchmark_data['name']
                    for app in benchmark_data['apps']:
                        # app_work(localrate, size, heapsize, it, benchmark, app)
                        # app_check(localrate, size, heapsize, it, benchmark, app)
                        app_calculate(localrate, size, heapsize, it, benchmark, app)
