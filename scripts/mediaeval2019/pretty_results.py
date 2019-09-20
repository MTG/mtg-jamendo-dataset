import argparse

import numpy as np
import pandas as pd
from sklearn import metrics
from pathlib import Path

METRIC = 'PR-AUC-macro'

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate leaderboard tables')
    parser.add_argument('directory', help='directory with TSV files per team')
    parser.add_argument('output', help='output file')
    args = parser.parse_args()

    root = Path(args.directory)
    tsv_files = root.glob('./*.tsv')
    results = {}
    best = {}
    for tsv_file in tsv_files:
        team = tsv_file.stem
        data = pd.read_csv(tsv_file, delimiter='\t', index_col=0)
        results[team] = data

        value = data[METRIC].max()
        algo = data[METRIC].idxmax()

        best['{} ({})'.format(team, algo)] = value

    best = pd.DataFrame(best.values(), best.keys(), columns=[METRIC])

    output = '## Leaderboard\n\n'
    output += best.to_html() + '\n\n'
    output += '## All submissions\n\n'

    for team, result in results.items():
        output += '### ' + team + '\n\n'
        output += result.to_html() + '\n\n'

    with open(args.output, 'w') as fp:
        fp.write(output)
