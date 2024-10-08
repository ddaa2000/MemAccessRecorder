import os
import sys
from utils import *

dir = '/home/huaziyue/eval-disagg-gc/logs/a-median'

json_dir = f'{dir}/logs-json'
raw_dir = f'{dir}/logs-raw'
output_dir = f'{dir}/data'

for file in os.listdir(json_dir):
    if 'quick' in file or 'dacapo' in file:
        print(file)
        file_name_short = file.replace('.json', '')
        print(file_name_short)
        mem_acc_dir = f'{raw_dir}/{file_name_short}_mem_access'
        json_file = f'{json_dir}/{file}'
        output_file = f'{output_dir}/{file_name_short}'
        # print(f'python3 file_mem_access.py {mem_acc_dir} {json_file} 10 {output_file}')
        os.system(f'python3 file_mem_access.py {mem_acc_dir} {json_file} 10 {output_file}')
