import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import pandas as pd
import time

# === USER SETTINGS ===
image_path = 'fig8.png'  # Change to your image filename
num_datasets = 2         # Set the number of datasets you want to extract
dataset_names = ['Dataset 1', 'Dataset 2']  # Change as needed

# === MAIN SCRIPT ===
img = mpimg.imread(image_path)
all_points = []

# --- Axis Calibration ---
plt.close('all')
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111)
ax.imshow(img)
ax.set_title("Click two points along the X axis (e.g., origin and x-max tick)")
print("Click two points along the X axis (e.g., origin and x-max tick), then close the window.")
x_axis_pts = plt.ginput(2, timeout=0)
plt.close(fig)
time.sleep(0.5)

x1_pixel, y1_pixel = x_axis_pts[0]
x2_pixel, y2_pixel = x_axis_pts[1]
x1_data = float(input("Enter the data value for the first X axis point: "))
x2_data = float(input("Enter the data value for the second X axis point: "))

fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111)
ax.imshow(img)
ax.set_title("Click two points along the Y axis (e.g., origin and y-max tick)")
print("Click two points along the Y axis (e.g., origin and y-max tick), then close the window.")
y_axis_pts = plt.ginput(2, timeout=0)
plt.close(fig)
time.sleep(0.5)

x3_pixel, y3_pixel = y_axis_pts[0]
x4_pixel, y4_pixel = y_axis_pts[1]
y1_data = float(input("Enter the data value for the first Y axis point: "))
y2_data = float(input("Enter the data value for the second Y axis point: "))

# Compute linear mapping: pixel -> data
def pixel_to_data(x_pixel, y_pixel):
    # X axis: map x_pixel to data
    x_data = x1_data + (x_pixel - x1_pixel) * (x2_data - x1_data) / (x2_pixel - x1_pixel)
    # Y axis: map y_pixel to data (note: y increases downward in images)
    y_data = y1_data + (y_pixel - y3_pixel) * (y2_data - y1_data) / (y4_pixel - y3_pixel)
    return x_data, y_data

# --- Data Point Extraction ---
for i in range(num_datasets):
    plt.close('all')
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.set_title(f"Click on data points for {dataset_names[i]}.\nClose the window when done.")
    print(f"Select points for {dataset_names[i]}. Click on all points, then close the window.")
    pts = plt.ginput(n=-1, timeout=0)
    plt.close(fig)
    time.sleep(0.5)
    for x, y in pts:
        x_data, y_data = pixel_to_data(x, y)
        all_points.append({
            'dataset': dataset_names[i],
            'x_pixel': x,
            'y_pixel': y,
            'x_data': x_data,
            'y_data': y_data
        })

# Save to CSV
df = pd.DataFrame(all_points)
df.to_csv('extracted_points_calibrated.csv', index=False)
print(f"Extracted {len(df)} points. Saved to extracted_points_calibrated.csv.")