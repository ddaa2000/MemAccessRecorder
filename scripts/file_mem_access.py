from socket import timeout
import struct
import sys, os
import time
import io
import json
from multiprocessing import Process,Queue
import json, pickle
from util import *

class Timestamp:
    def __init__(self, sampler_s, sampler_ns, is_max):
        self.sampler_s = sampler_s
        self.sampler_ns = sampler_ns
        self._is_max = is_max
    
    def get_seconds(self):
        return self.sampler_s
        #return self.sampler_s * self.sampler_ns*1e-9
    
    def get_nanoseconds(self):
        return int(self.sampler_s * 1e9 + self.sampler_ns)

    def get_ms(self):
        return int(self.sampler_s*1e3 + self.sampler_ns*1e-6)

    def __lt__(self, other):
        if other.is_max():
            return True
        if self.sampler_s == other.sampler_s:
            return self.sampler_ns < other.sampler_ns
        return self.sampler_s < other.sampler_s
    
    def __eq__(self, other):
        if other == None:
            return False
        return self.sampler_s == other.sampler_s and self.sampler_ns == other.sampler_ns

    def is_max(self):
        return self._is_max


def read_record(f, q):
    struct_format = 'QQQIQQ'
    struct_size = struct.calcsize(struct_format)

    buffer_size = 20480
    buffered_file = io.BufferedReader(f, buffer_size)

    while True:
        bytes_data = buffered_file.read(struct_size)
        if not bytes_data:
            break
        unpacked_data = struct.unpack(struct_format, bytes_data)

        data = {
            'tid': unpacked_data[0],
            'addr': (unpacked_data[1] >> 12),
            'core_time': unpacked_data[2],
            'cpu ': unpacked_data[3],
            'timestamp': Timestamp(unpacked_data[4], unpacked_data[5], False)
        }
        q.put(data)

    # return data
def cpu_records_reader(path, q, dir_list):
    #print("dir list len",len(dir_list))
    for file in dir_list:
        with open(os.path.join(path, file),'rb') as f:
            #print(f.name())
            read_record(f, q)
    #TODO consumer size
    for i in range(0,100):
        q.put(None)
    #print("[log] read file finish, read proc quit, send None")
    exit(0)
    #print("cpu ",path, "finish")
    # i = 0
    # while os.path.exists(os.path.join(path, cpu, str(i))):
    #     with open(os.path.join(path, cpu, str(i)), 'rb') as f:
    #         read_record(f, q)
    #     i += 1
    # q.put(Timestamp(0,0,True))

x = 0

def process(data):
    global x
    x += 1



def records_consumer(q, resq, gc_events, conc_threads, njt_threads, log_ms_window):
    dicts_all = dict()
    dicts_mutator = dict()
    dicts_njt = dict()
    dicts_jt = dict()

    gc_dicts = gc_events.copy()
    for record in gc_dicts['pause']:
        record['dicts'] = {}
    for record in gc_dicts['conc']:
        record['dicts'] = {}



    def update_dict(dicts, ms, addr):
        update_dict_n(dicts, windowed(ms, log_ms_window), addr, 1)
        # windowed_ms = windowed(ms)
        # if windowed_ms not in dicts.keys():
        #     dicts[windowed_ms]={}
        # diction = dicts[windowed_ms]
        # if data['addr'] not in diction.keys():
        #     diction[data['addr']]=1
        # else
        #     diction[data['addr']]+=1

    def find_and_update(records, ms, addr):
        for record in records:
            if ms >= record['start_ms'] and ms <= record['end_ms']:
                update_dict(record['dicts'], ms, addr)
                return True
        return False


    while True:
        data = q.get()
        if data is None:
            break

        #else:
        #    print("consumer ",id," process ",len(record_fronts))

        # sec = data['timestamp'].get_seconds()
        ms = data['timestamp'].get_ms()
        tid = int(data['tid'])
        addr = data['addr']

        # global dict
        update_dict(dicts_all, ms, addr)

        if tid in njt_threads.keys():
            update_dict(dicts_njt, ms, addr)

        # conc gc dict
        if tid in conc_threads.keys():
            if find_and_update(gc_events['conc'], ms, addr):
                continue
            find_and_update(gc_events['pause'], ms, addr) # maybe the concurrent thread also do pause works?
            # even if it is not found, it shall not be pause or mutator for the tid is not correct
            continue
            
        
        # print(ms)
        if find_and_update(gc_events['pause'], ms, addr):
            continue

        update_dict(dicts_mutator, ms, addr)
            

    resq.put((dicts_all, gc_dicts, dicts_mutator, dicts_njt))
    #print("[log] queue empty,proc quit")
    exit(0)


    
def process_gc_events(gc_events):
    gc_events_new = {
        'pause': [],
        'conc': []
    }
    for event in gc_events:
        if 'conc' in event[1]:
            gc_events_new['conc'].append({
                'start_ms':  int(event[0]*1000 - float(event[2])),
                'end_ms': int(event[0]*1000),
                'type': event[1]
            })
        else:
            gc_events_new['pause'].append({
                'start_ms':  int(event[0]*1000 - float(event[2])),
                'end_ms': int(event[0]*1000),
                'type': event[1]
            })
            # print(f'{int(event[0]*1000 - float(event[2]))} {int(event[0]*1000)} {float(event[2])}')

    def comparator(x):
        return x['start_ms']

    gc_events_new['pause'].sort(key=comparator)
    gc_events_new['conc'].sort(key=comparator)

    return gc_events_new


def process_thread_info(thread_info):
    conc_threads = {}
    njt_threads = {}
    for info in thread_info['conc_gcthread']['info']:
        conc_threads[int(info['tid'])] = {
            "name": info['name']
        }
    for info in thread_info['non_jthread']['info']:
        njt_threads[int(info['tid'])] = {
            "name": info['name']
        }
    return conc_threads, njt_threads




