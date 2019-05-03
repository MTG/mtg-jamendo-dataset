# MTG Jamendo Dataset
Metadata, scripts and baselines for MTG Jamendo dataset for auto-tagging.

## Structure

- `data` annotation_files
  - `base.tsv` (56650) - master file without track durations (only artist/album cross-referencing)
  - `with_durations.tsv` (56639) - with durations (removed corrupt audio files)
  - `filtered_by_durations.tsv`(55701) - with track durations more than 30s
  - `with_merged_tags.tsv`(55701) - with tags merged according to `tag_map.json`
  - `filtered_by_artists.tsv`(55609) - with tags that have at least 50 unique artists
  - `tag_map.json` - map of tags that we merged

- `stats` statistics of number of tracks, albums and artists per tag
  - each directory has statistics for annotations file with the same name

## Using the dataset

* Create virtual environment and install requirements (probably we will have several `requirements.txt` for different tasks, you don't need `tensorflow` for statistics)
```bash
virtualenv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

### Reproduce post-processing

* Compute statistics
```bash
python scripts/statistics.py data/with_durations.tsv stats/with_durations
python scripts/statistics.py data/filtered_by_durations.tsv stats/filtered_by_durations
```

* Merge tags and recompute statistics
```bash
python scripts/merge_tags.py data/filtered_by_durations.tsv data/tag_map.json data/with_merged_tags.tsv
python scripts/statistics.py data/with_merged_tags.tsv stats/with_merged_tags
```

* Filter out tags with low number of unique artists and recompute statistics
```bash
python scripts/filter.py data/with_merged_tags.tsv 50 data/filtered_by_artists.tsv --stats-directory stats/filtered_by_artists
```

### Reproduce experiments

TODO

## Acknowledgments

TODO
