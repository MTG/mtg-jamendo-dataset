import argparse

import commons
import statistics
import util
from filter_subset import filter_subset


def filter_tags(tracks, tags, artist_threshold, directory=None):
    if directory is not None:
        util.mkdir_p(directory)

    tags_new_all = {}
    for category in tags:
        stats, total = statistics.get_statistics(category, tracks, tags)
        stats_filtered = stats[stats['artists'] >= artist_threshold]
        if directory is not None:
            statistics.write_statistics(category, stats_filtered, directory)

        tags_new_all[category] = set(stats_filtered['tag'])
        print("- {} tags: {} -> {}".format(category, len(stats), len(stats_filtered)))

    filter_subset(tracks, tags_new_all)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filters out tags with low number of unique artists')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('artist_threshold', type=int, help='threshold number of artists')
    parser.add_argument('output_file', help='output tsv file')
    parser.add_argument('--stats-directory', default=None,
                        help='if this argument is set, statistics will be recomputed and written to this directory')
    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    filter_tags(tracks, tags, args.artist_threshold, args.stats_directory)
    commons.write_file(tracks, args.output_file, extra)
