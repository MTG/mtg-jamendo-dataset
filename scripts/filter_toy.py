import argparse
import random

import commons
import statistics


def has_only_common_tags(track: dict, tags: dict) -> bool:
    for category, common_tags in tags.items():
        if not track[category].issubset(common_tags.keys()):
            return False
    return True


def filter_toy(tracks: dict, tags: dict, threshold: int):
    common_tags_all = {}
    for category, category_tags in tags.items():
        common_tags_all[category] = {}
        for tag, tag_tracks in category_tags.items():
            if len(tag_tracks) > threshold:
                common_tags_all[category][tag] = list(tag_tracks)

    track_ids_to_remove = set()
    for category, common_tags in common_tags_all.items():
        for tag, track_ids in common_tags.items():
            random.shuffle(track_ids)
            for track_id in track_ids:
                if has_only_common_tags(tracks[track_id], common_tags_all):
                    track_ids_to_remove.add(track_id)

    for track_id in track_ids_to_remove:
        tracks.pop(track_id)

    return tracks


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Generates toy subset by selecting one track per artist')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('output_file', help='output tsv file')
    parser.add_argument('--seed', type=int, default=0, help='randomization seed')
    parser.add_argument('--threshold', type=int, default=200, help='number of tracks per tag that define tags to prune')
    parser.add_argument('--stats-directory', default=None,
                        help='if this argument is set, statistics will be recomputed and written to this directory')

    args = parser.parse_args()
    random.seed(args.seed)

    tracks, tags, extra = commons.read_file(args.tsv_file)
    tracks_filtered = filter_toy(tracks, tags, args.threshold)
    commons.write_file(tracks_filtered, args.output_file, extra)

    if args.stats_directory is not None:
        _, tags_filtered, _ = commons.read_file(args.output_file)
        statistics.compute_statistics(tracks_filtered, tags_filtered, args.stats_directory, sort_by='tracks')
