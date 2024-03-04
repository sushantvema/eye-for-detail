## IMPORTS
import os, sys
sys.path.insert(0, os.path.abspath("../.."))

import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
from PIL import Image

from config import IN_DEVELOPMENT
from config import DATA_DIR, SOURCE_IMAGES_DIR, POST_EVENT_ORIGINAL_TILES_TIF_DIR, POST_EVENT_CONVERTED_TILES_TIF_DIR, BUILDING_FOOTPRINTS_DIR
from config import TILE_DIMENSIONS, NUM_SAMPLE_TILES
from utils import visualize_geotiff, sample_random_tile_from_tif, convert_tif_crs_to_shapefile_crs
from utils import get_corners_from_tif_in_certain_crs, get_points_from_bounds, get_buildings_in_polygon
from utils import get_image_array, get_transposed_image_data
from utils import rasterize

####################################

def main():

    post_event_source_image = SOURCE_IMAGES_DIR / "Post_Event_San_Juan.tif"

    shapefile = gpd.read_file(BUILDING_FOOTPRINTS_DIR)
    shapefile_crs = shapefile.crs

    if IN_DEVELOPMENT:
        np.random.seed(0)
        # import ipdb; ipdb.set_trace()

    # Sample certain number of tiles, convert their coordinate systems to that of a building footprint shapefile,
    # and match polygon rasters. 
    for i in range(NUM_SAMPLE_TILES):
        tile_path = sample_random_tile_from_tif(sample_idx=i, input_file=post_event_source_image, output_dir=POST_EVENT_ORIGINAL_TILES_TIF_DIR,
                                tile_height=TILE_DIMENSIONS, tile_width=TILE_DIMENSIONS)

        converted_tile_path = convert_tif_crs_to_shapefile_crs(input_tif=tile_path, output_dir=POST_EVENT_CONVERTED_TILES_TIF_DIR, dest_crs=shapefile_crs)

        corner_coordinates = get_corners_from_tif_in_certain_crs(input_tif=converted_tile_path, tile_width=TILE_DIMENSIONS)
        
        # import ipdb; ipdb.set_trace()

        four_corner_coords = get_points_from_bounds(*corner_coordinates)

        building_footprints_in_tile = get_buildings_in_polygon(shapefile=shapefile, corner_coords=four_corner_coords)
        
        if len(building_footprints_in_tile):
            continue

        transposed_image = get_transposed_image_data(input_tif=converted_tile_path)

        rasterized_footprints = rasterize(raster_path=converted_tile_path, shapefile=building_footprints_in_tile)

        transposed_image[rasterized_footprints != 0] = 0
        plt.imshow(transposed_image)
        plt.show()
        

    return

    

if __name__ == "__main__":
    main()

