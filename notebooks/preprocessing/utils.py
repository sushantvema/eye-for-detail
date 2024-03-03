from osgeo import gdal, osr
import matplotlib.pyplot as plt

import numpy as np
import pathlib

import os

def visualize_geotiff(tiff_file):
    """
    Plots RGB image of a given .tif file.
    """
    if isinstance(tiff_file, str):
        tiff_file = gdal.Open(tiff_file, gdal.GA_ReadOnly) 
    bands = []
    for i in range(1, 4):
        bands.append(tiff_file.GetRasterBand(i).ReadAsArray())
    bands = np.array(bands).transpose(2, 1, 0)
    plt.imshow(bands)

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
        tile_data = ds.GetRasterBand(band).ReadAsArray(x_offset, y_offset, tile_width, tile_height)
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

    file_name = str(input_tif).split(".")[0]
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