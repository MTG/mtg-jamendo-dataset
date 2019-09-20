import argparse

import numpy as np
import pandas as pd
from sklearn import metrics
from pathlib import Path

from evaluate import evaluate

ROOT = Path('../../mediaeval-submissions/')
RESULTS_ROOT = Path('../../mediaeval-submissions/all')
GROUNDTRUTH = '../results/mediaeval2019/groundtruth.npy'

DATA = {
    'TaiInn': {
        'dir': 'MediaEval2019/results/',
    },
    'AugLi': {
        'dir': 'AugLi_results_mediaeval19_emotion_task',
    }
}

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='Calculates evaluation metrics from prediction and ground-truth '
    #                                              'matrices')
    # parser.add_argument('groundtruth_file', help='NPY file with groundtruth values (tracks x tags)')
    # args = parser.parse_args()

    groundtruth = np.load(GROUNDTRUTH)

    for team, data in DATA.items():
        results = {}
        root = ROOT / data['dir']
        prediction_files = sorted(root.glob('./*predictions.npy'))
        decision_files = sorted(root.glob('./*decisions.npy'))
        names = [filename.stem[:-11].strip('-_ ') for filename in prediction_files]

        for name, prediction_file, decision_file in zip(names, prediction_files, decision_files):
            predictions = np.load(prediction_file)
            decisions = np.load(decision_file)
            results[name] = evaluate(groundtruth, predictions, decisions)
        df = pd.DataFrame(results)
        print(df)
        df.to_csv(RESULTS_ROOT / (team + '.tsv'), sep='\t', float_format='%.6f')
