import os, sys
sys.path.insert(0, os.path.abspath("../.."))

from osgeo import gdal, osr
import matplotlib.pyplot as plt
import numpy as np
import pathlib
import shapely
from PIL import Image
import rasterio
from rasterio import features
from rasterio.enums import MergeAlg

from config import RASTERS_DIR

import os
import json

def get_image_array(tiff_file):
    """
    Returns the band data of a given .tif image.
    """
    if isinstance(tiff_file, pathlib.Path):
        tiff_file = gdal.Open(tiff_file) 
    bands = []
    for i in range(1, 4):
        bands.append(tiff_file.GetRasterBand(i).ReadAsArray())
    bands = np.array(bands).transpose(2, 1, 0)
    return bands

def tiff_to_jpeg(tiff_file, output_file):
    img = Image.open(tiff_file)
    img = img.convert("RGB")
    img.save(output_file)

def visualize_geotiff(tiff_file):
    """
    Plots RGB image of a given .tif file.
    """
    bands = get_image_array(tiff_file)
    plt.imshow(bands)
    plt.show()

def sample_random_tile_from_tif(sample_idx:int, input_file:str, output_dir:pathlib.Path, tile_width:int, tile_height:int):
    """
    From a .tif input_file, sample a random tile_width x tile_height size patch and save it to an output directory.
    """
    ds = gdal.Open(input_file)
    # Get image size and number of bands
    width = ds.RasterXSize
    height = ds.RasterYSize
    num_bands = ds.RasterCount

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Sample a random x_ and y_offset to select a tile
    x_offset = np.random.randint(0, width - tile_width)
    y_offset = np.random.randint(0, height - tile_height)

    # Handle edge cases
    tile_width = min(tile_width, width - x_offset)
    tile_height = min(tile_height, height - y_offset)

    tile = []
    for band in range(1, num_bands + 1):
        tile_data = ds.GetRasterBand(band).ReadAsArray(x_offset, y_offset, tile_width , tile_height)
        tile.append(tile_data)

    # Create output filename
    output_file = output_dir / f"{sample_idx}_tile.tif"
        
    # Create an output TIFF file with same CRS and band values range
    driver = gdal.GetDriverByName("GTiff")
    options = ['COMPRESS=DEFLATE', 'PREDICTOR=2', 'TILED=YES']
    out_ds = driver.Create(output_file, tile_width, tile_height, num_bands, 
                ds.GetRasterBand(1).DataType, options=options)
    # out_ds = driver.Create(output_file, tile_width, tile_height, num_bands, ds.GetRasterBand(1).DataType)

    # Set the geotransform
    geotransform = list(ds.GetGeoTransform())
    geotransform[0] = geotransform[0] + x_offset * geotransform[1]
    geotransform[3] = geotransform[3] + y_offset * geotransform[5]
    out_ds.SetGeoTransform(tuple(geotransform))

    # Set the projection
    out_ds.SetProjection(ds.GetProjection())

    # Write each band to the output file
    for band in range(1, num_bands + 1):
        out_band = out_ds.GetRasterBand(band)
        out_band.WriteArray(tile[band - 1])

    # Close the output file
    out_ds = None

    print("Tiles generation completed.")

    return output_file

def convert_tif_crs_to_shapefile_crs(input_tif, output_dir, dest_crs: str):
    """
    Convert the CRS of an input .tif to a different CRS, and then save the converted .tif to an 
    output directory with a modified file name.
    """
    
    target_crs = osr.SpatialReference()
    if dest_crs == "EPSG:32620":
        target_crs.ImportFromEPSG(32620)
    
    # Open input GeoTIFF file
    input_dataset = gdal.Open(input_tif)

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    file_name = str(input_tif).split(".")[0].split("/")[-1]
    output_tif_path = output_dir / f"{file_name}_converted.tif"

    # Create output GeoTIFF file with the desired target CRS
    output_dataset = gdal.Warp(output_tif_path, input_dataset, dstSRS=target_crs)
    
    # Close datasets
    input_dataset = None
    output_dataset = None

    return output_tif_path

