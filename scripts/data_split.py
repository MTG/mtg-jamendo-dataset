import argparse
import csv
import collections
import random
import sys
import math
import logging
import os
import copy
import itertools

import util

log = logging.Logger('lookup')
ch = logging.StreamHandler()
#ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
ch.setFormatter(logging.Formatter('%(message)s'))
fh = logging.FileHandler("make_split.log")
#fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
fh.setFormatter(logging.Formatter('%(message)s'))

log.setLevel(logging.DEBUG)
log.addHandler(ch)
log.addHandler(fh)


TRAIN = "train"
TEST = "test"
VALIDATION = "validation"

config = {}


def _split_artists(artistids):
    random.shuffle(artistids)
    art_len = len(artistids)
    train_count = int(math.ceil(art_len * config['split_ratio'][TRAIN] / 100.))
    test_count = int(math.ceil(art_len * config['split_ratio'][TEST] / 100.))
    validation_count = int(math.ceil(art_len * config['split_ratio'][VALIDATION] / 100.))

    train_items = artistids[:train_count]
    test_items = artistids[train_count:train_count+test_count]
    validation_items = artistids[train_count+test_count:
                                 train_count+test_count+validation_count]
    log.debug("%s artists, %s train, %s test, %s validation", art_len, train_count, test_count, validation_count)

    splits = {}
    for i in train_items:
        splits[i] = TRAIN
    for i in test_items:
        splits[i] = TEST
    for i in validation_items:
        splits[i] = VALIDATION

    return splits


def _load_groundtruth(groundtruthfile):
    log.debug("Loading groundtruth")
    with open(groundtruthfile) as fp:
        r = csv.reader(fp, delimiter="\t")
        header = next(r)
        groundtruth = {}
        groundtruth_meta = {}
        track_to_artist = {}
        for l in r:
            track = l[0]
            artist = l[1]
            track_to_artist[track] = artist      
            # artistid, albumid, path, duration
            groundtruth_meta[track] = [l[1], l[2], l[3], l[4]]
            # tags
            groundtruth[track] = set(l[5:])
        
        artist_to_tracks = collections.defaultdict(list)
        for t, a in track_to_artist.items():
            artist_to_tracks[a].append(t)
    
    return groundtruth, groundtruth_meta, track_to_artist, artist_to_tracks, header


def _tags_by_category(tags):
    tags_genres = [k for k in tags if k.startswith("genre---")]
    tags_moods = [k for k in tags if k.startswith("mood/theme---")]
    tags_instruments = [k for k in tags if k.startswith("instrument---")]
    return tags_genres, tags_moods, tags_instruments


def run_trials(groundtruthfile):
    groundtruth, groundtruth_meta, track_to_artist, artist_to_tracks, header = _load_groundtruth(groundtruthfile)

    tag_to_tracks = collections.defaultdict(list)
    for trackid, tags in groundtruth.items():
        for t in tags:
            tag_to_tracks[t].append(trackid)

    artists = artist_to_tracks.keys()

    solutions = []
    total_tags = len(tag_to_tracks)

    for trialnumber in range(config['trials']):
        # Randomly split artists into sections
        log.debug("Trial %s", trialnumber)
        log.debug("Splitting by artists")
        artist_splits = _split_artists(list(artists))
        train, test, validation, discarded_tags = split_groundtruth(dict(groundtruth), track_to_artist, artist_to_tracks, tag_to_tracks, artist_splits, trialnumber)
        solutions.append((len(discarded_tags), discarded_tags, train, test, validation))

        # Only keep the best solutions (this saves memory load)
        solutions = sorted(solutions)
        if len(solutions) > config['splits']:
            best_discarded = solutions[config['splits']][0]
            solutions = [s for s in solutions if s[0] <= best_discarded]

    log.debug("")
    log.debug("-" * 10 + " Best trials " + "-" * 10)
    for s in solutions:
        log.debug("- Discarded %s out of %s tags: %s", s[0], total_tags, sorted(list(s[1])))

    # We want all subsets to have the same tags. Select the best set of splits
    # that minimized the amout of discarded tracks.
    selections = list(itertools.combinations(solutions, config['splits']))
    selections = [(set([t for s in selection for t in s[1]]), selection) for selection in selections]
    selections = [(len(tags), sorted(list(tags)), selection) for tags, selection in selections]
    _, discarded_tags, best_selection = sorted(selections)[0]

    log.debug("")
    log.debug("-" * 10 + " Best solution: " + "-" * 10)
    log.debug("Discarded %s tags: %s", len(discarded_tags), discarded_tags)

    for i in range(len(best_selection)):
        _, _, train, test, validation = best_selection[i]
        train = remove_tags_from_groundtruth(train, discarded_tags, tag_to_tracks)
        test = remove_tags_from_groundtruth(test, discarded_tags, tag_to_tracks)
        validation = remove_tags_from_groundtruth(validation, discarded_tags, tag_to_tracks)

        gt_dir = os.path.dirname(groundtruthfile)
        gt_file = os.path.basename(groundtruthfile)
        gt_name, gt_ext = os.path.splitext(gt_file)

        splitdir = "split-%s" % i
        util.mkdir_p(splitdir)

        for part, data in [("train", train), ("test", test), ("validation", validation)]:
            out_file = os.path.join(splitdir, "%s-%s%s" % (gt_name, part, gt_ext))
            log.debug("Writing part %s to file %s", part, out_file)
            with open(out_file, "w") as fp:
                w = csv.writer(fp, delimiter="\t")
                w.writerow(header)
                for trackid, tags in data.items():
                    row = [trackid] + groundtruth_meta[trackid] + list(tags)
                    w.writerow(row)


