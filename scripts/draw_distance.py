import json
import matplotlib.pyplot as plt
import sys
import os
import re
import pickle
import numpy as np
import multiprocessing
from utils import *



pkl_path = './data-qcd-8g'
gclog_path = '../eval-disagg-gc/logs/a-qcd-8g/logs-raw'
output_path = './figures-qcd-8g'
# step = int(sys.argv[2])

localrates = ['100']
# localrates = ['25']
sizes = ['large']
heapsizes = ['8']
young_gen_size_in_bytes = 1 << 30
iters = ['1']
benchmarks = [
    # {'name': 'graphchi', 'apps': ['kc']},
    # {'name': 'graphchi', 'apps': ['wcc']},
    # {'name': 'spark', 'apps': ['km', 'nb']},
    # {'name': 'spark', 'apps': ['km']},
    # {'name': 'corenlp', 'apps': ['kbp']},
    {'name': 'quickcached', 'apps': ['qrd']}
]
# gcs = ['ps', 'psnew', 'psmc', 'g1', 'ps_young4g', 'g1_young4g', 'genshen']
gcs = ['g1_no_adaptive_young1g_conc04']
# gcs = ['ps']


# gcs = ['ps', 'psnew']

# gcs = ['ps']


steps = [1, 5, 10, 20]



def draw_gens(file_prefix, data, start_addr, end_addr, log_region_pages):

    timestamps = [int(d) for d in data.keys()]
    print(len(timestamps))
    timestamps.sort()
    print(timestamps[-1] - timestamps[0])

    xs_young = []
    ys_young = []
    xs_old = []
    ys_old = []

    ranges = []

    young_gen_pages = young_gen_size_in_bytes >> 12
    young_gen_bottom_index = end_addr - young_gen_pages


    index = 0
    for t in timestamps:
        # index += 1
        # if index % 1000 != 0:
        #     continue
        for item in data[t].keys():
            region_index = int(item) >> log_region_pages
            if item >= start_addr and item <= end_addr:
                if item > young_gen_bottom_index:
                    xs_young.append(t)
                    ys_young.append(region_index)
                else:
                    xs_old.append(t)
                    ys_old.append(region_index)
        
    plt.figure(figsize=(60,60))
    plt.scatter(xs_young, ys_young, s=1, c='red')
    plt.scatter(xs_old, ys_old, s=1, c='blue')
    plt.savefig(f"{file_prefix}.png")
    plt.close()


