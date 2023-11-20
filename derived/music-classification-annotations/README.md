# Music Classification Annotations

This dataset contains a collection of annotations for the [split-0 test set](data/splits/split-0/autotagging-test.tsv) of the MTG-Jamendo Dataset according to the taxonomies of 15 existing music classification datasets.
All the considered taxonomies are single label, including binary and multi-class cases:

- **genre_dortmund**: alternative, blues, electronic, folkcountry, funksoulrnb, jazz, pop, raphiphop, rock
- **genre_rosamerica**: classic, dance, hip hop, jazz, pop, rhythm and blues, rock, speech
- **genre_tzanetakis**: blues, classic, country, disco, hip hop, jazz, metal, pop, reggae, rock
- **genre_electronic**: ambeint, dnb, house, techno, trance
- **genre_acoustic**: acoustic, non acoustic
- **mood_aggressive**: aggressive, non aggressive
- **mood_electronic**: electronic, non electronic
- **mood_happy**: happy, non happy
- **mood_party**: party, non party
- **mood_relaxed**: relaxed, non relaxed
- **mood_sad**: sad, non sad
- **danceability**: danceable, non danceable
- **voice_instrumental**: voice, instrumental
- **gender**: male, female
- **tonal_atonal**: atonal, tonal


There are annotations for the complete *split-0 test set* for all the taxonomies but those related to genres, where we could only annotate 1,500 tracks.
Most tracks were annotated by 3 different annotators using a dedicated [annotation tool](https://github.com/mtg/mtg-jamendo-annotator).
This tool forces the user to select a label for the mood-related, danceability, voice_instrumental, and tonal_atonal taxonomies.
For the genre-related and voice_instrumental taxonomies there are options `unmatched` and `instrumental` for tracks that are not suitable for the taxonomy at hand.
We provide two ground truth files: `music-classification-annotations-raw.tsv`, with all the collected annotations, and `music-classification-annotations-clean.tsv`, with only the annotations where the three annotators agreed and the answer was not `unmatched` or `instrumental`.

The following table shows the number of annotations with perfect inter-annotator agreement and suitable labels:

| Taxonomy | Agreement rate (%) | Number of tracks |
|---|---|---|
| genre_dortmund | 49 | 612 |
| genre_rosamerica | 52 | 573 |
| genre_tzanetakis | 47 | 411 |
| genre_electronic | 62 | 180 |
| mood_acoustic | 60 | 6429 |
| mood_aggressive | 71 | 7686 |
| mood_electronic | 66 | 7143 |
| mood_happy | 53 | 5702 |
| mood_party | 69 | 7476 |
| mood_relaxed | 57 | 6163 |
| mood_sad | 53 | 5678 |
| danceability | 44 | 4476 |
| voice_instrumental | 87 | 2070 |
| gender | 75 | 7533 |
| tonal_atonal | 87 | 8756 |

## Usage
The existing tools can be used to load the music classification annotations:

```python
import commons

input_file = '../derived/music-classification-annotations/music-classification-annotations-clean.tsv'
tracks, tags, extra = commons.read_file(input_file)
```

## Annotation format
The annotations follow this naming convention: `<taxonomy>---<annotation_1>,<annotation_2>,<annotation_3>`.
Note that some tracks are missing annotations for some taxonomies or may be annotated by only one or two annotators.
This is how the raw annotations for an example track look like:

```python
{
    484424: {
    ...
    'tags': [
        'genre_dortmund---pop,unmatched,unmatched',
        'genre_rosamerica---pop,unmatched,unmatched',
        'genre_tzanetakis---reggae,reggae,reggae',
        ...
        ],
    'genre': set(),
    'mood/theme': set(),
    'instrument': set(),
    'genre_dortmund': {'unmatched', 'pop'},
    'genre_rosamerica': {'unmatched', 'pop'},
    'genre_tzanetakis': {'reggae'}
    ...
    }
    ...
}
```

In the `clean` version, we only include taxonomies where the three annotators agreed and the label was not `unmatched` or `instrumental`:

```python
{
    484424: {
    ...
    'tags': [
        'genre_tzanetakis---reggae,reggae,reggae',
        'mood_aggressive---not_aggressive,not_aggressive,not_aggressive',
        'mood_happy---happy,happy,happy',
        ...
        ],
    'genre': set(),
    'mood/theme': set(),
    'instrument': set(),
    'genre_tzanetakis': {'reggae'},
    'mood_aggressive': {'not_aggressive'},
    'mood_happy': {'happy'}
    ...
    }
    ...
}
```
As it can be seen, genre_dortmund and genre_rosamerica are not present in the clean version due to the disagreement among annotators.
