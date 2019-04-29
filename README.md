# MTG Jamendo Dataset
Metadata, scripts and baselines for MTG Jamendo dataset for auto-tagging.

## Structure

- `base.csv` - master file with tracks (only artist/album cross-referencing)
- `tracks.tsv`

## Using the dataset

* Create virtual environment and install requirements (probably we will have several `requirements.txt` for different tasks, you don't need `tensorflow` for statistics)
```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

* Compute statistics

* Run baseline
