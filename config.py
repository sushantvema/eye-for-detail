import pathlib

# temp fix
CWD = pathlib.Path.cwd().parent.parent

# Development flag
IN_DEVELOPMENT=True

# Data directories
DATA_DIR = CWD / "data"
SOURCE_IMAGES_DIR = DATA_DIR / "source_images"
BUILDING_FOOTPRINTS_DIR = DATA_DIR / "buildings-footprints-roi"
RASTERS_DIR = DATA_DIR / "rasters"
TILES_DIR = DATA_DIR / "tiles"
POST_EVENT_ORIGINAL_TILES_TIF_DIR = TILES_DIR / "Post_Event_Grids_In_TIF"
POST_EVENT_CONVERTED_TILES_TIF_DIR = TILES_DIR / "Post_Event_Converted_Grids_In_TIF"
POST_EVENT_ORIGINAL_TILES_JPEG_DIR = TILES_DIR / "Post_Event_Grids_In_JPEG"

# Preprocessing Parameters
TILE_DIMENSIONS = 512  #pixels width and height (square tiles)
NUM_SAMPLE_TILES = 100

# Submission images
TEST_SET_DIR = DATA_DIR / "challenge_1_submission_images" 