def draw_point_graph(file_prefix, data, start_addr, end_addr, log_region_pages):

    timestamps = [int(d) for d in data.keys()]
    timestamps.sort()
    print(timestamps[-1] - timestamps[0])

    print(timestamps[5000:5100])
    acc = 0

    # xs = []
    # ys = []
    # cs = []

    present = 0
    prev_acc_num = {}

    # distance_distribution = {}
    # min_v = 1 << 40
    # max_v = -1
    # total_num = 0
    distance_all = []
    distance_young = []
    distance_old = []
    young_gen_pages = young_gen_size_in_bytes >> 12
    young_gen_bottom_index = end_addr - young_gen_pages

    ranges = []
    range_dict = {}

    for j in [10000, 100000, 1000000, 10000000]:
        for i in range(1, 10):
            range_dict[i*j] = {
                'xs': [timestamps[0], timestamps[0]],
                'ys': [start_addr, end_addr],
            }
            ranges.append(i * j)


    for t in timestamps:
        regions = set()
        for item in data[t].keys():
            acc += data[t][item]
            region_index = int(item) >> log_region_pages
            if item >= start_addr and item <= end_addr and not region_index in regions:
                # print(region_index - boundary)
                if not region_index in prev_acc_num.keys():
                    prev_acc_num[region_index] = present
                else:
                    distance = present - prev_acc_num[region_index]
                    prev_acc_num[region_index] = present
                    distance_all.append(distance)
                    for r in ranges:
                        if distance <= r:
                            range_dict[r]['xs'].append(t)
                            range_dict[r]['ys'].append(region_index << log_region_pages)
                            break
                    if item > young_gen_bottom_index:
                        distance_young.append(distance)
                    else:
                        distance_old.append(distance)
                    # windowed_distance = windowed(distance, 10)
                    # if not windowed_distance in distance_distribution.keys():
                    #     distance_distribution[windowed_distance] = 0
                    # distance_distribution[windowed_distance] += 1
                    # total_num += 1
                    # min_v = min(windowed_distance, min_v)
                    # max_v = max(windowed_distance, max_v)
                present += 1
            regions.add(region_index)

    # xs_young = []
    # ys_young = []
    # xs_old = []
    # ys_old = []

    # ranges = []


    # index = 0
    # for t in timestamps:
    #     # index += 1
    #     # if index % 1000 != 0:
    #     #     continue
    #     for item in data[t].keys():
    #         acc += data[t][item]
    #         region_index = int(item) >> log_region_pages
    #         if item >= start_addr and item <= end_addr:
    #             if item > young_gen_bottom_index:
    #                 xs_young.append(t)
    #                 ys_young.append(region_index)
    #             else:
    #                 xs_old.append(t)
    #                 ys_old.append(region_index)
        
    # plt.figure(figsize=(60,60))
    # plt.scatter(xs_young, ys_young, s=1, c='red')
    # plt.scatter(xs_old, ys_old, s=1, c='blue')
    # plt.savefig(f"{file_prefix}.png")
    # plt.close()

    for r in range_dict.keys():
        plt.figure(figsize=(60,60))
        plt.scatter(range_dict[r]['xs'], range_dict[r]['ys'], s=1, c='red')
        plt.savefig(f"{file_prefix}_region{log_region_pages}_range{r}_hist_all.png")
        plt.close()


    # sorted_list = sorted(distance_all)
    # cut_index = int(len(sorted_list) * 0.95)

    # plt.figure(figsize=(60,10))
    # plt.hist(sorted_list[:cut_index], bins=200, alpha=0.7, color='blue')
    # plt.savefig(f"{file_prefix}_region{log_region_pages}_hist_all.png")
    # plt.close()

    # sorted_list = sorted(distance_young)
    # cut_index = int(len(sorted_list) * 0.95)

    # plt.figure(figsize=(60,10))
    # plt.hist(sorted_list[:cut_index], bins=200, alpha=0.7, color='blue')
    # plt.savefig(f"{file_prefix}_region{log_region_pages}_hist_young.png")
    # plt.close()

    # sorted_list = sorted(distance_old)
    # cut_index = int(len(sorted_list) * 0.95)

    # plt.figure(figsize=(60,10))
    # plt.hist(sorted_list[:cut_index], bins=200, alpha=0.7, color='blue')
    # plt.savefig(f"{file_prefix}_region{log_region_pages}_hist_old.png")
    # plt.close()

def draw_point_graph_conc_nonconc(file_prefix, data_conc, data_mutator, data_all, start_addr, end_addr):

    timestamps = [int(d) for d in data_all.keys()]
    timestamps.sort()

    xs = []
    ys = []
    cs = []

    for t in timestamps:
        visited_regions = {}
        if t in data_mutator.keys():
            for item in data_mutator[t].keys():
                region_index = int(item) >> 12
                if region_index >= start_addr and region_index <= end_addr:
                    # print(region_index - boundary)
                    if not (region_index - start_addr) in visited_regions.keys():
                        visited_regions[region_index - start_addr] = 0 # 16MB
                        xs.append(t)
                        ys.append(float(region_index - start_addr)/(1<<6))
                        cs.append('#008000')
        
        visited_regions = {}
        if t in data_conc.keys():
            for item in data_conc[t].keys():
                region_index = int(item) >> 12
                if region_index >= start_addr and region_index <= end_addr:
                    # print(region_index - boundary)
                    if not (region_index - start_addr) in visited_regions.keys():
                        visited_regions[region_index - start_addr] = 0 # 16MB
                        xs.append(t)
                        ys.append(float(region_index - start_addr)/(1<<6))
                        cs.append('red')
    # percentiles = np.percentile(cs, [10, 20, 50, 70, 90, 95, 99])
    # print(percentiles)
    
    plt.figure(figsize=(60,60))
    plt.scatter(xs, ys, s=1, c=cs)
    plt.savefig(f"{file_prefix}.png")
    plt.close()



