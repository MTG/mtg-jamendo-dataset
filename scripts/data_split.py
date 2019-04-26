import argparse
import csv
import collections
import random
import sys
import math
import logging
import os

import util

log = logging.Logger('lookup')
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
fh = logging.FileHandler("make_split.log")
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
log.setLevel(logging.DEBUG)
log.addHandler(ch)
log.addHandler(fh)


TRAIN = "train"
TEST = "test"
VALIDATION = "validation"

# Splits, 70%, 15%, 15%
TRAIN_PERCT = 0.6
TEST_PERCT = 0.2
validation_PERCT = 0.2

def _split_artists(artistids):
    random.shuffle(artistids)
    art_len = len(artistids)
    train_count = int(math.ceil(art_len * TRAIN_PERCT))
    test_count = int(math.ceil(art_len * TEST_PERCT))
    validation_count = int(math.ceil(art_len * validation_PERCT))

    train_items = artistids[:train_count]
    artistids = artistids[train_count:]
    test_items = artistids[:test_count]
    artistids = artistids[test_count:]
    validation_items = artistids[:validation_count]

    log.debug("%s artists, %s train, %s test, %s validation", art_len, train_count, test_count, validation_count)

    splits = {}
    for i in train_items:
        splits[i] = TRAIN
    for i in test_items:
        splits[i] = TEST
    for i in validation_items:
        splits[i] = VALIDATION

    return splits


def one_iteration(trialnumber, artistmap, groundtruthfile):
    # Randomly split artists into sections
    tracks = list(set(artistmap.values()))
    artist_to_tracks = collections.defaultdict(list)
    for track, artist in artistmap.items():
        artist_to_tracks[artist].append(track)

    log.debug("Splitting by artists")
    artist_splits = _split_artists(tracks)
    track_splits = {}
    for artist, group in artist_splits.items():
        for t in artist_to_tracks[artist]:
            track_splits[t] = group

    log.debug("Loading groundtruth")
    with open(groundtruthfile) as fp:
        r = csv.reader(fp, delimiter="\t")
        header = r.next()
        groundtruth = {}
        groundtruth_meta = {}
        for l in r:
            groundtruth_meta[l[0]] = [l[1], l[2], l[3], l[4]] # artistid, albumid, path, duration
            groundtruth[l[0]] = set(l[5:]) 

    train, test, validation = split_groundtruth(groundtruth, artistmap, artist_splits, track_splits)

    gt_dir = os.path.dirname(groundtruthfile)
    gt_file = os.path.basename(groundtruthfile)
    gt_name, gt_ext = os.path.splitext(gt_file)

    #trialdir = os.path.join(gt_dir, "trial-%s" %trialnumber)
    trialdir = "trial-%s" % trialnumber
    util.mkdir_p(trialdir)

    for part, data in [("train", train), ("test", test), ("validation", validation)]:
        out_file = os.path.join(trialdir, "%s-%s%s" % (gt_name, part, gt_ext))
        log.debug("Writing part %s to file %s", part, out_file)
        with open(out_file, "w") as fp:
            w = csv.writer(fp, delimiter="\t")
            w.writerow(header)
            for trackid, tags in data.items():
                row = [trackid] + groundtruth_meta[trackid] + list(tags)
                w.writerow(row)


