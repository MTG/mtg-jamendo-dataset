import argparse

import numpy as np
from sklearn import metrics


def evaluate(groundtruth_file, activation_file, prediction_file):
    groundtruth = np.load(groundtruth_file)
    activation = np.load(activation_file)
    prediction = np.load(prediction_file)

    results = {'ROC-AUC': metrics.roc_auc_score(groundtruth, activation, average='macro'),
               'PR-AUC': metrics.average_precision_score(groundtruth, activation, average='macro')}

    for average in ['macro', 'micro']:
        results['precision-' + average], results['recall-' + average], results['F-score-' + average], _ = \
            metrics.precision_recall_fscore_support(groundtruth, prediction, average=average)

    for metric, value in results.items():
        print('{} = {:4f}'.format(metric, value))
    return results


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Calculates evaluation metrics from prediction and ground-truth '
                                                 'matrices')
    parser.add_argument('groundtruth_file', help='NPY file with groundtruth values (tracks x tags)')
    parser.add_argument('activation_file', help='NPY file with activation values (real)')
    parser.add_argument('prediction_file', help='NPY file with prediction values (binary)')
    args = parser.parse_args()

    evaluate(args.groundtruth_file, args.activation_file, args.prediction_file)