def draw_point_graphs(file_prefix, data_all, data_gc, data_mutator, data_njt, start_addr, end_addr):
    # draw_point_graph(f'{file_prefix}_all', data_all, start_addr, end_addr)
    
    # draw_point_graph(f'{file_prefix}_njt', data_njt, start_addr, end_addr)

    draw_gens(f'{file_prefix}_young_old', data_all, start_addr, end_addr, 0)

    # pause_data = data_gc['pause']
    # pause_dict = merge_dict([d['dicts'] for d in pause_data])

    # conc_data = data_gc['conc']
    # conc_dict = merge_dict([d['dicts'] for d in conc_data])

    # nonconc_dict = merge_dict([data_mutator, pause_dict])

    # gc_dict = merge_dict([pause_dict, conc_dict])

    # for log_region in [0, 4]:
    # # for log_region in [0]:
    #     # draw_point_graph(f'{file_prefix}_mutator', data_mutator, start_addr, end_addr, log_region)
    #     draw_point_graph(f'{file_prefix}_nonconc', nonconc_dict, start_addr, end_addr, log_region)


    # draw_point_graph_conc_nonconc(f'{file_prefix}_conc_nonconc', conc_dict, data_mutator, data_all, start_addr, end_addr)

    # draw_point_graph(f'{file_prefix}_pause', pause_dict, start_addr, end_addr)
    # draw_point_graph(f'{file_prefix}_conc', conc_dict, start_addr, end_addr)
    # draw_point_graph(f'{file_prefix}_gc', gc_dict, start_addr, end_addr)
    

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
    for gc in gcs:
        file_prefix = f"{output_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access"
        start_addr, end_addr = parse_gclog(gclog_path, gc, localrate, size, heapsize, it, benchmark, app)
        start_addr_page = start_addr >> 12
        end_addr_page = end_addr >> 12
        data_all, data_gc, data_mutator, data_njt = load_data(pkl_path, gc, localrate, size, heapsize, it, benchmark, app)
        

        draw_point_graphs(file_prefix, data_all, data_gc, data_mutator, data_njt, start_addr_page, end_addr_page)

    #     pause_data = data_gc['pause']
    #     pause_dict = merge_dict([d['dicts'] for d in pause_data])

    #     conc_data = data_gc['conc']
    #     conc_dict = merge_dict([d['dicts'] for d in conc_data])

    #     gc_dict = merge_dict([pause_dict, conc_dict])

    #     acc_time_limits = get_acc_num_time_limits(data_all, 1000000)

        
    #     acc_time_limits_new = [(d - acc_time_limits[0])/1000 for d in acc_time_limits]
    #     print(len(acc_time_limits_new))
    #     print(acc_time_limits_new)

    #     limits[gc] = {"start": 0, "end": len(acc_time_limits)}

    #     data_all_gcs['data_all'][gc] =  merge_by_time_limits(data_all, acc_time_limits)
    #     data_all_gcs['data_mutator'][gc] = merge_by_time_limits(data_mutator, acc_time_limits)
    #     data_all_gcs['data_gc'][gc] = merge_by_time_limits(gc_dict, acc_time_limits)
    #     # data_all_gcs['data_conc'][gc] = merge_by_time_limits(conc_dict, acc_time_limits)
    #     # data_all_gcs['data_pause'][gc] = merge_by_time_limits(pause_dict, acc_time_limits)
    #     # data_all_gcs['data_mutator_and_conc'][gc] =  merge_by_time_limits(merge_dict([data_all_gcs['data_mutator'][gc], data_all_gcs['data_conc'][gc]]), acc_time_limits)

    # s_procs = []
    # # # for k in data_all_gcs.keys():
    # # #     wss_prefix = f"{output_path}/{k}_{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}"
    # # #     draw_wss(wss_prefix, data_all_gcs[k])

    # for k in data_all_gcs.keys():
    #     def draw_one_metric():
    #         wss_prefix = f"{output_path}/{k}_{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}"
    #         draw_wss(wss_prefix, data_all_gcs[k], limits)
    #     s_proc = multiprocessing.Process(target=draw_one_metric, args=())
    #     s_procs.append(s_proc)
    #     s_proc.start()
    # for p in s_procs:
    #     p.join()
    
    # # wss_prefix = f"{output_path}/data_mutator_and_conc_{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}"
    # # draw_wss(wss_prefix, data_all_gcs['data_mutator_and_conc'])


