import argparse
import commons
import statistics
import util


def filter_tags(tracks, tags, tag_threshold, directory=None):
    if directory is not None:
        util.mkdir_p(directory)

    tags_merged = {}
    for category_tags in tags.values():
        tags_merged.update(category_tags)

    stats, total = statistics.get_statistics('all', tracks, {'all': tags_merged})
    stats = stats.sort_values(by='tracks', ascending=False)
    stats_filtered = stats[:tag_threshold]
    if directory is not None:
        statistics.write_statistics('all', stats_filtered, directory)

    tags_top = set(stats_filtered['tag'])

    tracks_to_delete = []
    for track_id, track in tracks.items():

        total_tags = 0
        for category in commons.CATEGORIES:
            track[category] &= tags_top
            total_tags += len(track[category])
        if total_tags == 0:
            tracks_to_delete.append(track_id)

    for track in tracks_to_delete:
        tracks.pop(track)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filters out less frequent tags')
    parser.add_argument('tsv_file', help='TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, '
                                         'TAGS')
    parser.add_argument('tag_threshold', type=int, help='Threshold number of tags')
    parser.add_argument('output_file', help='Output tsv file')
    parser.add_argument('--stats-directory', default=None,
                        help='If this argument is set, statistics will be recomputed and written to this directory')
    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    filter_tags(tracks, tags, args.tag_threshold, args.stats_directory)
    commons.write_file(tracks, args.output_file, extra)
