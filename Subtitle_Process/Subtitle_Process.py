# Process subtitle srt file, data source: https://r3sub.com/nav.php?id=4
from dateutil import parser
import tensorflow as tf
import pandas as pd
import numpy as np
import datetime
import chardet
import sys
import re
import os
from ckiptagger import WS

def is_contains_chinese(strs:str) -> bool:
    """
    Distinguish whether the string contain Chinese.
        strs: string
    """
    for _char in strs:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False

def get_files_path(folder_path:str) -> list:
    """
    Get all subtitle file (.srt) paths under the folder.
        folder_path: folder path
    """
    file_list = []
    for i in os.listdir(f'{folder_path}'):
        file_list.append(f'{folder_path}{i}/' + os.listdir(f'{folder_path}{i}')[0])
    return file_list

def read_subtitle_file(path:str) -> pd.DataFrame:
    """
    Read subtitle file.
        path: file path
    """
    # detect encoding
    with open(path, 'rb') as rawdata:
        result = chardet.detect(rawdata.read())
        file_encoding = result['encoding']
    subtitle_number = []
    subtitle_time = []
    subtitle_content = []
    with open(path, errors='ignore', encoding=file_encoding) as f:
        ct = 0
        for i in f:
            ct += 1
            if ((i.strip() == '') & (ct >= 3)):
                ct = 0
            elif (i.strip() == ''):
                pass
                ct -= 1
            elif ct == 1:
                subtitle_number.append(i.strip())
            elif ct == 2:
                subtitle_time.append(i.strip())
            elif ct == 3:
                subtitle_content.append(i.strip())
            elif (ct == 4) & (len(i.strip()) != 0):
                ct = 3
                subtitle_content[len(subtitle_content) - 1] = subtitle_content[len(subtitle_content) - 1] + '，' + i.strip()
            else:
                raise 'error'
    subtitle = pd.DataFrame([subtitle_number, subtitle_time, subtitle_content]).T
    subtitle.columns = ['number', 'time', 'content']
    return subtitle

def arrange_subtitle(path:str) -> pd.DataFrame:
    """
    Read and arrange subtitle data as a dataframe.
        path: subtitle file path
    """
    print(path)
    subtitle = read_subtitle_file(path)
    subtitle['start_time'] = subtitle['time'].apply(lambda x: x.split('-->')[0])
    subtitle['end_time'] = subtitle['time'].apply(lambda x: x.split('-->')[1])
    subtitle['next_start_time'] = subtitle['start_time'].shift(-1)
    subtitle['next_content'] = subtitle['content'].shift(-1)
    subtitle = subtitle.loc[subtitle.next_start_time.notnull()]
    subtitle['min_interval'] = subtitle.apply(lambda x: (parser.parse(x.next_start_time) - parser.parse(x.end_time)).microseconds, axis=1)
    subtitle['interval'] = subtitle.apply(lambda x: (parser.parse(x.next_start_time) - parser.parse(x.end_time)).seconds, axis=1)
    subtitle['interval'] = subtitle['min_interval'] + subtitle['interval'] * 1000000
    subtitle = subtitle.drop(columns=['min_interval'])
    subtitle = subtitle.loc[20 :len(subtitle) - 30, :] # exlude head and tail
    subtitle = subtitle.loc[(subtitle.interval < 5000000) & (subtitle.interval > 100000)]
    subtitle['movie_name'] = path.split('/')[2]
    return subtitle

def clean_subtitle(data:pd.DataFrame) -> pd.DataFrame:
    """
    Clean dirty strings of subtitle.
        data: subtitle data
    """
    data = data.applymap(lambda x: re.sub('\（.*\）', '', x))
    data = data.applymap(lambda x: re.sub('_|-', '', x))
    data = data.applymap(lambda x: x.strip())
    for i in ['【', '】', '\[', '\]', '\'', '\"', '”', '“', '\(', '\)']:
        data['question'] = data['question'].apply(lambda x: re.sub(i, '', x))
        data['answer'] = data['answer'].apply(lambda x: re.sub(i, '', x))
    data = data.loc[(data['question'].notnull()) & (data['answer'].notnull())]
    data = data.loc[(data['question'] != '') & (data['answer'] != '')]
    return data

def word_segmentation(data:pd.DataFrame, seg_fields:list) -> pd.DataFrame:
    """
    Do word segmentation to specific fields.
        data: target data
        seg_fields: the fields would be done word segmentation
    """
    for i in seg_fields:
        data[i] = [' '.join(k) for k in ws(data[i])]
    return data

if __name__ == "__main__":
    ws = WS("./data")
    subtitle_list = get_files_path('./subtitle/')
    subtitle = pd.DataFrame()
    for i in subtitle_list:
        tmp_subtitle = arrange_subtitle(i)
        subtitle = pd.concat([subtitle, tmp_subtitle])
    subtitle = subtitle[['content', 'next_content', 'movie_name']]
    subtitle.columns = ['question', 'answer', 'movie_name']
    subtitle.to_csv('tmp_subtitle.csv', index=False)
    subtitle = clean_subtitle(subtitle)
    subtitle = word_segmentation(subtitle, ['question', 'answer'])
    subtitle.to_csv('subtitle.csv', index=False)