def get_corners_from_tif_in_certain_crs(input_tif, tile_width=512):
    """
    Uses the geotransform of a given .tif image to calculate the top left and 
    bottom right corner coordinates in the image's native CRS.
    """
    if isinstance(input_tif, pathlib.Path):
        dataset = gdal.Open(input_tif)
    gt = dataset.GetGeoTransform()
    x_0 = gt[0]
    y_0 = gt[3]
    x_1 = x_0 + tile_width * gt[1]
    y_1 = y_0 + tile_width * gt[5]
    return (x_0, y_0, x_1, y_1)

def get_points_from_bounds(minx, miny, maxx, maxy):
    """
    Return all 4 enumerated coordinate points based on the top left and top right corner.
    """
    return [(minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)]
    
def get_buildings_in_polygon(shapefile, corner_coords):
    """
    Given a shapefile of building footprints and coordinate bounds for a Polygon enclosure,
    find all of the building footprints within the Polygon.
    """
    sampled_image_polygon = shapely.Polygon(corner_coords)
    buildings_in_sampled_image = shapefile[shapefile.within(sampled_image_polygon)]

    return buildings_in_sampled_image

def get_transposed_image_data(input_tif):
    """
    Flips and rotates a .tif tile in order to match with building footprints. 
    """
    image_data = get_image_array(tiff_file=input_tif)
    image = Image.fromarray(image_data)
    image = image.transpose(Image.FLIP_LEFT_RIGHT)
    image = image.rotate(90)
    image_data = np.asarray(image).copy()
    return image_data

def rasterize(raster_path, shapefile):
    with rasterio.open(raster_path, "r") as src:
        # Get the CRS of the raster
        raster_crs = src.crs

        # Reproject the geometries
        shapefile = shapefile.to_crs(raster_crs)

        # Get list of geometries for all features in vector file
        geom = [shapes for shapes in shapefile.geometry]

        # Rasterize vector using the shape and coordinate system of the raster
        rasterized = features.rasterize(geom,
                                        out_shape = src.shape,
                                        fill = 0,
                                        out = None,
                                        transform = src.transform,
                                        all_touched = True,
                                        merge_alg=MergeAlg.add,
                                        default_value = 255,
                                        dtype = None)
        return rasterized
    
def convert_coords_to_pixel_coords(polygon, geotransform, use_bounding_box=True):
    if use_bounding_box:
        bounds = polygon.bounds
        building_coords = np.array(get_points_from_bounds(*bounds))
    if not use_bounding_box:
        building_coords = np.array(list(polygon.exterior.coords))
    pixel_coords = np.zeros_like(building_coords)
    pixel_coords[:, 0] = (building_coords[:, 0] - geotransform[0]) / geotransform[1]
    pixel_coords[:, 1] = (building_coords[:, 1] - geotransform[3]) / geotransform[5]
    return pixel_coords

def convert_all_coords_to_pixel_coords(gdf, converted_tile_path, use_bounding_box:bool):
    gt = gdal.Open(converted_tile_path).GetGeoTransform()
    def apply_conversion(row):
        return convert_coords_to_pixel_coords(row["geometry"], gt, use_bounding_box=use_bounding_box)
    return gdf.apply(apply_conversion, axis=1)

def create_label_shape_dict(pixel_coords, group_id:str):
    labelme_dict = {
        "label": "unlabeled",
        "group_id": group_id,
        "description": "",
        "shape_type": "polygon",
        "flags": {},
        "mask": None,
        "points": pixel_coords.tolist()
    }
    return labelme_dict   

def get_all_labelme_shapes(gdf, converted_tile_path, use_bounding_box:bool):
    pixel_coords = convert_all_coords_to_pixel_coords(gdf, converted_tile_path, use_bounding_box=use_bounding_box)
    group_id = "bbox" if use_bounding_box else "polygon"
    shapes = [
        create_label_shape_dict(coords, group_id=group_id) for coords in pixel_coords
    ]
    return shapes

def create_labelme_json(building_footprints_in_tile, converted_tile_path, output_file_path):
    file_name_of_tile = str(converted_tile_path).split("/")[-1]
    labelme_json = {
        "version": "5.4.1",
        "flags": {},
        "imagePath": file_name_of_tile,
        "imageData": None,
        "imageHeight": 512,
        "imageWidth": 512,
        "shapes": get_all_labelme_shapes(building_footprints_in_tile, converted_tile_path, use_bounding_box=True)
    }
    json.dump(labelme_json, open(output_file_path, "w+"), indent=4)