import argparse
import csv
import hashlib
import os
import os.path
import shutil
import sys
import tarfile
import time
from pathlib import Path

import gdown
import requests
from tqdm import tqdm

base_path = Path(__file__).parent
ID_FILE_PATH = (base_path / "../../data/download/").resolve()

download_from_names = {'gdrive': 'GDrive', 'mtg': 'MTG', 'mtg-fast': 'MTG Fast mirror'}

CHUNK_SIZE = 512 * 1024  # 512KB

# --- Download resilience settings ---
DEFAULT_MAX_RETRIES = 5       # Maximum retry attempts per file
DEFAULT_CONNECT_TIMEOUT = 30  # Connection timeout in seconds
DEFAULT_READ_TIMEOUT = 60     # Read timeout (max gap between chunks) in seconds
DEFAULT_RETRY_BACKOFF = 5     # Base backoff seconds (exponential: 5, 10, 20, ...)


def _format_size(num_bytes):
    """Format a byte count into a human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return '%.1f %s' % (num_bytes, unit)
        num_bytes /= 1024.0
    return '%.1f PB' % num_bytes


def compute_sha256(filename):
    """Compute SHA256 checksum using chunked reads (memory-efficient)."""
    sha256 = hashlib.sha256()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def download_from_mtg(url, output, max_retries=DEFAULT_MAX_RETRIES,
                     connect_timeout=DEFAULT_CONNECT_TIMEOUT,
                     read_timeout=DEFAULT_READ_TIMEOUT):
    """Download from MTG with timeout, resume, and retry.

    Uses a .part file + HTTP Range header so interrupted downloads can
    be resumed.  Retries with exponential backoff on network errors.
    Raises if all retries are exhausted (keeps .part for future resume).
    """
    output_path = Path(output)
    part_file = str(output_path) + '.part'

    print('Downloading...', file=sys.stderr)
    print('From:', url, file=sys.stderr)
    print('To:', output_path, file=sys.stderr)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            # Check for existing partial download to resume.
            resume_pos = 0
            if os.path.exists(part_file):
                resume_pos = os.path.getsize(part_file)
                if resume_pos > 0:
                    print('Found partial download: %s (%s), resuming...'
                          % (part_file, _format_size(resume_pos)), file=sys.stderr)

            headers = {}
            if resume_pos > 0:
                headers['Range'] = 'bytes=%d-' % resume_pos

            res = requests.get(url, stream=True, headers=headers,
                               timeout=(connect_timeout, read_timeout))
            try:
                # 416: part file >= remote size; clear and restart.
                if res.status_code == 416:
                    print('Server returned 416, restarting from scratch', file=sys.stderr)
                    if os.path.exists(part_file):
                        os.remove(part_file)
                    raise IOError('Range not satisfiable, part file cleared')

                res.raise_for_status()

                # 206 → append (resume); 200 → overwrite (fresh or no resume support).
                if resume_pos > 0 and res.status_code == 200:
                    print('Server does not support resume, starting from scratch',
                          file=sys.stderr)
                    resume_pos = 0
                    mode = 'wb'
                elif res.status_code == 206:
                    mode = 'ab'
                else:
                    mode = 'wb'

                content_length = res.headers.get('Content-Length')
                if content_length is not None:
                    full_total = int(content_length) + resume_pos
                else:
                    full_total = None

                with open(part_file, mode) as f:
                    with tqdm(total=full_total, initial=resume_pos,
                              unit='B', unit_scale=True) as progressbar:
                        for chunk in res.iter_content(chunk_size=CHUNK_SIZE):
                            f.write(chunk)
                            progressbar.update(len(chunk))
            finally:
                res.close()

            # Verify download is complete.
            got = os.path.getsize(part_file)
            if full_total is not None and got != full_total:
                raise IOError('Download incomplete: got %s, expected %s'
                              % (_format_size(got), _format_size(full_total)))

            # Success: move .part → final output.
            shutil.move(part_file, output)
            print('Download complete: %s' % output_path, file=sys.stderr)
            return output

        except (requests.exceptions.RequestException, IOError, OSError) as e:
            last_error = e
            cur = os.path.getsize(part_file) if os.path.exists(part_file) else 0
            print('Attempt %d/%d failed: %s (downloaded %s so far)'
                  % (attempt, max_retries, e, _format_size(cur)), file=sys.stderr)
            if attempt < max_retries:
                backoff = DEFAULT_RETRY_BACKOFF * (2 ** (attempt - 1))
                print('Retrying in %d seconds...' % backoff, file=sys.stderr)
                time.sleep(backoff)
            else:
                print('Max retries (%d) reached for %s'
                      % (max_retries, url), file=sys.stderr)

    # All retries exhausted; keep .part file for future resume.
    if os.path.exists(part_file):
        print('Keeping partial download %s for future resume' % part_file,
              file=sys.stderr)
    raise last_error


def download(dataset, data_type, download_from, output_dir, unpack_tars, remove_tars,
             max_retries=DEFAULT_MAX_RETRIES, connect_timeout=DEFAULT_CONNECT_TIMEOUT,
             read_timeout=DEFAULT_READ_TIMEOUT, skip_file=None):
    if not os.path.exists(output_dir):
        print('Output directory {} does not exist'.format(output_dir), file=sys.stderr)
        return

    if download_from not in download_from_names:
        print("Unknown --from argument, choices are {}".format(list(download_from_names.keys())), file=sys.stderr)
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

    # Filenames to download.
    ids = sha256_tars.keys()

    # Google IDs to download.
    if download_from == 'gdrive':
        gids = {}
        with open(file_gids, 'r') as f:
            for line in f:
                id, filename = line.split(('   '))[:2]
                gids[filename] = id

    # Read list of files to skip (already downloaded and moved elsewhere).
    skip_files = set()
    if skip_file:
        if not os.path.exists(skip_file):
            print('Skip file %s does not exist' % skip_file, file=sys.stderr)
            return
        with open(skip_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    skip_files.add(os.path.basename(line))
        print('Skipping %d files listed in %s' % (len(skip_files), skip_file))

    removed = []
    for filename in ids:
        output = os.path.join(output_dir, filename)
        part_file = output + '.part'

        # Skip if in the completed list or file already exists on disk.
        if filename in skip_files:
            print('Skipping %s (marked as completed in skip file)' % filename)
            continue
        if os.path.exists(output):
            print('Skipping %s (file already exists)' % output)
            continue

        if download_from == 'gdrive':
            url = 'https://drive.google.com/uc?id=%s' % gids[filename]
            gdown.download(url, output, quiet=False)
        else:
            # mtg or mtg-fast
            if download_from == 'mtg':
                url = 'https://essentia.upf.edu/documentation/datasets/mtg-jamendo/' \
                      '%s/%s/%s' % (dataset, data_type, filename)
            elif download_from == 'mtg-fast':
                url = 'https://cdn.freesound.org/mtg-jamendo/' \
                      '%s/%s/%s' % (dataset, data_type, filename)

            try:
                download_from_mtg(url, output, max_retries=max_retries,
                                  connect_timeout=connect_timeout,
                                  read_timeout=read_timeout)
            except Exception as e:
                print('Failed to download %s: %s' % (filename, e), file=sys.stderr)
                removed.append(filename)
                continue

        # Validate the checksum.
        if compute_sha256(output) != sha256_tars[filename]:
            print('%s does not match the checksum, removing the file' % output, file=sys.stderr)
            removed.append(filename)
            os.remove(output)
            # Also remove the .part file to prevent bad resume.
            if os.path.exists(part_file):
                os.remove(part_file)
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
            if filename in skip_files:
                print('Skipping %s (marked as completed in skip file)' % filename)
                continue
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

        # Check for unexpected or missing tracks.
        if skip_files:
            # Some files were skipped; only check for unexpected tracks.
            extra = set(tracks_checked) - set(sha256_tracks.keys())
            if extra:
                raise Exception('Unpacked data contains tracks not present in the checksum files')
            missing_count = len(set(sha256_tracks.keys()) - set(tracks_checked))
            if missing_count:
                print('Note: %d tracks not verified (belong to %d skipped files)'
                      % (missing_count, len(skip_files)), file=sys.stderr)
        else:
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
    parser.add_argument('--from', default='mtg-fast', choices=['mtg', 'mtg-fast'],
                        dest='download_from',
                        help='download from MTG (server in Spain, slow), '
                             'or fast MTG mirror (Finland)')
    #parser.add_argument('--from', default='mtg-fast', choices=['gdrive', 'mtg', 'mtg-fast'],
    #                    dest='download_from',
    #                    help='download from Google Drive (fast everywhere), MTG (server in Spain, slow), '
    #                         'or fast MTG mirror (Finland)')
    parser.add_argument('outputdir', help='directory to store the dataset')
    parser.add_argument('--unpack', action='store_true', help='unpack tar archives')
    parser.add_argument('--remove', action='store_true', help='remove tar archives while unpacking one by one (use to save disk space)')
    parser.add_argument('--retries', type=int, default=DEFAULT_MAX_RETRIES,
                        help='maximum number of download retry attempts per file')
    parser.add_argument('--connect-timeout', type=int, default=DEFAULT_CONNECT_TIMEOUT,
                        help='connection timeout in seconds')
    parser.add_argument('--read-timeout', type=int, default=DEFAULT_READ_TIMEOUT,
                        help='read timeout in seconds (max gap between data chunks)')
    parser.add_argument('--skip-file', dest='skip_file', default=None,
                        help='path to a text file listing already-completed tar files to '
                             'skip (one filename per line, # for comments)')

    args = parser.parse_args()
    download(args.dataset, args.type, args.download_from, args.outputdir, args.unpack, args.remove,
             max_retries=args.retries, connect_timeout=args.connect_timeout,
             read_timeout=args.read_timeout, skip_file=args.skip_file)
