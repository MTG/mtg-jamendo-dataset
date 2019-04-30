# MTG Jamendo Dataset
Metadata, scripts and baselines for MTG Jamendo dataset for auto-tagging.

## Structure

- `data`
  - `base.csv` (56650) - master file without durations (only artist/album cross-referencing)
  - `base_with_durations.csv` (56639) - with durations (removed corrupt)
  - `base_filtered_by_durations.csv`(55701) - with durations more than 30s

- `stats_base` statistics for `base_filtered_by_durations.csv`

## Using the dataset

* Create virtual environment and install requirements (probably we will have several `requirements.txt` for different tasks, you don't need `tensorflow` for statistics)
```bash
virtualenv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

* Compute statistics
```bash
python scripts/statistics.py data/base_with_durations.tsv stats_base
python scripts/statistics.py data/base_filtered_by_durations.tsv stats_filtered_by_durations
```

* Merge tags and recompute statistics
```bash
python scripts/merge_tags.py data/base_filtered_by_durations.tsv data/tag_map.json data/base_with_merged_tags.tsv
python scripts/statistics.py data/base_with_merged_tags.tsv stats_merged
```

* Run baseline
