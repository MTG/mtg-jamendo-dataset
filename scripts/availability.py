"""Requires Python 3.9"""
import argparse
from pathlib import Path
from time import sleep
from typing import Optional

import pandas as pd
import requests
from tqdm import tqdm


def get_url(track_id: int) -> str:
    return f'https://mp3d.jamendo.com/?trackid={track_id}&format=mp32'


def check_availability(input_file: Path, delay: int, skip: Optional[int]) -> None:
    df = pd.read_csv(input_file, sep='\t', usecols=[0])
    track_ids = [int(row.removeprefix('track_')) for row in df['TRACK_ID']]
    if skip is not None:
        track_ids = track_ids[skip:]
    else:
        skip = 0
    not_available_list = []

    try:
        for track_id in (pbar := tqdm(track_ids, desc='N/A: 0 streams', initial=skip, total=len(track_ids) + skip)):
            r = requests.get(get_url(track_id))
            available = (r.status_code == 200 and
                         'audio' in r.headers['Content-Type'] and
                         int(r.headers['Content-Length']) > 4000)
            if not available:
                not_available_list.append(track_id)
                pbar.desc = f'N/A: {len(not_available_list)} streams'
            sleep(delay)
    finally:
        print(f'N/A: {not_available_list}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('input_file', type=Path, help='input .tsv file')
    # parser.add_argument('output_file', type=Path, help='output file')
    parser.add_argument('--delay', type=int, default=5, help='delay in seconds between requests')
    parser.add_argument('--skip', type=int, help='skip this number of tracks')
    args = parser.parse_args()

    check_availability(args.input_file, args.delay, args.skip)
