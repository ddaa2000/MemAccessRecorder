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
input_path = '/home/huaziyue/eval-disagg-gc/logs/a-median/data'
# step = int(sys.argv[2])

sample_rate = 1000

# localrates = ['25', '100']
localrates = ['100']
sizes = ['median']
heapsizes = ['32']
iters = ['1']
apps = ['GWCC', 'SKM', 'SNB', 'KBP']
benchmarks = [
    # {'name': 'graphchi', 'apps': ['kc']},
    {'name': 'graphchi', 'apps': ['wcc'], 'short_names': ['GWCC']},
    {'name': 'spark', 'apps': ['km', 'nb'], 'short_names': ['SKM', 'SNB']},
    # {'name': 'spark', 'apps': ['pr']},
    {'name': 'corenlp', 'apps': ['kbp'], 'short_names': ['KBP']},
    # {'name': 'quickcached', 'apps': ['qrd']}
]

benchmark_mapping = {
    'graphchi': {
        'wcc': 'GWCC',
    },
    'spark': {
        'km': 'SKM',
        'nb': 'SNB',
    },
    'corenlp': {
        'kbp': 'KBP',
    },
}

colors = { 'ms': 'steelblue', 'psnew':'steelblue', 'psmc':'steelblue',
            'ps': 'darkgoldenrod', 'g1': 'darkgoldenrod',
            'genshen': 'red'}

# gcs = ['ps', 'psnew', 'psmc', 'g1', 'ps_young4g', 'g1_young4g', 'genshen']
# gcs = ['g1_no_adaptive_young1g_conc04']
gcs = ['ps', 'psnew', 'psmc']


# gcs = ['ps', 'psnew']

# gcs = ['ps']

# procs = []
# for localrate in localrates:
#     for size in sizes:
#         for heapsize in heapsizes:
#             for it in iters:
#                 for benchmark_data in benchmarks:
#                     benchmark = benchmark_data['name']
#                     results_all['wss'][benchmark] = {}
#                     for app in benchmark_data['apps']:
#                         app_work(localrate, size, heapsize, it, benchmark, app)

with open(f'{input_path}/wss-1.json') as f:
    results_all = json.load(f)


wss_data = results_all['wss']

wss_values = {}

for benchmark in wss_data.keys():
    for app in wss_data[benchmark].keys():
        wss_values[benchmark_mapping[benchmark][app]] = {}
        for gc in wss_data[benchmark][app].keys():
            wss_values[benchmark_mapping[benchmark][app]][gc] = wss_data[benchmark][app][gc]


fig = plt.figure(figsize=(3*len(apps),3), constrained_layout=False)
fig, axes = plt.subplots(nrows=1, ncols=len(apps), figsize=(3*len(apps),3.8))

instr_window = 3000000000 / 1000000

for i in range(0, len(apps)):
    ax = axes[i]
    for gc in gcs:
        l = [n * instr_window for n in range(0, len(wss_values[apps[i]][gc][1]))]
        ax.plot(l, wss_values[apps[i]][gc][1])
    ax.set_ylim(0, 6)
    ax.grid(axis='y', linestyle='dashed', linewidth=0.7)
    ax.set_title(apps[i])
    if i == 0:
        ax.set_xlabel('Memory Access Instruction Index')
        ax.set_ylabel('WSS (GB)')
        

plt.savefig('test.pdf')
plt.savefig('test.png')





