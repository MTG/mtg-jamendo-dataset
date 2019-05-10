import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams, font_manager
import os


def visualize(directory, n):
    fig, axs = plt.subplots(1, 3, figsize=(12, 4))

    axs[0].set_ylabel('Tracks')

    for category, ax in zip(['genre', 'instrument', 'mood_theme'], axs):
        tsv_file = os.path.join(directory, category + '.tsv')
        data = pd.read_csv(tsv_file, delimiter='\t')

        data = data[:n]
        data = data.sort_values(by=['tracks'], ascending=False)

        ax.bar(np.arange(n), data['tracks'], align='center')
        ax.set_xticks(np.arange(n))
        ax.set_xticklabels(data['tag'], rotation='vertical')

        ax.set_title(category.replace('_', '/').capitalize())

    plt.subplots_adjust(bottom=0.3)

    output_file = os.path.join(directory, 'top{}.png'.format(n))
    fig.savefig(output_file, bbox_inches='tight')
    plt.show()
    plt.close()


def visualize2(directory, n):
    tag_list = []
    track_list = []
    for category in ['genre', 'instrument', 'mood_theme']:
        tsv_file = os.path.join(directory, category + '.tsv')
        data = pd.read_csv(tsv_file, delimiter='\t')
        data = data.sort_values(by=['tracks'], ascending=False)
        data = data[:n]
        tag_list += list(data['tag'])
        track_list += list(data['tracks'])

    fig = plt.figure(figsize=(12, 2.5))
    plt.style.use('seaborn-whitegrid')

    font_manager._rebuild()
    rcParams['font.family'] = 'serif'
    rcParams['font.serif'] = 'Times'
    plt.grid(False)
    plt.ylabel('# of tracks')
    plt.xlim([-1, 60])
    plt.ylim([0, 18000])
    for i, color in enumerate(['c', 'm', 'y']):
        indices = np.arange(n * i, n * (i + 1))
        plt.bar(indices, np.array(track_list)[indices], align='center')

    for i in [0, 20, 40, 59]:
        plt.text(i, track_list[i] + 300, track_list[i], fontsize=8, horizontalalignment='center')

    plt.xticks(np.arange(len(tag_list)), tag_list, rotation='vertical')
    ylabels = np.arange(4, 20, 4)
    plt.yticks(ylabels*1000, ['{}k'.format(ylabel) for ylabel in ylabels])
    plt.subplots_adjust(bottom=0.4)

    output_file = os.path.join(directory, 'top{}.pdf'.format(n))
    plt.savefig(output_file, bbox_inches='tight')
    # plt.show()
    plt.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plots the amount of tracks per tag')
    parser.add_argument('directory', help='Directory with TSV files with such columns: tag, artists, albums, tracks')
    parser.add_argument('tag_number', type=int, help='Number of tags to visualize')
    # parser.add_argument('output_file', help='Figure output file')
    args = parser.parse_args()

    visualize2(args.directory, args.tag_number)