# procs = []
for localrate in localrates:
    for size in sizes:
        for heapsize in heapsizes:
            for it in iters:
                for benchmark_data in benchmarks:
                    benchmark = benchmark_data['name']
                    for app in benchmark_data['apps']:
                        app_work(localrate, size, heapsize, it, benchmark, app)
                        # proc = multiprocessing.Process(target=app_work, args=(localrate, size, heapsize, it, benchmark, app))
                        # procs.append(proc)
                        # proc.start()

# for p in procs:
#     p.join()
# exit(-1)


    


# def single_app(gcs, localrate, size, heapsize, it, benchmark, app):
    
#     global steps
#     global boundary
#     global pkl_path


#     results_all = {}
#     # if os.path.exists(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}_wss_step{steps[0]}(s).png'):
#     #     return



#     for gc in gcs:
#         if not os.path.exists(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access_all.pkl'):
#             return

#     for gc in gcs:
#         start, end = parse_gclog(gc, localrate, size, heapsize, it, benchmark, app)
#         start = start >> 24
#         end = end >> 24

#         results_all[gc] = {}

#         # if os.path.exists(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access.pkl'):
#         #     continue

#         with open(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access_all.pkl', 'rb') as f:
#             data = pickle.load(f)
#             # with open(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access.pkl', 'wb') as f:
#             #     pickle.dump(data, f)

#         timestamps = [int(d) for d in data.keys()]
#         timestamps.sort()

#         xs = []
#         ys = []
                    
#         # for step in [1, 5, 10, 20]:
#         #     results_all[gc][step] = {}
#         #     present = timestamps[0]
#         #     present_dict = dict()

#         #     ts = []
#         #     wss = []

#         #     for t in timestamps:
#         #         if t - present == step:
#         #             wss.append(len(present_dict)*4.0/1024/1024)
#         #             ts.append(t)
#         #             present_dict.clear()
#         #             present = t
                    
#         #         present_dict.update(data[str(t)])

#         #     results_all[gc][step]['wss'] = wss
#         #     results_all[gc][step]['ts'] = [t - ts[0] for t in ts]


#         for t in timestamps:
#             visited_regions = set()
#             for item in data[t].keys():
#                 region_index = int(item) >> 12
#                 if region_index >= start and region_index <= end:
#                     # print(region_index - boundary)
#                     visited_regions.add(region_index - start) # 16MB
#             for item in visited_regions:
#                 xs.append(t)
#                 # print(float(item)/(1<<6))
#                 ys.append(float(item)/(1<<6)) #gb
#         plt.figure(figsize=(60,10))
#         plt.scatter(ys, xs, s=1)
#         plt.savefig(f"{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}_mem_access.png")
#         plt.close()

#     # for step in steps:
#     #     plt.figure()
#     #     for gc in gcs:
#     #         plt.plot(results_all[gc][step]['ts'], results_all[gc][step]['wss'], label=gc)
#     #     plt.legend()
#     #     plt.savefig(f"{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{app}_{size}_{it}_wss_step{step}(s).png")
#     #     plt.close()