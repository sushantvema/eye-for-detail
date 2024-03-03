## IMPORTS
import os, sys
sys.path.insert(0, os.path.abspath("../.."))

from osgeo import gdal, osr
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd

from config import IN_DEVELOPMENT
from config import DATA_DIR, SOURCE_IMAGES_DIR, POST_EVENT_ORIGINAL_TILES_TIF_DIR, POST_EVENT_CONVERTED_TILES_TIF_DIR, BUILDING_FOOTPRINTS_DIR
from config import TILE_DIMENSIONS, NUM_SAMPLE_TILES
from utils import visualize_geotiff, sample_random_tile_from_tif, convert_tif_crs_to_shapefile_crs, get_corners_from_tif_in_certain_crs

####################################

def main():

    if IN_DEVELOPMENT:
        np.random.seed(0)
        # import ipdb; ipdb.set_trace()

    post_event_source_image = SOURCE_IMAGES_DIR / "Post_Event_San_Juan.tif"

    shapefile = gpd.read_file(BUILDING_FOOTPRINTS_DIR)
    shapefile_crs = shapefile.crs

    # Sample certain number of tiles, convert their coordinate systems to that of a building footprint shapefile,
    # and match polygon rasters. 
    for i in range(NUM_SAMPLE_TILES):
        tile_path = sample_random_tile_from_tif(sample_idx=i, input_file=post_event_source_image, output_dir=POST_EVENT_ORIGINAL_TILES_TIF_DIR,
                                tile_height=TILE_DIMENSIONS, tile_width=TILE_DIMENSIONS)

        converted_tile_path = convert_tif_crs_to_shapefile_crs(input_tif=tile_path, output_dir=POST_EVENT_CONVERTED_TILES_TIF_DIR, dest_crs=shapefile_crs)

        corner_coordinates = get_corners_from_tif_in_certain_crs(input_tif=converted_tile_path, tile_width=TILE_DIMENSIONS)
        print(corner_coordinates)

    return

    

if __name__ == "__main__":
    main()

