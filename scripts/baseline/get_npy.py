import os
import csv
import pickle
import numpy as np
from collections import Counter

def read_tsv(fn):
    r = []
    with open(fn) as tsv:
        reader = csv.reader(tsv, delimiter='\t')
        for row in reader:
            r.append(row)
    return r[1:]

def get_tag_list(option):
    if option == 'top50tags':
        tag_list = np.load('tag_list_50.npy')
    else:
        tag_list = np.load('tag_list.npy')
        if option == 'genre':
            tag_list = tag_list[:87]
        elif option == 'instrument':
            tag_list = tag_list[87:127]
        elif option == 'moodtheme':
            tag_list = tag_list[127:]
    return list(tag_list)

def get_npy_array(path, tag_list, option, type_='train'):
    if option=='all':
        tsv_fn = os.path.join(path, 'autotagging-%s.tsv'%type_)
    else:
        tsv_fn = os.path.join(path, 'autotagging_%s-%s.tsv'%(option, type_))
    rows = read_tsv(tsv_fn)
    dictionary = {}
    i = 0
    for row in rows:
        temp_dict = {}
        temp_dict['path'] = row[3]
        temp_dict['duration'] = (float(row[4]) * 16000 - 512) // 256
        if option == 'all':
            temp_dict['tags'] = np.zeros(183)
        elif option == 'genre':
            temp_dict['tags'] = np.zeros(87)
        elif option == 'instrument':
            temp_dict['tags'] = np.zeros(40)
        elif option == 'moodtheme':
            temp_dict['tags'] = np.zeros(56)
        elif option == 'top50tags':
            temp_dict['tags'] = np.zeros(50)
        tags = row[5:]
        for tag in tags:
            try:
                temp_dict['tags'][tag_list.index(tag)] = 1
            except:
                continue
        if temp_dict['tags'].sum() > 0:
            dictionary[i] = temp_dict
            i += 1
    dict_fn = os.path.join(path, '%s_%s_dict.pickle'%(option, type_))
    with open(dict_fn, 'wb') as pf:
        pickle.dump(dictionary, pf)

def run_iter(split, option='all'):
    tag_list = get_tag_list(option)
    path = '../../data/splits/split-%d/' % split
    get_npy_array(path, tag_list, option, type_='train')
    get_npy_array(path, tag_list, option, type_='validation')
    get_npy_array(path, tag_list, option, type_='test')

def run():
    for i in range(5):
        run_iter(i, 'all')
        run_iter(i, 'genre')
        run_iter(i, 'instrument')
        run_iter(i, 'moodtheme')
        run_iter(i, 'top50tags')
