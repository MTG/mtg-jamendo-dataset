import argparse
import random

import commons


def filter_toy(tracks: dict) -> dict:
    tracks_toy = {}
    artist_ids = set()
    for track_id, track in tracks.items():
        if track['artist_id'] not in artist_ids:
            tracks_toy[track_id] = track
            artist_ids.add(track['artist_id'])

    return tracks_toy


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Selects one track per artist')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('output_file', help='output tsv file')
    parser.add_argument('--seed', type=int, default=0, help='randomization seed')

    args = parser.parse_args()
    random.seed(args.seed)

    tracks, tags, extra = commons.read_file(args.tsv_file)
    tracks = filter_toy(tracks)
    commons.write_file(tracks, args.output_file, extra)
