import json
import matplotlib.pyplot as plt
import sys
import os
import re
import pickle
import numpy as np
import multiprocessing
from utils import *



pkl_path = '/home/huaziyue/eval-disagg-gc/logs/a-median/data'
gclog_path = '/home/huaziyue/eval-disagg-gc/logs/a-median/logs-raw'
output_path = '/home/huaziyue/eval-disagg-gc/logs/a-median/data'
# step = int(sys.argv[2])

target_window = 3000000000
sample_rate = 1000
sample_window = target_window / sample_rate

# localrates = ['25', '100']
localrates = ['100']
sizes = ['median']
heapsizes = ['32']
iters = ['1']
benchmarks = [
    # {'name': 'graphchi', 'apps': ['kc']},
    {'name': 'graphchi', 'apps': ['wcc']},
    {'name': 'spark', 'apps': ['km', 'nb']},
    {'name': 'dacapo', 'apps': ['h2']},
    {'name': 'corenlp', 'apps': ['kbp']},
    {'name': 'quickcached', 'apps': ['yqrdh', 'yqrdu']}
]
# gcs = ['ps', 'psnew', 'psmc', 'g1', 'ps_young4g', 'g1_young4g', 'genshen']
# gcs = ['g1_no_adaptive_young1g_conc04']
gcs = ['ps', 'psnew', 'psmc']


# gcs = ['ps', 'psnew']

# gcs = ['ps']

results_all = {}


steps = [1, 5, 10, 20]


def wss_cal(data):
    # print(len(data))
    # data = down_sample(data, step_log)
    

    timestamps = [int(d) for d in data.keys()]
    timestamps.sort()
    print(len(timestamps))

    ts = timestamps
    wss_list = [[],[],[],[],[],[]]
    all = []
    for t in ts:
        wss = [0,0,0,0,0,0]
        # print(len(data[t].keys()))
        all.append(len(data[t].keys()))
        for k in data[t].keys():
            value = data[t][k]
            if value < 2:
                wss[0] += 1
            elif value < 4:
                wss[1] += 1
            elif value < 8:
                wss[2] += 1
            elif value < 16:
                wss[3] += 1
            elif value < 32:
                wss[4] += 1
            else:
                wss[5] += 1
        for i in range(0, 6):
            wss_list[i].append(wss[i]*4.0/1024/1024)
            # wss_list[i].append(wss[i]*1.0)


    ts = [t - ts[0] for t in ts]

    return ts, wss_list, all


def wss_no_weight(data):
    timestamps = [int(d) for d in data.keys()]
    timestamps.sort()
    print(len(timestamps))

    ts = timestamps
    wss_list = []
    for t in ts:
        # print(len(data[t].keys()))
        acc = len(data[t].keys())
        wss_list.append(acc*4.0/1024/1024)

    ts = [t - ts[0] for t in ts]

    return ts, wss_list
         

def acc_per_period(data_all):
    for timestamp in data_all.keys():
        acc = 0
        for page_num in data_all[timestamp].keys():
            acc += data_all[timestamp][page_num]
        print(acc)

def get_acc_num_time_limits(data, window_size):
    result = {}
    acc_all = 0
    acc_time_limits = []
    timestamps = list(data.keys())
    timestamps.sort()
    for timestamp in timestamps:
        acc = 0
        for page_num in data[timestamp].keys():
            acc += data[timestamp][page_num]
        # print(acc)
        acc_all += acc
        if acc_all >= window_size:
            acc_all %= window_size
            acc_time_limits.append(timestamp)
    if acc_time_limits[-1] != timestamps[-1]:
        acc_time_limits.append(timestamps[-1])
    return acc_time_limits

def merge_by_time_limits(data, acc_time_limits):
    result = {}
    present = 0

    timestamps = list(data.keys())
    timestamps.sort()
    for timestamp in timestamps:
        while timestamp > acc_time_limits[present]:
            if present not in result.keys():
                result[present] = {0: 0}
            # else:
                # print(f'add {(timestamp - acc_time_limits[0])/1000.0} {present} {(acc_time_limits[present] - acc_time_limits[0])/1000.0} {len(result[present].keys())}')
            present += 1
        for addr in data[timestamp].keys():
            update_dict_n(result, present, addr, data[timestamp][addr])
    return result




def app_work(localrate, size, heapsize, it, benchmark, app):
    data_all_gcs = {
        'data_all': {},
        'data_mutator': {},
        'data_gc': {},
        # 'data_conc': {},
        # 'data_pause': {},
        # 'data_mutator_and_conc': {},
    }

    limits = {}
    results_all['wss'][benchmark][app] = {}

    for gc in gcs:
        file_prefix = f"{output_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access"
        start_addr, end_addr = parse_gclog(gclog_path, gc, localrate, size, heapsize, it, benchmark, app)
        start_addr = start_addr >> 24
        end_addr = end_addr >> 24
        data_all, data_gc, data_mutator, data_njt = load_data(pkl_path, gc, localrate, size, heapsize, it, benchmark, app)
        

        pause_data = data_gc['pause']
        pause_dict = merge_dict([d['dicts'] for d in pause_data])

        conc_data = data_gc['conc']
        conc_dict = merge_dict([d['dicts'] for d in conc_data])

        gc_dict = merge_dict([pause_dict, conc_dict])

        acc_time_limits = get_acc_num_time_limits(data_all, sample_window)

        
        acc_time_limits_new = [(d - acc_time_limits[0])/1000 for d in acc_time_limits]
        print(len(acc_time_limits_new))
        print(acc_time_limits_new)

        limits[gc] = {"start": 0, "end": len(acc_time_limits)}

        data_all_gcs['data_all'][gc] =  merge_by_time_limits(data_all, acc_time_limits)
        data_all_gcs['data_mutator'][gc] = merge_by_time_limits(data_mutator, acc_time_limits)
        data_all_gcs['data_gc'][gc] = merge_by_time_limits(gc_dict, acc_time_limits)

        wss_all = wss_no_weight(merge_by_time_limits(data_all, acc_time_limits))

        results_all['wss'][benchmark][app][gc] = wss_all

    # s_procs = []
    # # for k in data_all_gcs.keys():
    # #     wss_prefix = f"{output_path}/{k}_{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}"
    # #     draw_wss(wss_prefix, data_all_gcs[k])

    # for k in data_all_gcs.keys():
    #     def draw_one_metric():
    #         wss_prefix = f"{output_path}/{k}_{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}"
    #         draw_wss(wss_prefix, data_all_gcs[k], limits)
    #     s_proc = multiprocessing.Process(target=draw_one_metric, args=())
    #     s_procs.append(s_proc)
    #     s_proc.start()
    # for p in s_procs:
    #     p.join()
    
    # wss_prefix = f"{output_path}/data_mutator_and_conc_{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}"
    # draw_wss(wss_prefix, data_all_gcs['data_mutator_and_conc'])

results_all['sample_rate'] = sample_rate
results_all['wss'] = {}

# procs = []
for localrate in localrates:
    for size in sizes:
        for heapsize in heapsizes:
            for it in iters:
                for benchmark_data in benchmarks:
                    benchmark = benchmark_data['name']
                    results_all['wss'][benchmark] = {}
                    for app in benchmark_data['apps']:
                        app_work(localrate, size, heapsize, it, benchmark, app)

with open(f'{output_path}/wss.json', 'w+') as f:
    json.dump(results_all, f)
