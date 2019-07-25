import argparse
import random

import commons
import statistics


def generate_toy(tracks: dict) -> dict:
    tracks_toy = {}
    artist_ids = set()
    track_ids = list(tracks.keys())
    random.shuffle(track_ids)

    for track_id in track_ids:
        track = tracks[track_id]
        if track['artist_id'] not in artist_ids:
            tracks_toy[track_id] = track
            artist_ids.add(track['artist_id'])

    return tracks_toy


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates toy subset by selecting one track per artist')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('output_prefix', help='output tsv file')
    parser.add_argument('--seed', type=int, default=0, help='randomization seed')
    parser.add_argument('--n', type=int, default=1, help='number of subsets to generate')
    parser.add_argument('--stats-directory', default=None,
                        help='if this argument is set, statistics will be recomputed and written to this directory')

    args = parser.parse_args()
    random.seed(args.seed)

    tracks, tags, extra = commons.read_file(args.tsv_file)
    for i in range(args.n):
        print("Generating toy subset #{}".format(i))
        tracks_toy = generate_toy(tracks)
        filename = "{}_{}.tsv".format(args.output_prefix, i)
        commons.write_file(tracks_toy, filename, extra)

        if args.stats_directory is not None:
            _, tags_toy, _ = commons.read_file(filename)
            statistics.compute_statistics(tracks_toy, tags_toy, "{}_{}".format(args.stats_directory, i))
