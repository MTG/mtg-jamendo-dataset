import argparse

import pandas as pd

import commons


def read_tags_file(tsv_file):
    data = pd.read_csv(tsv_file, delimiter='\t', header=None)
    tags = {category: set() for category in commons.CATEGORIES}

    for tag_str in data[0]:
        category, tag = tag_str.split(commons.TAG_HYPHEN)
        tags[category].add(tag)

    return tags


def filter_subset(tracks, tags_subset):
    tracks_to_delete = []
    for track_id, track in tracks.items():
        total_tags = 0
        for category, tags_new in tags_subset.items():
            track[category] &= tags_new
            total_tags += len(track[category])
        if total_tags == 0:
            tracks_to_delete.append(track_id)

    for track in tracks_to_delete:
        tracks.pop(track)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filters out tags according to tag list and removes tracks with no '
                                                 'tags left')
    parser.add_argument('tsv_file', help='TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, '
                                         'TAGS')
    parser.add_argument('tags_file', help='file with list of tag subset')
    parser.add_argument('output_file', help='output tsv file')

    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    tags_subset = read_tags_file(args.tags_file)
    filter_subset(tracks, tags_subset)
    commons.write_file(tracks, args.output_file, extra)
