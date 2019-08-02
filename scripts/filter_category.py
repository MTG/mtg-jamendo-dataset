import argparse

import pandas as pd

import commons


def filter_category(tracks, tags, category, tag_file=None):
    if tag_file is not None:
        tag_list = [category + commons.TAG_HYPHEN + tag for tag in tags[category].keys()]
        tag_list = pd.DataFrame(tag_list, columns=['tag'])
        tag_list = tag_list.sort_values(by='tag')
        tag_list.to_csv(tag_file, sep='\t', index=False, header=False)

    track_id_sets = [tag_track_ids for tag_track_ids in tags[category].values()]
    track_ids = set().union(*track_id_sets)
    tracks_new = {track_id: track for track_id, track in tracks.items() if track_id in track_ids}
    for track in tracks_new.values():
        for other_category in set(commons.CATEGORIES) - {category}:
            track[other_category] = set()
    return tracks_new


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='creates subset of the full dataset')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('category', choices=commons.CATEGORIES, help='category to extract')
    parser.add_argument('output_file', help='output tsv file')
    parser.add_argument('--tag-list', default=None, help='text file with subset tags')

    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    tracks_filtered = filter_category(tracks, tags, args.category, args.tag_list)
    commons.write_file(tracks_filtered, args.output_file, extra)