def discard_tags_by_count(tag_split_artists, tag_split_tracks):
    # Tags below the minimum artist count for train/test/validation
    discard_tags_artist = tag_split_artists
    for t in list(discard_tags_artist.keys()):
        if (len(discard_tags_artist[t][TRAIN]) >= config['artist_threshold'][TRAIN] and 
            len(discard_tags_artist[t][TEST]) >= config['artist_threshold'][TEST] and 
            len(discard_tags_artist[t][VALIDATION]) >= config['artist_threshold'][VALIDATION]):
            del discard_tags_artist[t]

    # Tags below the minimum track count for train/test/validation
    discard_tags_track = tag_split_tracks
    for t in list(discard_tags_track.keys()):
        if (len(discard_tags_track[t][TRAIN]) >= config['track_threshold'][TRAIN] and 
            len(discard_tags_track[t][TEST]) >= config['track_threshold'][TEST] and 
            len(discard_tags_track[t][VALIDATION]) >= config['track_threshold'][VALIDATION]):
            del discard_tags_track[t]

    log.debug("Tags with insufficient artist counts: %s", discard_tags_artist.keys())
    log.debug("Tags with insufficient track counts: %s", discard_tags_track.keys())

    tags_to_remove = set(list(discard_tags_artist.keys()) + list(discard_tags_track.keys()))
    return tags_to_remove


def split_groundtruth(groundtruth, track_to_artist, artist_to_tracks, tag_to_tracks, artist_splits, trialnumber):

    log.debug("Making mapping of tag counts")
        
    track_splits = {}
    for artist, group in artist_splits.items():
        for t in artist_to_tracks[artist]:
            track_splits[t] = group

    # Mapping from tags to tracks and artists
    tag_split_artists = collections.defaultdict(lambda: { TRAIN: set(), TEST: set(), VALIDATION: set() })
    tag_split_tracks = collections.defaultdict(lambda: { TRAIN: [], TEST: [], VALIDATION: [] })

    for trackid, tags in groundtruth.items():
        artistid = track_to_artist[trackid]
        group = artist_splits[artistid]
        for t in tags:
            tag_split_artists[t][group].add(artistid)
            tag_split_tracks[t][group].append(trackid)

    original_number_tags = len(tag_to_tracks)
    original_genres, original_moods, original_instruments = _tags_by_category(tag_to_tracks.keys())

    log.debug("-" * 80)
    for t in tag_to_tracks.keys():
        log.debug("Tag: %s\tartist counts: %s - %s - %s\ttrack counts: %s - %s - %s", t, 
                      len(tag_split_artists[t][TRAIN]), 
                      len(tag_split_artists[t][TEST]),
                      len(tag_split_artists[t][VALIDATION]),
                      len(tag_split_tracks[t][TRAIN]), 
                      len(tag_split_tracks[t][TEST]),
                      len(tag_split_tracks[t][VALIDATION]))
    log.debug("-" * 80)

    tags_to_remove = discard_tags_by_count(tag_split_artists, tag_split_tracks)
    discarded_tags = tags_to_remove

    # Remove these labels from all items in the ground truth
    # Remove all items in the groundtruth which now have no labels

    log.debug("GT currently has %s tracks", len(groundtruth))
    log.debug("Number of unique tags: %s", len(tag_to_tracks))
    log.debug("Going to remove these tags: %s", sorted(list(tags_to_remove)))
    num_removed_tags = len(tags_to_remove)
    remove_genres, remove_moods, remove_instruments = _tags_by_category(tags_to_remove)

    groundtruth = remove_tags_from_groundtruth(groundtruth, tags_to_remove, tag_to_tracks)

    log.debug("After filtering, GT has %s tracks", len(groundtruth))


    log.debug("Building train/test/validation splits of tracks")
    # Take the intersection of all labels in train/test/validation. 
    # These are the labels that we're going to use
    # Filter any label which is not these from the ground truth

    train = {}
    test = {}
    validation = {}
    for trackid, tags in groundtruth.items():
        if track_splits.get(trackid) == TRAIN:
            train[trackid] = tags
        elif track_splits.get(trackid) == TEST:
            test[trackid] = tags
        elif track_splits.get(trackid) == VALIDATION:
            validation[trackid] = tags

    log.debug("train: %s\ntest: %s\nvalidation: %s", len(train), len(test), len(validation))

    all_tags_in_train = _get_all_tags_in_gt(train)
    all_tags_in_test = _get_all_tags_in_gt(test)
    all_tags_in_validation = _get_all_tags_in_gt(validation)
    log.debug("%s tags in train", len(all_tags_in_train))
    log.debug("%s tags in test", len(all_tags_in_test))
    log.debug("%s tags in validation", len(all_tags_in_validation))

    intersection_tags = all_tags_in_train & all_tags_in_test & all_tags_in_validation
    union_tags = all_tags_in_train | all_tags_in_test | all_tags_in_validation
    # Tags to remove is union-intersection

    log.debug("%s tags in union of train-test-validation", len(union_tags))
    log.debug("%s tags in intersection of train-test-validation", len(intersection_tags))
    tags_to_remove = union_tags - intersection_tags
    discarded_tags = discarded_tags | tags_to_remove
    log.debug("need to remove %s tags which don't appear in all splits", len(tags_to_remove))
    log.debug("going to remove these tags: %s", sorted(list(tags_to_remove)))

    num_removed_tags += len(tags_to_remove)

    train = remove_tags_from_groundtruth(train, tags_to_remove, tag_to_tracks)
    test = remove_tags_from_groundtruth(test, tags_to_remove, tag_to_tracks)
    validation = remove_tags_from_groundtruth(validation, tags_to_remove, tag_to_tracks)

    log.debug("after filtering\ntrain: %s\ntest: %s\nvalidation: %s", len(train), len(test), len(validation))

    final_number_tags = original_number_tags - num_removed_tags
    log.debug("Keeping %s tags (%s%%):", final_number_tags, final_number_tags*100.0/original_number_tags)
    log.debug("%s genres out of %s", len(original_genres) - len(remove_genres), len(original_genres))
    log.debug("%s mood/themes out of %s", len(original_moods) - len(remove_moods), len(original_moods))
    log.debug("%s instruments out of %s", len(original_instruments) - len(remove_instruments), len(original_instruments))

    log.debug("Trial %s: Keeping %s tags out of %s; discarded %s tags: %s", 
              trialnumber, final_number_tags, original_number_tags, 
              len(discarded_tags), sorted(list(discarded_tags)))

    return train, test, validation, discarded_tags


