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

# Splits, 70%, 15%, 15%
TRAIN_PERCT = 0.6
TEST_PERCT = 0.2
VALIDATION_PERCT = 0.2

def _split_artists(artistids):
    random.shuffle(artistids)
    art_len = len(artistids)
    train_count = int(math.ceil(art_len * TRAIN_PERCT))
    test_count = int(math.ceil(art_len * TEST_PERCT))
    validation_count = int(math.ceil(art_len * VALIDATION_PERCT))

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


def _load_groundtruth(groundtruthfile):
    log.debug("Loading groundtruth")
    with open(groundtruthfile) as fp:
        r = csv.reader(fp, delimiter="\t")
        header = r.next()
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


def one_iteration(trialnumber, groundtruthfile):
    groundtruth, groundtruth_meta, track_to_artist, artist_to_tracks, header = _load_groundtruth(groundtruthfile)

    # Randomly split artists into sections
    log.debug("Splitting by artists")
    artists = artist_to_tracks.keys()
    artist_splits = _split_artists(artists)
    track_splits = {}
    for artist, group in artist_splits.items():
        for t in artist_to_tracks[artist]:
            track_splits[t] = group

    train, test, validation = split_groundtruth(groundtruth, track_to_artist, artist_splits, track_splits)

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


def discard_tags_by_count(tag_split_artists, tag_split_tracks):
    # TODO make hardcoded thresholds configurable

    # Tags below the minimum artist count for train/test/validation
    discard_tags_artist = tag_split_artists
    for t in discard_tags_artist.keys():
        if (len(discard_tags_artist[t][TRAIN]) >= 10 and 
                len(discard_tags_artist[t][TEST]) >= 5 and 
                len(discard_tags_artist[t][VALIDATION]) >= 5):
            del discard_tags_artist[t]

    # Tags below the minimum track count for train/test/validation
    discard_tags_track = tag_split_tracks
    for t in discard_tags_track.keys():
        if (len(discard_tags_track[t][TRAIN]) >= 40 and 
                len(discard_tags_track[t][TEST]) >= 20 and 
                len(discard_tags_track[t][VALIDATION]) >= 20):
            del discard_tags_track[t]

    log.debug("Tags with insufficient artist counts: %s", discard_tags_artist.keys())
    log.debug("Tags with insufficient track counts: %s", discard_tags_track.keys())

    tags_to_remove = set(discard_tags_artist.keys() + discard_tags_track.keys())
    return tags_to_remove


def split_groundtruth(groundtruth, track_to_artist, artist_splits, track_splits):

    log.debug("Making mapping of tag counts")

    # Mapping from tags to tracks and artists
    tag_to_tracks = collections.defaultdict(list)
    tag_to_artists = collections.defaultdict(set)

    tag_split_artists = collections.defaultdict(lambda: { TRAIN: set(), TEST: set(), VALIDATION: set() })
    tag_split_tracks = collections.defaultdict(lambda: { TRAIN: [], TEST: [], VALIDATION: [] })

    for trackid, tags in groundtruth.items():
        artistid = track_to_artist[trackid]
        group = artist_splits[artistid]
        for t in tags:
            tag_to_tracks[t].append(trackid)
            tag_to_artists[t].add(artistid)
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



def main(trialnumber, groundtruthfile):
    one_iteration(trialnumber, groundtruthfile)


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
