import argparse

import numpy as np
import pandas as pd

import commons


def generate_matrix(test_file, tags_file, output_file=None):
    tracks, tags, extra = commons.read_file(test_file)

    tags_data = pd.read_csv(tags_file, delimiter='\t', header=None)
    tag_map = {}
    for index, tag_str in enumerate(tags_data[0]):
        category, tag = tag_str.split(commons.TAG_HYPHEN)
        if category not in tag_map:
            tag_map[category] = {}
        tag_map[category][tag] = index

    print(tag_map)

    data = np.zeros([len(tracks), len(tags_data[0])], dtype=bool)
    for i, track in enumerate(tracks.values()):
        for category in commons.CATEGORIES:
            for tag in track[category]:
                data[i][tag_map[category][tag]] = True

    if output_file is not None:
        np.save(output_file, data)

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates matrix (tracks x tags) for a given file')
    parser.add_argument('test_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('tags_file', help='file with tag order that will be used')
    parser.add_argument('output_file', help='output NPY file ')
    args = parser.parse_args()

    generate_matrix(args.test_file, args.tags_file, args.output_file)
