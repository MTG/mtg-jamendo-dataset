import argparse
from pathlib import Path

import commons
from filter_subset import filter_subset, read_tags_file
from filter_category import filter_category

PARTS = ['train', 'test', 'validation']

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Filters out tags according to the subset and removes tracks with no '
                                                 'tags left')
    parser.add_argument('directory', help='location of root splits directory (that contains split-0, split-1, etc.)')
    parser.add_argument('input_prefix', help='filename prefix of splits for input (e.g. for autotagging-test.tsv the '
                                             'prefix is autotagging)')
    parser.add_argument('output_prefix', help='filename prefix of splits for output')
    parser.add_argument('--subset-file', default=None, help='file with list of tags subset')
    parser.add_argument('--category', default=None, choices=commons.CATEGORIES + [None],
                        help='file with list of tags subset')
    parser.add_argument('--sort', default=False, action='store_true',
                        help='sorts tracks according to track_id')

    args = parser.parse_args()

    tags_subset = None
    if args.subset_file is not None:
        tags_subset = read_tags_file(args.subset_file)

    split_dirs = [split_dir for split_dir in Path(args.directory).iterdir() if split_dir.is_dir()]
    for split_dir in split_dirs:
        for part in PARTS:
            input_file = split_dir / (args.input_prefix + '-' + part + '.tsv')
            output_file = split_dir / (args.output_prefix + '-' + part + '.tsv')

            tracks, tags, extra = commons.read_file(input_file)

            if tags_subset is not None:
                filter_subset(tracks, tags_subset)

            if args.category is not None:
                tracks = filter_category(tracks, tags, args.category)

            if args.sort:
                tracks = {track_id: tracks[track_id] for track_id in sorted(tracks)}

            commons.write_file(tracks, output_file, extra)
