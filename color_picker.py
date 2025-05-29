import cv2
import numpy as np
import matplotlib.pyplot as plt

# Absolute path to the cleaned plot image (update if needed)
CLEANED_PLOT_PATH = 'legend_preprocessed.png'

# Load the cleaned plot image
img = cv2.imread(CLEANED_PLOT_PATH)
if img is None:
    raise FileNotFoundError(f'Could not load image at {CLEANED_PLOT_PATH}')
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

picked_rgb = []

fig, ax = plt.subplots(figsize=(8, 8))
ax.imshow(img_rgb)
ax.set_title('Click on 6 data points to pick their RGB values')

# Click event handler
def onclick(event):
    if event.xdata is not None and event.ydata is not None:
        x, y = int(event.xdata), int(event.ydata)
        rgb_val = img_rgb[int(y), int(x)]
        picked_rgb.append(rgb_val)
        print(f'Clicked at (x={x}, y={y}), RGB={rgb_val}')
        if len(picked_rgb) >= 6:
            fig.canvas.mpl_disconnect(cid)
            print('\nPicked RGB values:')
            for i, rgb in enumerate(picked_rgb):
                print(f'Point {i+1}: R={rgb[0]}, G={rgb[1]}, B={rgb[2]}')
            plt.close(fig)

cid = fig.canvas.mpl_connect('button_press_event', onclick)
plt.show()