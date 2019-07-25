import csv

CATEGORIES = ['genre', 'instrument', 'mood/theme']
TAG_HYPHEN = '---'
METADATA_DESCRIPTION = 'TSV file with such columns: TRACK_ID, ARTIST_ID, ALBUM_ID, PATH, DURATION, TAGS'


def get_id(value):
    return int(value.split('_')[1])


def get_length(values):
    return len(str(max(values)))


def read_file(tsv_file):
    tracks = {}
    tags = {category: {} for category in CATEGORIES}

    # For statistics
    artist_ids = set()
    albums_ids = set()

    with open(tsv_file) as fp:
        reader = csv.reader(fp, delimiter='\t')
        next(reader, None)  # skip header
        for row in reader:
            track_id = get_id(row[0])
            tracks[track_id] = {
                'artist_id': get_id(row[1]),
                'album_id': get_id(row[2]),
                'path': row[3],
                'duration': float(row[4]),
                'tags': row[5:],  # raw tags, not sure if will be used
            }
            tracks[track_id].update({category: set() for category in CATEGORIES})

            artist_ids.add(get_id(row[1]))
            albums_ids.add(get_id(row[2]))

            for tag_str in row[5:]:
                category, tag = tag_str.split(TAG_HYPHEN)

                if tag not in tags[category]:
                    tags[category][tag] = set()

                tags[category][tag].add(track_id)

                tracks[track_id][category].add(tag)

    print("Reading: {} tracks, {} albums, {} artists".format(len(tracks), len(albums_ids), len(artist_ids)))

    extra = {
        'track_id_length': get_length(tracks.keys()),
        'artist_id_length': get_length(artist_ids),
        'album_id_length': get_length(albums_ids)
    }
    return tracks, tags, extra


def write_file(tracks, tsv_file, extra):
    rows = []
    for track_id, track in tracks.items():
        row = [
            'track_' + str(track_id).zfill(extra['track_id_length']),
            'artist_' + str(track['artist_id']).zfill(extra['artist_id_length']),
            'album_' + str(track['album_id']).zfill(extra['album_id_length']),
            track['path'],
            track['duration']
        ]

        tags = []
        for category in CATEGORIES:
            tags += [category + '---' + tag for tag in track[category]]

        row += sorted(tags)
        rows.append(row)

    with open(tsv_file, 'w') as fp:
        writer = csv.writer(fp, delimiter='\t')
        writer.writerow(['TRACK_ID', 'ARTIST_ID', 'ALBUM_ID', 'PATH', 'DURATION', 'TAGS'])
        for row in rows:
            writer.writerow(row)
