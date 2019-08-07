import argparse

import numpy as np
import pandas as pd
from sklearn import metrics


def evaluate(groundtruth_file, prediction_file, decision_file, output_file=None):
    groundtruth = np.load(groundtruth_file)
    predictions = np.load(prediction_file)
    decisions = np.load(decision_file)

    for name, data in [('Decision', decisions), ('Prediction', predictions)]:
        if not data.shape == groundtruth.shape:
            raise ValueError('{} file dimensions {} don''t match the groundtruth {}'.format(
                name, data.shape, groundtruth.shape))

    results = {'ROC-AUC': metrics.roc_auc_score(groundtruth, predictions, average='macro'),
               'PR-AUC': metrics.average_precision_score(groundtruth, predictions, average='macro')}

    for average in ['macro', 'micro']:
        results['precision-' + average], results['recall-' + average], results['F-score-' + average], _ = \
            metrics.precision_recall_fscore_support(groundtruth, decisions, average=average)

    for metric, value in results.items():
        print('{}\t{:6f}'.format(metric, value))

    if output_file is not None:
        df = pd.DataFrame(results.values(), results.keys())
        df.to_csv(output_file, sep='\t', header=None, float_format='%.6f')

    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculates evaluation metrics from prediction and ground-truth '
                                                 'matrices')
    parser.add_argument('groundtruth_file', help='NPY file with groundtruth values (tracks x tags)')
    parser.add_argument('prediction_file', help='NPY file with activation values (float64)')
    parser.add_argument('decision_file', help='NPY file with decision values (bool)')
    parser.add_argument('--output-file', help='file to write metric values to')
    args = parser.parse_args()

    evaluate(args.groundtruth_file, args.prediction_file, args.decision_file, args.output_file)
