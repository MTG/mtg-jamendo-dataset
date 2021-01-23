import argparse
import sys
import os.path
import csv
import hashlib
import tarfile
from pathlib import Path
import gdown
import wget


base_path = Path(__file__).parent
ID_FILE_PATH = (base_path / "../../data/download/").resolve()

download_from_names = {'gdrive': 'GDrive', 'mtg': 'MTG'}


def compute_sha256(filename):
    with open(filename, 'rb') as f:
        contents = f.read()
        checksum = hashlib.sha256(contents).hexdigest()
        return checksum
    return None
    
    raise Exception('Error computing a checksum for %s' % filename)


def download(dataset, data_type, download_from, output_dir, unpack_tars, remove_tars):
    if not os.path.exists(output_dir):
        sys.stderr.write('Output directory %s does not exist' % output_dir)
        return

    print('Downloading %s from %s' % (dataset, download_from_names[download_from]))
    file_gids = os.path.join(ID_FILE_PATH, dataset + '_' + data_type + '_gids.txt')
    file_sha256_tars = os.path.join(ID_FILE_PATH, dataset + '_' + data_type + '_sha256_tars.txt')
    file_sha256_tracks = os.path.join(ID_FILE_PATH, dataset + '_' + data_type + '_sha256_tracks.txt')

    # Read checksum values for tars and files inside.
    with open(file_sha256_tars) as f:
        sha256_tars = dict([(row[1], row[0]) for row in csv.reader(f, delimiter=' ')])

    with open(file_sha256_tracks) as f:
        sha256_tracks = dict([(row[1], row[0]) for row in csv.reader(f, delimiter=' ')])

    # Read filenames and google IDs to download.
    ids = {}
    with open(file_gids, 'r') as f:
        for line in f:
            id, filename = line.split(('   '))[:2]
            ids[filename] = id

    removed = []
    for filename in ids:
        output = os.path.join(output_dir, filename)

        # Download from Google Drive.
        if os.path.exists(output):
            print('Skipping %s (file already exists)' % output)
            continue

        if download_from == 'gdrive':
            url = 'https://drive.google.com/uc?id=%s' % ids[filename]
            gdown.download(url, output, quiet=False)

        elif download_from == 'mtg':
            url = 'https://essentia.upf.edu/documentation/datasets/mtg-jamendo/' \
                  '%s/%s/%s' % (dataset, data_type, filename)
            print('From:', url)
            print('To:', output)
            wget.download (url, out=output)

        # Validate the checksum.
        if compute_sha256(output) != sha256_tars[filename]:
            sys.stderr.write('%s does not match the checksum, removing the file' % output)
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
                    sys.stderr.write('%s does not match the checksum' % trackname)
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
    parser.add_argument('--type', default='audio', choices=['audio', 'melspecs', 'acousticbrainz'],
                        help='type of data to download (audio, mel-spectrograms, AcousticBrainz features)')
    parser.add_argument('--from', default='gdrive', choices=['gdrive', 'mtg'],
                        dest='download_from',
                        help='download from Google Drive (fast everywhere) or MTG (server in Spain, slow)')
    parser.add_argument('outputdir', help='directory to store the dataset')
    parser.add_argument('--unpack', action='store_true', help='unpack tar archives')
    parser.add_argument('--remove', action='store_true', help='remove tar archives while unpacking one by one (use to save disk space)')

    args = parser.parse_args()
    download(args.dataset, args.type, args.download_from, args.outputdir, args.unpack, args.remove)
