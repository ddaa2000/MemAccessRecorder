def update_dict_n(dicts, index, addr, n):
    if index not in dicts.keys():
        dicts[index]={}
    diction = dicts[index]
    if addr not in diction.keys():
        diction[addr]=n
    else:
        diction[addr]+=n

def windowed(val, log):
    return (val >> log) << log

def merge_dict(dicts):
    result = {}
    for d in dicts:
        for key in d.keys():
            for addr in d[key].keys():
                update_dict_n(result, key, addr, d[key][addr])
    return result

def down_sample(d, log):
    result = {}
    for key in d.keys():
        for addr in d[key].keys():
            update_dict_n(result, windowed(key, log), addr, d[key][addr])
    return result


def parse_ps_heap_region(lines):
    young_regex = r'PSYoungGen\s+total\s+\d+K, used \d+K \[(0x[0-9a-fA-F]+), .*?, (0x[0-9a-fA-F]+)\)'
    old_regex = r'ParOldGen\s+total\s+\d+K, used \d+K \[(0x[0-9a-fA-F]+), .*?, (0x[0-9a-fA-F]+)\)'
    for line in lines:
        match = re.search(young_regex, line)
        if match:
            young_start = int(match.group(1), 16)
            young_end = int(match.group(2), 16)

        match = re.search(old_regex, line)
        if match:
            old_start = int(match.group(1), 16)
            old_end = int(match.group(2), 16)
            break
    return old_start, young_end


def parse_g1_heap_region(lines):
    regex = r'garbage-first\s+heap\s+total \d+K, used \d+K \[(0x[0-9a-fA-F]+), (0x[0-9a-fA-F]+)\)'
    for line in lines:
        match = re.search(regex, line)
        if match:
            start = int(match.group(1), 16)
            end = int(match.group(2), 16)
            break
    return start, end


def parse_genshen_heap_region(lines):
    regex = r'\[(0x[0-9a-fA-F]+), (0x[0-9a-fA-F]+)\)'
    found = False
    for line in lines:
        if found:
            match = re.search(regex, line)
            if match:
                start = int(match.group(1), 16)
                end = int(match.group(2), 16)
                break
        found = False
        if 'Reserved region:' in line:
            found = True
    return start, end
        
def parse_gclog(gc, localrate, size, heapsize, it, benchmark, app):
    global gclog_path
    with open(f'{gclog_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}.gclog') as f:
        if 'ps' in gc:
            start, end = parse_ps_heap_region(f.readlines())
        elif 'g1' in gc:
            start, end = parse_g1_heap_region(f.readlines())
        elif 'genshen' in gc:
            start, end = parse_genshen_heap_region(f.readlines())
    
    print(f'{start} {end} {(end-start)>>30}')
    return start, end

def load_data(gc, localrate, size, heapsize, it, benchmark, app):
    with open(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}-all.pkl', 'rb') as f:
        data_all = pickle.load(f)
    with open(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}-gc.pkl', 'rb') as f:
        data_gc = pickle.load(f)
    with open(f'{pkl_path}/{benchmark}_{localrate}p_xmx{heapsize}g_{gc}_{app}_{size}_{it}-mutator.pkl', 'rb') as f:
        data_mutator = pickle.load(f)
    data_njt = {}
    return data_all, data_gc, data_mutator, data_njt