def _get_all_tags_in_gt(groundtruth):
    tags = set()
    for k, v in groundtruth.items():
        tags.update(v)
    return tags


def remove_tags_from_groundtruth(groundtruth, tags, tag_to_tracks):
    """ Remove all tags in `tags` from the groundtruth, using `tag_to_tracks` to find
    which tracks to remove tags from. If a track has no more tags, remove it
    from the groundtruth
    """
    # We don't want to change the original dict as it is used in all interations
    groundtruth = copy.deepcopy(groundtruth)

    log.debug("Removing %s tags from groundtruth", len(tags))

    affected_tracks = set()
    for t in tags:
        tag_recs = tag_to_tracks[t]
        affected_tracks.update(set(tag_recs))

        for rec in tag_recs:
            if rec in groundtruth:
                groundtruth[rec].discard(t)

    log.debug("number of affected tracks: %s", len(affected_tracks))

    # Check all affected tracks and delete if it it no longer has any tags
    count = 0
    for r in affected_tracks:
        if r in groundtruth and len(groundtruth[r]) == 0:
            count += 1
            del groundtruth[r]

    log.debug("completely deleted %s tracks from gt", count)

    return groundtruth



def main(groundtruthfile):
    run_trials(groundtruthfile)


if __name__ == "__main__":
    desc = """
Split a ground-truth file into a train/test/validation split, applying
artist filtering to make sure that tracks from the same artist all
fall into the same split.
    """
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("groundtruthfile", help="Metadata ground-truth file")
    parser.add_argument('--splits', default=5,
                        help='Required number of splits (default 5)')
    parser.add_argument('--trials', default=500,
                        help='Number of random split attempts to select best splits (default 500)')
    parser.add_argument('--split-ratio', default="60-20-20",
                        help='Train/test/validation split ratio (default "60-20-20")')
    parser.add_argument('--artist-threshold', default="10-5-5",
                        help='Minimum amount of artists that each tag should have in train/test/validation splits (default "10-5-5")')
    parser.add_argument('--track-threshold', default="40-20-20",
                        help='Minimum amount of tracks that each tag should have in train/test/validation splits (default "40-20-20")')

    args = parser.parse_args()

    config = {}

    train_perct, test_perct, validation_perct = [int(x) for x in args.split_ratio.split('-')]
    if train_perct + test_perct + validation_perct != 100:
        print("Split ratios should sum to 100")
        sys.exit(1)
    
    config['split_ratio'] = { TRAIN: train_perct, 
                              TEST: test_perct, 
                              VALIDATION: validation_perct }

    art_train, art_test, art_valid = [int(x) for x in args.artist_threshold.split('-')]
    config['artist_threshold'] = { TRAIN: art_train, 
                              TEST: art_test, 
                              VALIDATION: art_valid }
    
    track_train, track_test, track_valid = [int(x) for x in args.track_threshold.split('-')]
    config['track_threshold'] = { TRAIN: track_train, 
                              TEST: track_test, 
                              VALIDATION: track_valid }

    config['splits'] = int(args.splits)
    config['trials'] = int(args.trials)

    main(args.groundtruthfile)
