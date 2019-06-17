import argparse
import commons
import statistics
import util


def filter_tags(tracks, tags, tag_threshold, directory=None, tags_file=None):
    if directory is not None:
        util.mkdir_p(directory)

    # TODO: refactor to properly handle and not disconnect category+tag
    tags_merged = {}
    tags_with_prefix = {}
    for category, category_tags in tags.items():
        tags_merged.update(category_tags)
        if tags_file is not None:
            tags_with_prefix.update({tag: category + commons.TAG_HYPHEN + tag for tag in category_tags})

    stats, total = statistics.get_statistics('all', tracks, {'all': tags_merged})
    stats = stats.sort_values(by='tracks', ascending=False)
    stats_filtered = stats[:tag_threshold]
    if directory is not None:
        statistics.write_statistics('all', stats_filtered, directory)

    if tags_file is not None:
        tag_list = stats_filtered['tag'].replace(tags_with_prefix).sort_values()
        tag_list.to_csv(tags_file, sep='\t', index=False, header=False)

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
    parser = argparse.ArgumentParser(description='Filters out less frequent tags according to the number of tracks')
    parser.add_argument('tsv_file', help='TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, '
                                         'TAGS')
    parser.add_argument('tag_threshold', type=int, help='threshold number of tags')
    parser.add_argument('output_file', help='output tsv file')
    parser.add_argument('--stats-directory', default=None,
                        help='if this argument is set, statistics will be recomputed and written to this directory')
    parser.add_argument('--tag-list', default=None, help='text file with filtered tags (top-n)')
    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    filter_tags(tracks, tags, args.tag_threshold, args.stats_directory, args.tag_list)
    commons.write_file(tracks, args.output_file, extra)
