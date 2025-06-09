import matplotlib
matplotlib.use('TkAgg')
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

from core.axes_calibration import calibrate_axes
from core.plot_characteristics import get_plot_characteristics
from core.points_extraction import extract_points


IMAGE_PATH = 'figure/fig8.png'
# Set default figure size
plt.rcParams['figure.figsize'] = (8, 8)
plt.rcParams['figure.dpi'] = 150
# Load image
img = mpimg.imread(IMAGE_PATH)

# Collect plot characteristics
plot_name, sandstone_names = get_plot_characteristics()

# Calibrate axes
pixel_to_data = calibrate_axes(img)

# Extract the data points
extract_points(img, sandstone_names, pixel_to_data)

# Notify user of completion
print(f"Data extraction for plot '{plot_name}' completed successfully. Check 'extracted_data.csv' for results.")
