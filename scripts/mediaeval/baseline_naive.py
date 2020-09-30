import argparse

import pandas as pd
import numpy as np

import commons
from get_statistics import get_statistics


def predict_popular(train_tracks, train_tags, test_tracks, test_tags, tags_order):
    tags_popular = {}
    for category in commons.CATEGORIES:
        stats, _ = get_statistics(category, train_tracks, train_tags)
        if len(stats) > 0:
            # save top tag, number of tracks and category for it
            stats = stats.sort_values(by='tracks', ascending=False)
            stats = stats.reset_index(drop=True)
            tags_popular[stats['tag'][0]] = {'tracks': stats['tracks'][0], 'category': category}
    print(tags_popular)
    tag_popular = max(tags_popular.keys(), key=lambda key: tags_popular[key]['tracks'])
    full_tag = tags_popular[tag_popular]['category'] + commons.TAG_HYPHEN + tag_popular

    data = np.zeros([len(test_tracks), len(tags_order)], dtype=bool)
    tag_index = tags_order.index[tags_order[0] == full_tag]
    data[:, tag_index] = True
    return data


# super non-optimized, refactor due after tags rework
def predict_random(train_tracks, train_tags, test_tracks, test_tags, tags_order):
    n_tracks = len(train_tracks)
    tag_ratios = {}
    for category in commons.CATEGORIES:
        stats, _ = get_statistics(category, train_tracks, train_tags)
        if len(stats) > 0:
            for _, row in stats.iterrows():
                full_tag = category + commons.TAG_HYPHEN + row['tag']
                tag_ratios[full_tag] = row['tracks'] / n_tracks

    tag_vector = np.zeros(len(tags_order))
    for i, row in tags_order.iterrows():
        tag_vector[i] = tag_ratios[row[0]]

    data = np.tile(tag_vector, (len(test_tracks), 1))
    return data


ALGORITHMS = {
    'popular': predict_popular,
    'random': predict_random
}

DEFAULT_ALGORITHM = 'popular'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates predictions based on naive baseline algorithms')
    parser.add_argument('train_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('test_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('tags_file', help='file with tag order that will be used')
    parser.add_argument('output_file', help='output NPY file ')
    parser.add_argument('--algorithm', choices=ALGORITHMS.keys(), default=DEFAULT_ALGORITHM,
                        help='algorithm to use')
    args = parser.parse_args()

    func = ALGORITHMS[args.algorithm]
    train_tracks, train_tags, _ = commons.read_file(args.train_file)
    test_tracks, test_tags, _ = commons.read_file(args.test_file)
    tags_order = pd.read_csv(args.tags_file, delimiter='\t', header=None)

    data = ALGORITHMS[args.algorithm](train_tracks, train_tags, test_tracks, test_tags, tags_order)
    np.save(args.output_file, data)
