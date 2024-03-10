## IMPORTS
import os, sys
import random
import pathlib
import json
sys.path.insert(0, os.path.abspath("../.."))

import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from PIL import Image

from config import IN_DEVELOPMENT
from config import DATA_DIR, SOURCE_IMAGES_DIR, POST_EVENT_ORIGINAL_TILES_TIF_DIR, POST_EVENT_CONVERTED_TILES_TIF_DIR, BUILDING_FOOTPRINTS_DIR, TRAIN_DIR
from config import TILE_DIMENSIONS, NUM_SAMPLE_TILES
from utils import sample_random_tile_from_tif, convert_tif_crs_to_shapefile_crs
from utils import get_corners_from_tif_in_certain_crs, get_points_from_bounds, get_buildings_in_polygon
from utils import create_labelme_json
from utils import convert_tiff_to_jpeg, delete_file_by_extension
from roboflow import Roboflow

import argparse

####################################

def main(arguments):

    print(arguments)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--annotate-mode', help="Start labelme with propagated class labels on a custom dataset.", action="store_true")
    parser.add_argument('--dataset-name', help="Name for your custom dataset.", type=str)
    parser.add_argument('--num-samples', help="Override NUM_SAMPLE in config.py with a custom number.", type=str)
    parser.add_argument('--should-convert-crs', help="Decide whether to convert tile projections to match building footprints shapefile.", action="store_true")
    parser.add_argument('--img-type', help="What image type to convert the tiles into.", type=str, choices=[".tif", ".jpg", ".png"])
    parser.add_argument("--upload-to-roboflow", help="Flag if present will upload image to roboflow.", action="store_true")
    parser.add_argument("--seed", help="Random seed for sampling", type=int, default=random.randint(0, 10_000_000))

    args = parser.parse_args(arguments)  
    
    if args.upload_to_roboflow:
        creds = json.load(open(pathlib.Path(__file__).parent.parent.parent / "credentials.json", "r"))
        rf = Roboflow(creds["ROBOFLOW_API_KEY"])
        workspaceId = 'sushantcv'
        projectId = 'ey-openscience-data-challenge-24'
        project = rf.workspace(workspaceId).project(projectId)

    if args.num_samples is not None:
        NUM_SAMPLE_TILES = args.num_samples

    annotate_mode = args.annotate_mode
    dataset_name = args.dataset_name
    if annotate_mode:
        DATA_FOLDER = TRAIN_DIR / dataset_name
        os.chdir(DATA_FOLDER)
        os.system("labelme --labels undamagedresidentialbuilding,damagedresidentialbuilding,undamagedcommercialbuilding,damagedcommercialbuilding --nodata")
        return
    
    file_extension = args.img_type
    convert_crs = args.should_convert_crs
    
    post_event_source_image = SOURCE_IMAGES_DIR / "Post_Event_San_Juan.tif"

    shapefile = gpd.read_file(BUILDING_FOOTPRINTS_DIR)
    shapefile_crs = shapefile.crs

    np.random.seed(args.seed)
    print("Using seed:", args.seed)
        # import ipdb; ipdb.set_trace()

    OUTPUT_DIR = TRAIN_DIR / dataset_name
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Sample certain number of tiles, convert their coordinate systems to that of a building footprint shapefile,
    # and match polygon rasters. 
    counter = int(NUM_SAMPLE_TILES)
    while counter > 0:
        if convert_crs:
            tile_path, x_offset, y_offset = sample_random_tile_from_tif(sample_idx=counter, input_file=post_event_source_image, output_dir=POST_EVENT_ORIGINAL_TILES_TIF_DIR,
                                    tile_height=TILE_DIMENSIONS, tile_width=TILE_DIMENSIONS)
            converted_tile_path = convert_tif_crs_to_shapefile_crs(input_tif=tile_path, output_dir=OUTPUT_DIR, dest_crs=shapefile_crs)
        else:
            tile_path, x_offset, y_offset = sample_random_tile_from_tif(sample_idx=counter, input_file=post_event_source_image, output_dir=OUTPUT_DIR,
                                    tile_height=TILE_DIMENSIONS, tile_width=TILE_DIMENSIONS)
            converted_tile_path = convert_tif_crs_to_shapefile_crs(input_tif=tile_path, output_dir=POST_EVENT_CONVERTED_TILES_TIF_DIR, dest_crs=shapefile_crs)

        corner_coordinates = get_corners_from_tif_in_certain_crs(input_tif=converted_tile_path, tile_width=TILE_DIMENSIONS)

        four_corner_coords = get_points_from_bounds(*corner_coordinates)

        building_footprints_in_tile = get_buildings_in_polygon(shapefile=shapefile, corner_coords=four_corner_coords)
        
        if len(building_footprints_in_tile) == 0:
            continue 

        if convert_crs:
            tile_name = str(converted_tile_path).split(".")[0].split("/")[-1]
            output_file_path = TRAIN_DIR / OUTPUT_DIR / f"{tile_name}.json"
        else:
            tile_name = str(tile_path).split(".")[0].split("/")[-1]
            output_file_path = TRAIN_DIR / OUTPUT_DIR / f"{tile_name}.json"
            
        create_labelme_json(building_footprints_in_tile, tile_path, output_file_path)
            
        if file_extension == ".jpg":
            convert_tiff_to_jpeg(input_dir=OUTPUT_DIR, output_dir=OUTPUT_DIR)
            tile_path = pathlib.Path(tile_path.parent, tile_path.stem + ".jpg")
            tile_path = tile_path.rename(pathlib.Path(tile_path.parent, f"{x_offset}_{y_offset}" + ".jpg"))
            delete_file_by_extension(dir_name=OUTPUT_DIR, extension=".tif")
        
        if args.upload_to_roboflow:
            project.upload(
                image_path=str(tile_path)
            )

        counter -= 1
        
    return

    

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

