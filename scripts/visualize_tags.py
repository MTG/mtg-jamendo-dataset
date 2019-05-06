import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os


def visualize(tsv_file, n, category, output_file):
    data = pd.read_csv(tsv_file, delimiter='\t')
    data = data[:n]
    data = data.sort_values(by=['tracks'], ascending=False)
    plt.bar(np.arange(n), data['tracks'], align='center')
    plt.xticks(np.arange(n), data['tag'], rotation='vertical')
    plt.subplots_adjust(bottom=0.3)
    plt.ylabel('Tracks')
    plt.title('{} tags'.format(category))

    plt.savefig(output_file, bbox_inches='tight')
    # plt.show()
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plots the amount of tracks per tag')
    parser.add_argument('directory', help='Directory with TSV files with such columns: tag, artists, albums, tracks')
    parser.add_argument('tag_number', type=int, help='Number of tags to visualize')
    # parser.add_argument('output_file', help='Figure output file')
    args = parser.parse_args()

    for category in ['genre', 'instrument', 'mood_theme']:
        visualize(os.path.join(args.directory, category + '.tsv'), args.tag_number, category.capitalize(),
                  os.path.join(args.directory, '{}_top_{}.png'.format(category, args.tag_number)))
