import os
import sys
from util import *

dir = '/home/huaziyue/eval-disagg-gc/logs/a-qcd-8g'

json_dir = f'{dir}/logs-json'
raw_dir = f'{dir}/logs-raw'
output_dir = './data-qcd-8g'

for file in os.listdir(json_dir):
    if '100p' in file and 'conc04' in file and 'qrd' in file:
    # if 'quickcached_100p_xmx8g_g1_no_adap' in file:
        print(file)
        file_name_short = file.replace('.json', '')
        print(file_name_short)
        mem_acc_dir = f'{raw_dir}/{file_name_short}_mem_access'
        json_file = f'{json_dir}/{file}'
        output_file = f'{output_dir}/{file_name_short}'
        # print(f'python3 file_mem_access.py {mem_acc_dir} {json_file} 10 {output_file}')
        os.system(f'python3 file_mem_access.py {mem_acc_dir} {json_file} 10 {output_file}')
