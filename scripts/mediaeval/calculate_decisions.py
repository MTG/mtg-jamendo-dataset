import argparse

import numpy as np
import pandas as pd
from sklearn import metrics


def calculate_decisions(groundtruth, predictions, tags, threshold_file, decision_file=None, display=False):
    if not predictions.shape == groundtruth.shape:
        raise ValueError('Prediction matrix dimensions {} don''t match the groundtruth {}'.format(
            predictions.shape, groundtruth.shape))

    n_tags = groundtruth.shape[1]
    if not n_tags == len(tags):
        raise ValueError('Number of tags in tag list ({}) doesn''t match the matrices ({})'.format(
            len(tags), n_tags))

    # Optimized macro F-score
    thresholds = {}
    for i, tag in enumerate(tags):
        precision, recall, threshold = metrics.precision_recall_curve(groundtruth[:, i], predictions[:, i])
        f_score = np.nan_to_num((2 * precision * recall) / (precision + recall))
        thresholds[tag] = threshold[np.argmax(f_score)]  # removed float()

    if display:
        for tag, threshold in thresholds.items():
            print('{}\t{:6f}'.format(tag, threshold))

    df = pd.DataFrame(thresholds.values(), thresholds.keys())
    df.to_csv(threshold_file, sep='\t', header=None)

    decisions = predictions > np.array(list(thresholds.values()))
    if decision_file is not None:
        np.save(decision_file, decisions)

    return thresholds, decisions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculates evaluation metrics from prediction and ground-truth '
                                                 'matrices')
    parser.add_argument('groundtruth_file', help='NPY file with groundtruth values (tracks x tags)')
    parser.add_argument('prediction_file', help='NPY file with activation values (float64)')
    parser.add_argument('threshold_file', help='TSV file to write optimal decision thresholds for each tag')
    parser.add_argument('tag_file', help='TSV file with list of tags')
    parser.add_argument('--decision-file', help='NPY file to write decision values (bool)')
    args = parser.parse_args()

    groundtruth = np.load(args.groundtruth_file)
    predictions = np.load(args.prediction_file)
    tags = pd.read_csv(args.tag_file, delimiter='\t', header=None)[0].to_list()

    calculate_decisions(groundtruth, predictions, tags, args.threshold_file, args.decision_file, display=True)
