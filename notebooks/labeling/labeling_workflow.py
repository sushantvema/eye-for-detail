from typing import Union
import labelme

from pathlib import Path

import argparse
import os
import random
import sys

def start_labeling(datasets: str):
    print(datasets)
    cwd = Path.cwd().parent.parent
    post_event_tiles_dir = cwd / "data" / "Post_Event_Grids_In_JPEG"
    pre_event_tiles_dir = cwd / "data" / "Post_Event_Grids_In_JPEG"
    assert len(os.listdir(post_event_tiles_dir)) == len(os.listdir(pre_event_tiles_dir))

    # Based on selected datasets, find out which tiles are labeled and unlabeled.
    if datasets == "post":
        all_files = os.listdir(post_event_tiles_dir)
        source_files = set([filename for filename in all_files if "jpg" in filename])
        annotation_files = set([filename for filename in all_files if "json" in filename])
        unannotated_files = list(source_files.difference(annotation_files))
        for filename in random.sample(unannotated_files, 5):
            os.system(f"labelme {post_event_tiles_dir / filename} --labels labels.txt --nodata --autosave")
        # import ipdb; ipdb.set_trace()
            
    if datasets == "both":
        all_files_post = os.listdir(post_event_tiles_dir)
        all_files_pre = os.listdir(pre_event_tiles_dir)
        source_files_post = set([filename for filename in all_files_post if "jpg" in filename])
        source_files_pre = set([filename for filename in all_files_pre if "jpg" in filename])
        for i in [random.randint(0, len(source_files_post) - 1) for j in range(5)]:
            pre_tile = pre_event_tiles_dir / ""
    return

def main(arguments):
    print(arguments)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--start-labeling', help="Start the process for labeling. Currently we label 5 random tiles at a time.", action="store_true")
    parser.add_argument("--datasets", type=str, choices=["pre", "post", "both"],
                    help="Choose the dataset(s) to start labeling.")

    args = parser.parse_args(arguments)

    if args.start_labeling:
        start_labeling(args.datasets)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))