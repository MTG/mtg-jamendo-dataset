import argparse
import csv
import pandas as pd
import os


def get_id(value):
    return int(value.split('_')[1])


def read_file(tsv_file):
    tracks = {}
    tags = {
        'genre': {},
        'mood/theme': {},
        'instrument': {}
    }

    with open(tsv_file) as fp:
        reader = csv.reader(fp, delimiter='\t')
        next(reader, None)  # skip header
        for row in reader:
            tracks[get_id(row[0])] = {
                'artist_id': get_id(row[1]),
                'album_id': get_id(row[2]),
                'path': row[3],
                'duration': float(row[4]),

                'tags': row[5:],
                'genre': [],
                'mood/theme': [],
                'instrument': []
            }

            for tag_str in row[5:]:
                category, tag = tag_str.split('---')

                if tag not in tags[category]:
                    tags[category][tag] = set()

                tags[category][tag].add(get_id(row[0]))

    return tracks, tags


def compute_statistics(tracks, tags, directory):
    try:
        os.mkdir(directory)
    except FileExistsError:
        print('Warning: statistics directory already exists, files will be overwritten')

    for category in tags:
        data = []
        for tag, tag_tracks in tags[category].items():
            row = [tag]

            for collection in ['artist', 'album']:
                collection_ids = {tracks[track_id][collection + "_id"] for track_id in tag_tracks}
                row.append(len(collection_ids))

            row.append(len(tag_tracks))
            data.append(row)

        data = pd.DataFrame(data, columns=['tag', 'artists', 'albums', 'tracks'])
        data = data.sort_values(by=['artists'], ascending=False)
        data = data.reset_index(drop=True)
        data.to_csv(os.path.join(directory, category.replace('/', '_') + '.tsv'), sep='\t', index=False)
        print('Total tags for {}: {}'.format(category, len(data)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Computes data statistics, such as number of unique tracks, albums '
                                                 'and artists per tag')
    parser.add_argument('tsv_file', help='TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, '
                                         'TAGS')
    parser.add_argument('directory', help='Directory for computed statistics')
    args = parser.parse_args()

    tracks, tags = read_file(args.tsv_file)
    compute_statistics(tracks, tags, args.directory)
