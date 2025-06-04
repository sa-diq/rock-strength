from core.axes_calibration import calibrate_axes
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

IMAGE_PATH = 'figure/fig8.png'
# Set default figure size
plt.rcParams['figure.figsize'] = (8, 8)
plt.rcParams['figure.dpi'] = 150
# Load image
img = mpimg.imread(IMAGE_PATH)


# Calibrate axes
pixel_to_data = calibrate_axes(img)
