# MediaEval 2019 Emotion and Theme Scripts

Scripts used for [MediaEval 2019 task: Emotion and Theme Recognition in Music Using Jamendo](https://multimediaeval.github.io/2019-Emotion-and-Theme-Recognition-in-Music-Task/)

Requirements are the same as in the [scripts](/scripts/requirements.txt) directory. It is recommended to use `scripts` as working directory, because some scripts are dependent on `commons.py` to read TSV files and should be executed with `-m` flag.

## Evaluation

```bash
python mediaeval2019/evaluate.py ../results/mediaeval2019/groundtruth.npy ../results/mediaeval2019/predictions.npy ../results/mediaeval2019/decisions.npy --output-file ../results/mediaeval2019/results.tsv
```

Will produce `results.tsv` that will contain values for all metrics that are used in the challenge.

## Calculate thresholds and generate decisions

```bash
python mediaeval2019/calculate_decisions.py ../results/mediaeval2019/groundtruth.npy ../results/mediaeval2019/predictions.npy ../results/mediaeval2019/thresholds.txt ../data/tags/moodtheme_split.txt --decision-file ../results/mediaeval2019/decisions.npy
```

Will produce `thresholds.txt` that contains per-tag thresholds for making decisions, as well as an optional `decisions.npy` that will contain the binary matrix with the decisions.

## Other helper scripts

* Generate groundtruth matrix

```bash
python -m  mediaeval2019.generate_matrix ../data/splits/split-0/autotagging_moodtheme-test.tsv ../data/tags/moodtheme_split.txt ../results/mediaeval2019/groundtruth.npy 
```


* Generate decisions for naive baselines

```bash
python -m  mediaeval2019.baseline_naive ../data/splits/split-0/autotagging_moodtheme-train.tsv ../data/splits/split-0/autotagging_moodtheme-test.tsv ../data/tags/moodtheme_split.txt ../results/mediaeval2019/baseline_popular_decisions_tracks.npy 
```
