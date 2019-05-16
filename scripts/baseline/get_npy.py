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

def get_tag_list(path):
    rows = read_tsv(os.path.join(path, 'base_filtered_by_artists-train.tsv'))
    t = []
    for row in rows:
        tags = row[5:]
        for tag in tags:
            t.append(tag)
    if path[:3] == 'top':
        t_counter = Counter(t)
        t_sort = t_counter.most_common()[:50]
        t = [line[0] for line in t_sort]
    t = list(set(t))
    t.sort()
    if path[:3] == 'all':
        return t
    elif path[:3] == 'gen':
        return t[:87]
    elif path[:3] == 'ins':
        return t[87:127]
    elif path[:3] == 'moo':
        return t[127:]
    elif path[:3] == 'top':
        return t

def get_npy_array(path, tag_list, type_='train'):
    tsv_fn = os.path.join(path, 'base_filtered_by_artists-'+type_+'.tsv')
    rows = read_tsv(tsv_fn)
    dictionary = {}
    i = 0
    for row in rows:
        temp_dict = {}
        temp_dict['path'] = row[3]
        temp_dict['duration'] = (float(row[4]) * 16000 - 512) // 256
        if path[:3] == 'all':
            temp_dict['tags'] = np.zeros(183)
        elif path[:3] == 'gen':
            temp_dict['tags'] = np.zeros(87)
        elif path[:3] == 'ins':
            temp_dict['tags'] = np.zeros(40)
        elif path[:3] == 'moo':
            temp_dict['tags'] = np.zeros(56)
        elif path[:3] == 'top':
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
    dict_fn = os.path.join(path, type_+'dict.pickle')
    with open(dict_fn, 'wb') as pf:
        pickle.dump(dictionary, pf)

def run_iter(split, option='all'):
    path = os.path.join(option, 'split-' + str(split))
    tag_list = get_tag_list(path)
    np.save(open(os.path.join(path, 'tag_list.npy'), 'wb'), tag_list)
    get_npy_array(path, tag_list, type_='train')
    get_npy_array(path, tag_list, type_='validation')
    get_npy_array(path, tag_list, type_='test')

def run():
    for i in range(5):
        run_iter(i, 'all')
        run_iter(i, 'genre')
        run_iter(i, 'instrument')
        run_iter(i, 'mood')
        run_iter(i, 'top50')
