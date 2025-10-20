import argparse
import csv
import hashlib
import os.path
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import requests
from tqdm import tqdm

base_path = Path(__file__).parent
ID_FILE_PATH = (base_path / "../../data/download/").resolve()

CHUNK_SIZE = 512 * 1024  # 512KB


def compute_sha256(filename):
    with open(filename, 'rb') as f:
        contents = f.read()
        checksum = hashlib.sha256(contents).hexdigest()
        return checksum


def download_from_mtg(url, output):
    output_path = Path(output)

    print('Downloading...', file=sys.stderr)
    print('From:', url, file=sys.stderr)
    print('To:', output_path, file=sys.stderr)

    res = requests.get(url, stream=True)

    try:
        total = res.headers.get('Content-Length')
        if total is not None:
            total = int(total)
        with tempfile.NamedTemporaryFile(
            prefix=output_path.name,
            dir=output_path.parent,
            delete=False,
        ) as tmp_file_d:
            tmp_file = tmp_file_d.name
            with tqdm(total=total, unit='B', unit_scale=True) as progressbar:
                for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
                    tmp_file_d.write(chunk)
                    progressbar.update(len(chunk))
        shutil.move(tmp_file_d.name, output)
    finally:
        try:
            os.remove(tmp_file)
        except OSError:
            pass

    return output


def download(dataset, data_type, output_dir, unpack_tars, remove_tars):
    if not os.path.exists(output_dir):
        print('Output directory {} does not exist'.format(output_dir), file=sys.stderr)
        return

    print('Downloading %s from MTG Fast mirror' % (dataset, ))
    file_gids = os.path.join(ID_FILE_PATH, dataset + '_' + data_type + '_gids.txt')
    file_sha256_tars = os.path.join(ID_FILE_PATH, dataset + '_' + data_type + '_sha256_tars.txt')
    file_sha256_tracks = os.path.join(ID_FILE_PATH, dataset + '_' + data_type + '_sha256_tracks.txt')

    # Read checksum values for tars and files inside.
    with open(file_sha256_tars) as f:
        sha256_tars = dict([(row[1], row[0]) for row in csv.reader(f, delimiter=' ')])

    with open(file_sha256_tracks) as f:
        sha256_tracks = dict([(row[1], row[0]) for row in csv.reader(f, delimiter=' ')])

    # Filenames to download.
    ids = sha256_tars.keys()

    removed = []
    for filename in ids:
        output = os.path.join(output_dir, filename)

        # Download from Google Drive.
        if os.path.exists(output):
            print('Skipping %s (file already exists)' % output)
            continue

        url = 'https://cdn.freesound.org/mtg-jamendo/' \
              '%s/%s/%s' % (dataset, data_type, filename)
        download_from_mtg(url, output)

        # Validate the checksum.
        if compute_sha256(output) != sha256_tars[filename]:
            print('%s does not match the checksum, removing the file' % output, file=sys.stderr)
            removed.append(filename)
            os.remove(output)
        else:
            print('%s checksum OK' % filename)

    if removed:
        print('Missing files:', ' '.join(removed))
        print('Re-run the script again')
        return

    print('Download complete')

    if unpack_tars:
        print('Unpacking tar archives')

        tracks_checked = []
        for filename in ids:
            output = os.path.join(output_dir, filename)
            print('Unpacking', output)
            tar = tarfile.open(output)
            tracks = tar.getnames()[1:]  # The first element is folder name.
            tar.extractall(path=output_dir)
            tar.close()

            # Validate checksums for all unpacked files
            for track in tracks:
                trackname = os.path.join(output_dir, track)
                if compute_sha256(trackname) != sha256_tracks[track]:
                    print('%s does not match the checksum' % trackname, file=sys.stderr)
                    raise Exception('Corrupt file in the dataset: %s' % trackname)

            print('%s track checksums OK' % filename)
            tracks_checked += tracks

            if remove_tars:
                os.remove(output)

        # Check if any tracks are missing in the unpacked archives.
        if set(tracks_checked) != set(sha256_tracks.keys()):
            raise Exception('Unpacked data contains tracks not present in the checksum files')

        print('Unpacking complete')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download the MTG-Jamendo dataset',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('--dataset', default='raw_30s', choices=['raw_30s', 'autotagging_moodtheme'],
                        help='dataset to download')
    parser.add_argument('--type', default='audio', choices=['audio', 'audio-low', 'melspecs', 'acousticbrainz'],
                        help='type of data to download (audio, audio in low quality, mel-spectrograms, AcousticBrainz features)')
    parser.add_argument('outputdir', help='directory to store the dataset')
    parser.add_argument('--unpack', action='store_true', help='unpack tar archives')
    parser.add_argument('--remove', action='store_true', help='remove tar archives while unpacking one by one (use to save disk space)')

    args = parser.parse_args()
    download(args.dataset, args.type, args.outputdir, args.unpack, args.remove)
