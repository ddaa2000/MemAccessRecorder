import json
import matplotlib.pyplot as plt
import sys

plt.style.use('../../../fig_scripts/usenix.mplstyle')

input_path = '/home/xiaojiawei/eval-disagg-gc/logs/wss/'
# step = int(sys.argv[2])

# localrates = ['25', '100']
localrates = ['100']
sizes = ['median']
heapsizes = ['32']
iters = ['1']
apps = ['SKM', 'SNB', 'GWC', 'KBP', 'QRIh', 'DH2', ]
benchmarks = [
    # {'name': 'graphchi', 'apps': ['kc']},
    {'name': 'graphchi', 'apps': ['wcc'], 'short_names': ['GWC']},
    {'name': 'spark', 'apps': ['km', 'nb'], 'short_names': ['SKM', 'SNB']},
    # {'name': 'spark', 'apps': ['pr']},
    {'name': 'corenlp', 'apps': ['kbp'], 'short_names': ['KBP']},
    {'name': 'quickcached', 'apps': ['yqrdh', 'yqrdu'], 'short_names': ['QRIh', 'QRIu']},
    {'name': 'dacapo', 'apps': ['h2'], 'short_names': ['DH2']},
]

benchmark_mapping = {
    'graphchi': {
        'wcc': 'GWC',
    },
    'spark': {
        'km': 'SKM',
        'nb': 'SNB',
    },
    'corenlp': {
        'kbp': 'KBP',
    },
    'quickcached': {
        'yqrdh': 'QRIh',
        'yqrdu': 'QRIu',
    },
    'dacapo': {
        'h2': 'DH2',
    },
}

colors = { 'ms': 'steelblue', 'psnew':'steelblue', 'psmc':'steelblue',
            'ps': 'darkgoldenrod', 'g1': 'darkgoldenrod',
            'genshen': 'red'}

# gcs = ['ps', 'psnew', 'psmc', 'g1', 'ps_young4g', 'g1_young4g', 'genshen']
# gcs = ['g1_no_adaptive_young1g_conc04']
gcs = ['psnew', 'psmc', 'ps']
gc_colors = {
    'psnew': '#3C8DC7',
    'psmc': '#C4B200',
    'ps': '#A74400',
}
gc_markers = {
    'psnew': '^',
    'psmc': 's',
    'ps': 'o',
}
gc_legends = {
    'psnew': 'MSE',
    'psmc': 'MC',
    'ms': 'MSP',
    'ps': 'PS',
    'g1': 'G1',
    'g1_no_pause_limit': 'G1T',
    'genshen': 'GenShen'
}

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

with open(f'{input_path}/wss.json') as f:
    results_all = json.load(f)


wss_data = results_all['wss']

wss_values = {}

for benchmark in wss_data.keys():
    for app in wss_data[benchmark].keys():
        wss_values[benchmark_mapping[benchmark][app]] = {}
        for gc in wss_data[benchmark][app].keys():
            wss_values[benchmark_mapping[benchmark][app]][gc] = wss_data[benchmark][app][gc]

instr_window = 3000000000 / 1000000
def plotOne(app):
    for gc in gcs:
        l = [n * instr_window / 1e3 for n in range(0, len(wss_values[app][gc][1]))]
        ax.plot(
            l,
            wss_values[app][gc][1],
            color=gc_colors[gc],
            marker=gc_markers[gc],
            markersize=3,
            markerfacecolor='none',
            markeredgewidth=0.7,
            linewidth=0.7,
            label=gc_legends[gc],
        )
    # ax.set_ylim(0, 6)
    ax.grid(axis='y', linestyle='dashed', linewidth=0.7)

fig = plt.figure(figsize=(3.335,3.6), constrained_layout=False)
axd = fig.subplot_mosaic(
    """
    AB
    CD
    EF
    """,
)


ax = axd['A']
app = 'SKM'
plotOne(app)
ax.set_title(app)

ax = axd['B']
app = 'SNB'
plotOne(app)
ax.set_title(app)

ax = axd['C']
app = 'GWC'
plotOne(app)
ax.set_title(app)

ax = axd['D']
app = 'KBP'
plotOne(app)
ax.set_title(app)

ax = axd['E']
app = 'QRIh'
plotOne(app)
ax.set_title(app)

ax = axd['F']
app = 'DH2'
plotOne(app)
ax.set_title(app)

fig.supylabel('WSS [GB]')
fig.supxlabel('Memory Access Instruction Index [K]')

# Move legend of ax A to the top of figure
handles, labels = axd['A'].get_legend_handles_labels()
# position of legend
loc = bbox_to_anchor=(-0.8, 4.1)
legend = plt.legend(
    handles, labels,
    loc=loc, # position of legend
    fontsize = '8',
    ncol=3, # number of cols
    frameon=False, fancybox=False, # no boxes
    columnspacing=1, # space between cols
)

plt.subplots_adjust(top=0.91, bottom=0.1, left=0.1, right=0.98,
                    wspace=0.2, hspace=0.45)
plt.savefig(
    '/home/xiaojiawei/eval-disagg-gc/figures/wss/wss.pdf',
    dpi=400
)
plt.savefig(
    '/home/xiaojiawei/eval-disagg-gc/figures/wss/wss.png',
    dpi=200
)
