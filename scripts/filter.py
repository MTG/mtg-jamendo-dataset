import argparse
import commons
import statistics
import util


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

    tracks_to_delete = []
    for track_id, track in tracks.items():
        total_tags = 0
        for category, tags_new in tags_new_all.items():
            track[category] &= tags_new
            total_tags += len(track[category])
        if total_tags == 0:
            tracks_to_delete.append(track_id)

    for track in tracks_to_delete:
        tracks.pop(track)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filters out tags with low number of unique artists')
    parser.add_argument('tsv_file', help='TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, '
                                         'TAGS')
    parser.add_argument('artist_threshold', type=int, help='Threshold number of artists')
    parser.add_argument('output_file', help='Output tsv file')
    parser.add_argument('--stats-directory', default=None,
                        help='If this argument is set, statistics will be recomputed and written to this directory')
    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    filter_tags(tracks, tags, args.artist_threshold, args.stats_directory)
    commons.write_file(tracks, args.output_file, extra)
