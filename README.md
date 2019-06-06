# The MTG-Jamendo Dataset
Metadata, scripts and baselines for MTG-Jamendo dataset for auto-tagging.

## License

* The code in this repository is licensed under [Apache 2.0](LICENSE) 
* The metadata is licensed under a [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
* The audio files are licensed under Creative Commons licenses, see individual licenses for details in `audio_licenses.txt`.

## Structure

### Metadata files in `data`

Pre-processing
- `raw.tsv` (56639) - raw file without postprocessing
- `raw_30s.tsv`(55701) - tracks with duration more than 30s
- `raw_30s_cleantags.tsv`(55701) - with tags merged according to `tag_map.json`
- `raw_30s_cleantags_50artists.tsv`(55609) - with tags that have at least 50 unique artists
- `tag_map.json` - map of tags that we merged
- `autotagging.tsv` = `raw_30sec_cleantags_50artists.tsv` - base file for autotagging (after all postprocessing, 195 tags)

Subsets
- `autotagging_top50tags.tsv` (54380) - only top 50 tags according to tag frequency in terms of tracks
- `autotagging_moodtheme.tsv` (18486) - only tracks with mood/theme tags (57 tags), and only those tags

Splits
- `splits` folder contains training/validation/testing sets for `autotagging.tsv` and subsets

Note: A few tags are discarded in the splits to guarantee the same
list of tags across all splits. For `autotagging.tsv`, this results in 55525 tracks annotated by 87 genre tags, 40 instrument tags, and 56 mood/theme tags available in the splits.


### Statistics in `stats`

Statistics of number of tracks, albums and artists per tag sorted by artists
Each directory has statistics for metadata file with the same name.


### Downloading the dataset
All audio is distributed in 320kbps MP3 format. In addition we provide precomputed mel-spectrograms which are distributed as NumPy Arrays in NPY format. The audio files and the NPY files are split into folders packed into TAR archives. The dataset is hosted [online at MTG UPF](https://essentia.upf.edu/documentation/datasets/mtg-jamendo/).

We provide the following data subsets:
- `raw_30s/audio` - all available audio for `raw_30s.tsv` (508 GB)
- `raw_30s/melspecs` - mel-spectrograms for `raw_30s.tsv` (229 GB)
- `autotagging-moodtheme/audio` - audio for the mood/theme subset `autotagging_moodtheme.tsv` (152 GB)
- `autotagging-moodtheme/melspecs` - mel-spectrograms for the `autotagging_moodtheme.tsv` subset (68 GB)

For faster downloads, we host a copy of the dataset on Google Drive. We provide a script to download and validate all files in the dataset. See its help message for more information:

```bash
python3 scripts/download/download_gdrive.py -h
```
```
usage: download_gdrive.py [-h] [--dataset {raw_30s,autotagging_moodtheme}]
                          [--type {audio,melspecs}] [--unpack] [--remove]
                          outputdir

Download the MTG-Jamendo dataset from Google Drive

positional arguments:
  outputdir             directory to store the dataset

optional arguments:
  -h, --help            show this help message and exit
  --dataset {raw_30s,autotagging_moodtheme}
                        dataset to download (default: raw_30s)
  --type {audio,melspecs}
                        type of data to download (audio or mel-spectrograms)
                        (default: audio)
  --unpack              unpack tar archives (default: False)
  --remove              remove tar archives while unpacking one by one (use to
                        save disk space) (default: False)

```

For example, to download audio for the `autotagging_moodtheme.tsv` subset, unpack and validate all tar archives:

```
mkdir /path/to/download
python3 scripts/download/download_gdrive.py --dataset autotagging_moodtheme --type audio /path/to/download --unpack --remove
```


Unpacking process is run after tar archive downloads are complete and validated. In the case of download errors, re-run the script to download missing files.

Due to the large size of the dataset, it can be useful to include the `--remove` flag to save disk space: in this case, tar archive are unpacked and immediately removed one by one.


## Using the dataset

### Requirements

* Python 3.6
* Virtualenv: `pip install virtualenv`
* Create virtual environment and install requirements
```bash
virtualenv venv
source venv/bin/activate
pip install -r scripts/requirements.txt
```

### Loading data in python
Assuming you are working in `scripts` folder
```python
import commons

input_file = '../data/autotagging.tsv'
tracks, tags, extra = commons.read_file(input_file)
```
`tracks` is a dictionary with `track_id` as key and track data as value:
```python
{
    1376256: {
    'artist_id': 490499,
    'album_id': 161779,
    'path': '56/1376256.mp3',
    'duration': 166.0,
    'tags': [
        'genre---easylistening',
        'genre---downtempo',
        'genre---chillout',
        'mood/theme---commercial',
        'mood/theme---corporate',
        'instrument---piano'
        ],
    'genre': {'chillout', 'downtempo', 'easylistening'},
    'mood/theme': {'commercial', 'corporate'},
    'instrument': {'piano'}
    }
    ...
}
```
`tags` contains mapping of tags to `track_id`:
```python
{
    'genre': {
        'easylistening': {1376256, 1376257, ...},
        'downtempo': {1376256, 1376257, ...},
        ...
    },
    'mood/theme': {...},
    'instrument': {...}
}
```
`extra` has information that is useful to format output file, so pass it to `write_file` if you are using it, otherwise you can just ignore it

### Reproduce postprocessing & statistics

* Compute statistics
```bash
python scripts/statistics.py data/raw.tsv stats/raw
python scripts/statistics.py data/raw_30s.tsv stats/raw_30s
```

* Clean tags and recompute statistics
```bash
python scripts/clean_tags.py data/raw_30s.tsv data/tag_map.json data/raw_30s_cleantags.tsv
python scripts/statistics.py data/raw_30s_cleantags.tsv stats/raw_30s_cleantags
```

* Filter out tags with low number of unique artists and recompute statistics
```bash
python scripts/filter_fewartists.py data/raw_30s_cleantags.tsv 50 data/raw_30s_cleantags_50artists.tsv --stats-directory stats/raw_30s_cleantags_50artists
```

* `autotagging` file in `data` and folder in `stats` is a symbolic link to `raw_30s_cleantags_50artists`

* Visualize top 20 tags per category
```bash
python scripts/visualize_tags stats/autotagging 20  # generates top20.pdf figure
```

### Subsets
* Create subset with only top50 tags by number of tracks
```bash
python scripts/filter_toptags.py data/autotagging.tsv 50 data/autotagging_top50tags.tsv --stats-directory stats/autotagging_top50tags
```

* Create subset with only mood/theme tags
```bash
python scripts/filter_category data/autotagging.tsv mood/theme data/autotagging_moodtheme.tsv
```
### Reproduce experiments

TODO


## Citing the dataset

Please consider citing the following publication when using the dataset:

[1] Bogdanov, D., Won M., Tovstogan P., Porter A., & Serra X. (2019).  [The MTG-Jamendo Dataset for Automatic Music Tagging](http://mtg.upf.edu/node/3957). Machine Learning for Music Discovery Workshop, International Conference on Machine Learning (ICML 2019).

An expanded version of the paper describing the dataset and the baselines will be announced later.


## Acknowledgments

This work was funded by the predoctoral grant MDM-2015-0502-17-2 from the Spanish Ministry of Economy and Competitiveness linked to the Maria de Maeztu Units of Excellence Programme (MDM-2015-0502). 

This project has received funding from the European Union's Horizon 2020 research and innovation programme under the Marie Skłodowsa-Curie grant agreement No. 765068.

This work has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement No 688382 "AudioCommons".

<img src="img/eu.svg" height="64" hspace="20">
