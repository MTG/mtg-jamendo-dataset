import argparse

import commons
import util


def merge_tags(tracks, tag_map_all):
    for track_id, track in tracks.items():
        for category, tag_map in tag_map_all.items():
            tags_original = track[category] & tag_map.keys()
            if len(tags_original) > 0:
                tags_new = {tag_map[tag] for tag in tags_original}
                track[category] = track[category] - tags_original | tags_new


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Merges tags according to the mapping')
    parser.add_argument('tsv_file', help=commons.METADATA_DESCRIPTION)
    parser.add_argument('map_file', help='JSON file: {"category": {"original_tag": "new_tag"}}')
    parser.add_argument('output_file', help='output tsv file')
    args = parser.parse_args()

    tracks, tags, extra = commons.read_file(args.tsv_file)
    tag_map = util.read_json(args.map_file)
    merge_tags(tracks, tag_map)
    commons.write_file(tracks, args.output_file, extra)
