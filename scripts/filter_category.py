import argparse

import commons


def filter_category(tracks, tags, category):
    track_id_sets = [tag_track_ids for tag_track_ids in tags[category].values()]
    track_ids = set().union(*track_id_sets)
    tracks_new = {track_id: track for track_id, track in tracks.items() if track_id in track_ids}
    for track in tracks_new.values():
        for other_category in set(commons.CATEGORIES) - {category}:
            track[other_category] = set()
    return tracks_new


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Creates subset of the full dataset')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('category', choices=commons.CATEGORIES, help='Category to extract')
    parser.add_argument('output_file', help='Output tsv file')
    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    tracks_filtered = filter_category(tracks, tags, args.category)
    commons.write_file(tracks_filtered, args.output_file, extra)