# print(Timestamp(0,1) < None)

records_path = sys.argv[1]
json_path = sys.argv[2]
n_proc = int(sys.argv[3])
output_path = sys.argv[4]
log_ms_window=6
logs_ms_small_down_sample=10

# how many thread read disk and which files it should read?
cpus = [ file for file in os.listdir(records_path) if file.isdigit() ]
# TODO detect n times of cpu maximum disk read

# thread_num = cpus*n


id = 0

with open(json_path) as f:
    gc_meta = json.load(f)
gc_meta=gc_meta["data"]
gc_meta=gc_meta[list(gc_meta.keys())[0]] # app
gc_meta=gc_meta[list(gc_meta.keys())[0]] # gc
gc_meta=gc_meta[list(gc_meta.keys())[0]] # localrate
gc_meta=gc_meta[list(gc_meta.keys())[0]] # size
gc_events=gc_meta["gc_events"]
thread_stat=gc_meta["thread_stat"]

gc_events = process_gc_events(gc_events)
conc_threads, njt_threads = process_thread_info(thread_stat)


# print(conc_threads)
# exit(0)


dictq = Queue(maxsize=2048)
procs = []
start_time = time.time()
qs = []
for cpu in cpus:
    cpu_path = os.path.join(records_path,cpu)
    dir = os.listdir(cpu_path)
    fragment = int(len(dir)/n_proc)
    for i in range(0,n_proc):
        q = Queue(maxsize=2048)
        qs.append(q)
        # each thread own one slice
        if i == n_proc-1:
            proc = Process(target=cpu_records_reader, args=(cpu_path, q,dir[i*fragment:]))
        else:
            proc = Process(target=cpu_records_reader, args=(cpu_path, q,dir[i*fragment:(i+1)*fragment]))
        procs.append(proc)
        proc.start()

# TODO consumer:producer n:1
consumer_proc = 1
for i in range(0,len(cpus)*n_proc):
    for j in range(0,consumer_proc):
        proc = Process(target=records_consumer, args=(qs[i],dictq, gc_events, conc_threads, njt_threads, log_ms_window))
        procs.append(proc)
        proc.start()

#for proc in procs:
#    proc.join()
qsize = len(cpus)*n_proc*consumer_proc
while dictq.qsize()<qsize:
    time.sleep(1)

print("total dict num",dictq.qsize())
end_time = time.time()
execution_time = end_time - start_time
print("execution time", execution_time, "seconds")


dict_list = []
dict_njt_list = []
gc_dict_list = []
mutator_dict_list = []

time_id = []
for i in range(0,qsize):
    dict_all, gc_dict, mutator_dict, dict_njt = dictq.get()
    dict_list.append(dict_all)
    dict_njt_list.append(dict_njt)
    gc_dict_list.append(gc_dict)
    mutator_dict_list.append(mutator_dict)
    # dict_list.append(dictq.get())
    time_id = time_id + list(dict_list[i].keys())
time_id = set(time_id)
time_id = list(time_id)
time_id.sort()




dicts_final = merge_dict(dict_list)
dicts_njt_final = merge_dict(dict_njt_list)

gc_dicts_final = gc_events.copy()

for i in range(0,len(gc_dicts_final['pause'])):
    record = gc_dicts_final['pause'][i]
    gds = [d['pause'][i]['dicts'] for d in gc_dict_list]
    record['dicts'] = merge_dict(gds)
for i in range(0,len(gc_dicts_final['conc'])):
    record = gc_dicts_final['conc'][i]
    gds = [d['conc'][i]['dicts'] for d in gc_dict_list]
    record['dicts'] = merge_dict(gds)

mutator_dicts_final = merge_dict(mutator_dict_list)



# dicts={}

# results_all = dict()
# for sid in time_id:
#     result = dict()
#     for diction in dict_list:
#         if sid in diction.keys():
#             result.update(diction[sid])
#     print("time ",sid,"s : wss = ",len(result)*4,"K")
#     results_all[sid] = result
#     # result.clear()

with open(f'{output_path}-all.pkl', 'wb+') as f:
    pickle.dump(dicts_final, f)

with open(f'{output_path}-gc.pkl', 'wb+') as f:
    pickle.dump(gc_dicts_final, f)

with open(f'{output_path}-mutator.pkl', 'wb+') as f:
    pickle.dump(mutator_dicts_final, f)

with open(f'{output_path}-njt.pkl', 'wb+') as f:
    pickle.dump(dicts_njt_final, f)


# dicts_final_small = down_sample(dicts_final, logs_ms_small_down_sample)

# gc_dicts_final_small = gc_events.copy()

# for i in range(0,len(gc_dicts_final_small['pause'])):
#     gc_dicts_final_small['pause'][i]['dicts'] = down_sample(gc_dicts_final['pause'][i]['dicts'], logs_ms_small_down_sample)
# for i in range(0,len(gc_dicts_final_small['conc'])):
#     gc_dicts_final_small['conc'][i]['dicts'] = down_sample(gc_dicts_final['conc'][i]['dicts'], logs_ms_small_down_sample)

# mutator_dicts_final_small =down_sample(mutator_dicts_final, logs_ms_small_down_sample)


# with open(f'{output_path}-all-small.pkl', 'wb+') as f:
#     pickle.dump(dicts_final_small, f)

# with open(f'{output_path}-gc-small.pkl', 'wb+') as f:
#     pickle.dump(gc_dicts_final_small, f)

# with open(f'{output_path}-mutator-small.pkl', 'wb+') as f:
#     pickle.dump(mutator_dicts_final_small, f)



exit(0)   


