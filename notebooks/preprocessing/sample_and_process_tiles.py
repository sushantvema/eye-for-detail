## IMPORTS
import os, sys
sys.path.insert(0, os.path.abspath("../.."))

import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from PIL import Image

from config import IN_DEVELOPMENT
from config import DATA_DIR, SOURCE_IMAGES_DIR, POST_EVENT_ORIGINAL_TILES_TIF_DIR, POST_EVENT_CONVERTED_TILES_TIF_DIR, BUILDING_FOOTPRINTS_DIR, TRAIN_DIR
from config import TILE_DIMENSIONS, NUM_SAMPLE_TILES
from utils import visualize_geotiff, sample_random_tile_from_tif, convert_tif_crs_to_shapefile_crs
from utils import get_corners_from_tif_in_certain_crs, get_points_from_bounds, get_buildings_in_polygon
from utils import get_image_array, get_transposed_image_data
from utils import rasterize
from utils import create_labelme_json, convert_coords_to_pixel_coords, convert_all_coords_to_pixel_coords, get_all_labelme_shapes
from utils import tiff_to_jpeg

import argparse
import json

####################################

def main(arguments):

    print(arguments)
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--dataset-name', help="Name for generated dataset.", type=str)

    args = parser.parse_args(arguments)

    dataset_name = args.dataset_name
    
    post_event_source_image = SOURCE_IMAGES_DIR / "Post_Event_San_Juan.tif"

    shapefile = gpd.read_file(BUILDING_FOOTPRINTS_DIR)
    shapefile_crs = shapefile.crs

    if IN_DEVELOPMENT:
        np.random.seed(0)
        # import ipdb; ipdb.set_trace()

    OUTPUT_DIR = TRAIN_DIR / dataset_name
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Sample certain number of tiles, convert their coordinate systems to that of a building footprint shapefile,
    # and match polygon rasters. 
    counter = NUM_SAMPLE_TILES
    while counter > 0:
        tile_path = sample_random_tile_from_tif(sample_idx=counter, input_file=post_event_source_image, output_dir=POST_EVENT_ORIGINAL_TILES_TIF_DIR,
                                tile_height=TILE_DIMENSIONS, tile_width=TILE_DIMENSIONS)

        converted_tile_path = convert_tif_crs_to_shapefile_crs(input_tif=tile_path, output_dir=OUTPUT_DIR, dest_crs=shapefile_crs)

        corner_coordinates = get_corners_from_tif_in_certain_crs(input_tif=converted_tile_path, tile_width=TILE_DIMENSIONS)

        four_corner_coords = get_points_from_bounds(*corner_coordinates)

        building_footprints_in_tile = get_buildings_in_polygon(shapefile=shapefile, corner_coords=four_corner_coords)
        
        if len(building_footprints_in_tile) == 0:
            continue

        tile_name = str(converted_tile_path).split(".")[0].split("/")[-1]
        output_file_path = TRAIN_DIR / OUTPUT_DIR / f"{tile_name}.json" 
        create_labelme_json(building_footprints_in_tile, converted_tile_path, output_file_path)

        counter -= 1
        
    return

    

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