def split_groundtruth(groundtruth, artistmap, splits, track_splits):

    tag_count_artist = {TRAIN: collections.Counter(), TEST: collections.Counter(), VALIDATION: collections.Counter()}
    tag_count_track = {TRAIN: collections.Counter(), TEST: collections.Counter(), VALIDATION: collections.Counter()}

    # Helper dict saying which track have each tag
    tag_to_tracks = collections.defaultdict(list)

    seen_artists = set()
    log.debug("Making mapping of tag counts")
    for trackid, tags in groundtruth.items():
        artistid = artistmap[trackid]
        group = splits[artistid] # Is this train/test/validation

        for t in tags:
            tag_to_tracks[t].append(trackid)
            tag_count_track[group][t] += 1 # How many tracks each tag has

        # How many artists each tag has
        if artistid not in seen_artists:
            seen_artists.add(artistid)
            for t in tags:
                tag_count_artist[group][t] += 1

    log.debug("Number of unique tags: %s", len(tag_to_tracks))
    original_number_tags = len(tag_to_tracks)

    low_artist_train = check_tags_for_count(tag_count_artist[TRAIN], "artist train", 10)
    low_artist_test = check_tags_for_count(tag_count_artist[TEST], "artist test", 5)
    low_artist_validation = check_tags_for_count(tag_count_artist[VALIDATION], "artist validation", 5)

    low_track_train = check_tags_for_count(tag_count_track[TRAIN], "track train", 40)
    low_track_test = check_tags_for_count(tag_count_track[TEST], "track test", 20)
    low_track_validation = check_tags_for_count(tag_count_track[VALIDATION], "track validation", 20)

    tags_to_remove = set()
    tags_to_remove.update(set(low_artist_test.keys()))
    tags_to_remove.update(set(low_artist_train.keys()))
    tags_to_remove.update(set(low_artist_validation.keys()))
    tags_to_remove.update(set(low_track_test.keys()))
    tags_to_remove.update(set(low_track_train.keys()))
    tags_to_remove.update(set(low_track_validation.keys()))

    # Remove these labels from all items in the ground truth
    # Remove all items in the groundtruth which now have no labels
    # Do the count but for tracks - make sure that a label is applied to at least 20/20/30 tracks

    log.debug("GT currently has %s tracks", len(groundtruth))
    log.debug("going to remove these tags")
    log.debug(sorted(list(tags_to_remove)))
    num_removed_tags = len(tags_to_remove)

    groundtruth = remove_tags_from_groundtruth(groundtruth, tags_to_remove, tag_to_tracks)

    log.debug("After filtering, GT has %s tracks", len(groundtruth))


    log.debug("Building train/test/validation splits of tracks")
    # Take the intersection of all labels in train/test/validation. These are the labels that we're going to use
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
    log.debug("need to remove %s tags which don't appear in all splits", len(tags_to_remove))
    log.debug("going to remove these tags")
    log.debug(sorted(list(tags_to_remove)))
    num_removed_tags += len(tags_to_remove)

    train = remove_tags_from_groundtruth(train, tags_to_remove, tag_to_tracks)
    test = remove_tags_from_groundtruth(test, tags_to_remove, tag_to_tracks)
    validation = remove_tags_from_groundtruth(validation, tags_to_remove, tag_to_tracks)

    log.debug("after filtering\ntrain: %s\ntest: %s\nvalidation: %s", len(train), len(test), len(validation))

    final_number_tags = original_number_tags - num_removed_tags
    log.debug("Keeping %s tags (%s%%)", final_number_tags, final_number_tags*100.0/original_number_tags)

    return train, test, validation


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


def check_tags_for_count(tag_counts, group, minimum):
    # Find if there are any labels which have a count of less than a theshold
    log.debug("Finding tag counts for %s less than %s", group, minimum)
    less_than_minimum = dict([(k, v) for k, v in tag_counts.most_common() if v < minimum])
    log.debug(" .. found %s", len(less_than_minimum))

    return less_than_minimum

def main(trialnumber, groundtruthfile):
    track_to_artist = {}
    log.debug("Loading artist map")
    with open(groundtruthfile) as fp:
        r = csv.reader(fp, delimiter="\t")
        next(r) # skip header
        for l in r:
            track = l[0]
            artist = l[1]
            track_to_artist[track] = artist

    one_iteration(trialnumber, track_to_artist, groundtruthfile)


if __name__ == "__main__":
    desc = """
Split a ground-truth file into a train/test/validation split, applying
artist filtering to make sure that tracks from the same artist all
fall into the same split.
    """
    parser = argparse.ArgumentParser(description=desc, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("trialnumber", help="A unique number to use as a trial")
    parser.add_argument("groundtruthfile", help="Metadata ground-truth file")

    args = parser.parse_args()

    main(args.trialnumber, args.groundtruthfile)
