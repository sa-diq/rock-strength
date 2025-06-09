from core.axes_calibration import calibrate_axes
from core.points_extraction import extract_points
import os
import matplotlib.image as mpimg


def run_extraction(image_path, sandstone_names, plot_name):
    # Load Image
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found at {image_path}")
    img = mpimg.imread(image_path)

    # Calibrate axes
    pixel_to_data = calibrate_axes(img)

    # Extract the data points
    extract_points(img, sandstone_names, pixel_to_data)

    print(f"Extraction for {plot_name} done.")