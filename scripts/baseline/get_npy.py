import os
import csv
import pickle
import numpy as np
import fire
from collections import Counter

class Split:
    def read_tsv(self, fn):
        r = []
        with open(fn) as tsv:
            reader = csv.reader(tsv, delimiter='\t')
            for row in reader:
                r.append(row)
        return r[1:]

    def get_tag_list(self, option):
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

    def get_npy_array(self, path, tag_list, option, type_='train'):
        if option=='all':
            tsv_fn = os.path.join(path, 'autotagging-%s.tsv'%type_)
        else:
            tsv_fn = os.path.join(path, 'autotagging_%s-%s.tsv'%(option, type_))
        rows = self.read_tsv(tsv_fn)
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
            if temp_dict['tags'].sum() > 0 and os.path.exists(os.path.join(self.npy_path, row[3][:-3])+'npy'):
                dictionary[i] = temp_dict
                i += 1
        dict_fn = os.path.join(path, '%s_%s_dict.pickle'%(option, type_))
        with open(dict_fn, 'wb') as pf:
            pickle.dump(dictionary, pf)

    def run_iter(self, split, option='all'):
        tag_list = self.get_tag_list(option)
        path = '../../data/splits/split-%d/' % split
        self.get_npy_array(path, tag_list, option, type_='train')
        self.get_npy_array(path, tag_list, option, type_='validation')
        self.get_npy_array(path, tag_list, option, type_='test')

    def run(self, path):
        self.npy_path = path
        for i in range(5):
            self.run_iter(i, 'all')
            self.run_iter(i, 'genre')
            self.run_iter(i, 'instrument')
            self.run_iter(i, 'moodtheme')
            self.run_iter(i, 'top50tags')


if __name__ == '__main__':
    s = Split()
    fire.Fire({'run': s.run})
