import pandas as pd
import numpy as np
import re
import sys
import json

'''
config:
{
    "probability_column": "redeem_ct",
    "filter_column": "輸入篩選欄位名稱",
    "filter_value": "輸入篩選閾值(>=n次)",
    "send": "提交"
}
'''

def repeat_list(data, probibility_column, filter_column, filter_value):
    if filter_column != '輸入篩選欄位名稱':
        repeat_list = data.loc[data[filter_column] >= int(filter_value)]
    else:
        repeat_list = data
    repeat_list = repeat_list['user_id'].repeat(repeat_list[probibility_column])
    repeat_list = pd.DataFrame(repeat_list).merge(data, how='left', on='user_id')
    return repeat_list

def read_config(file_name):
    file_name = re.sub('.csv', '.json', file_name)
    with open(f'./Upload/{file_name}', 'r') as reader:
        config = json.loads(reader.read())
    return config

def main(file_name):
    config = read_config(file_name)
    lottery = pd.read_csv(f'./Upload/{file_name}')
    lottery = repeat_list(lottery, config['probability_column'], config['filter_column'], config['filter_value'])
    download_file = 'completed_' + file_name
    lottery.to_csv(f'./Download/{download_file}', index=False)

if __name__ == "__main__":
    main(sys.argv[0])