import pandas as pd
import argparse
import csv


def read_file(tsv_file):
    tracks = {}
    with open(tsv_file, ) as fp:
        reader = csv.reader(fp, delimiter='\t')
        next(reader, None) # skip header
        for row in reader:
            pass


def compute_statistics():
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Computes data statistics, such as number of unique tracks, albums '
                                                 'and artists per tag')
    parser.add_argument('tsv_file', help='TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, '
                                         'TAGS')
    args = parser.parse_args()

    read_file(args.tsv_file)
    compute_statistics()
