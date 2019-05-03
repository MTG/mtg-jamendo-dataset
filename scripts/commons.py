import csv

CATEGORIES = ['genre', 'mood/theme', 'instrument']


def get_id(value):
    return int(value.split('_')[1])


def read_file(tsv_file):
    """
    Processes input annotations file into easy to use Python dictionaries
    :param str tsv_file: name of input file
    :return: Tuple of tracks {track_id: {track_data}}, tags {'genre': {'rock': tracks}} and extras that should be passed to
    write_file()
    """
    tracks = {}  # maps track_id to all track data
    tags = {category: {} for category in CATEGORIES}  # contains sets of track_ids for each tag

    artist_ids = set()
    albums_ids = set()

    with open(tsv_file) as fp:
        reader = csv.DictReader(fp, delimiter='\t', restkey='TAGS')
        for row in reader:
            track_id = get_id(row['TRACK_ID'])
            tracks[track_id] = {
                'artist_id': get_id(row['ARTIST_ID']),
                'album_id': get_id(row['ALBUM_ID']),
                'path': row['PATH'],
                'duration': float(row['DURATION']),
                'tags': [row['TAGS']] if type(row['TAGS']) is str else row['TAGS'],  # raw tags
            }

            tracks[track_id].update({category: set() for category in CATEGORIES})  # add tag categories

            artist_ids.add(tracks[track_id]['artist_id'])
            albums_ids.add(tracks[track_id]['album_id'])

            for tag_str in row['TAGS']:  # process raw tags into categories
                category, tag = tag_str.split('---')  # raw tags look like 'genre---rock'
                tracks[track_id][category].add(tag)

                # overall mapping of tags to track_ids
                if tag not in tags[category]:
                    tags[category][tag] = set()  # encounter new tag
                tags[category][tag].add(track_id)

    # data for formatting the output file
    extra = {
        'track_id_length': get_length(tracks.keys()),
        'artist_id_length': get_length(artist_ids),
        'album_id_length': get_length(albums_ids)
    }
    return tracks, tags, extra


def get_length(values):
    """
    Computes length in digits of maximum value in a collection of numbers
    :param values: collection
    :return: length in digits
    """
    return len(str(max(values)))


def write_file(tracks, tsv_file, extra):
    """
    Writes the track annotations to tsv file
    :param tracks: dictionary {track_id: {track_data}}
    :param str tsv_file: name of output file
    :param extra: third return value of of read_file()
    """
    rows = []
    for track_id, track in tracks.items():
        row = [
            'track_' + str(track_id).zfill(extra['track_id_length']),
            'artist_' + str(track['artist_id']).zfill(extra['artist_id_length']),
            'album_' + str(track['album_id']).zfill(extra['album_id_length']),
            track['path'],
            track['duration']
        ]

        for category in CATEGORIES:
            row += [category + '---' + tag for tag in track[category]]

        rows.append(row)

    with open(tsv_file, 'w') as fp:
        writer = csv.writer(fp, delimiter='\t')
        writer.writerow(['TRACK_ID', 'ARTIST_ID', 'ALBUM_ID', 'PATH', 'DURATION', 'TAGS'])
        writer.writerows(rows)
