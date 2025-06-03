# qp_digitiser.py
"""
Digitise Q–P plot data from an image using user calibration and point selection.

Usage:
    python qp_digitiser.py

Requirements:
    - OpenCV (cv2)
    - numpy
    - matplotlib
    - json

"""
import cv2
import numpy as np
import matplotlib.pyplot as plt
import json
import os
from datetime import datetime

# --- CONFIG ---
SAMPLE_IMAGE_PATH = os.path.join('figure', 'fig8.png')


def get_axis_calibration(axis_name, ax, img):
    print(f"\nClick two points along the {axis_name}-axis (from left to right or bottom to top).\n")
    pts = plt.ginput(2, timeout=-1)
    pts = np.array(pts)
    print(f"You clicked: {pts}")
    vals = []
    for i, pt in enumerate(pts):
        val = float(input(f"Enter the real-world {axis_name} value (MPa) for point {i+1}: "))
        vals.append(val)
    vals = np.array(vals)
    # Linear calibration: pixel -> MPa
    # x = a*pixel + b
    a = (vals[1] - vals[0]) / (pts[1, 0 if axis_name=='X' else 1] - pts[0, 0 if axis_name=='X' else 1])
    b = vals[0] - a * pts[0, 0 if axis_name=='X' else 1]
    return {
        'pixel_points': pts.tolist(),
        'real_values': vals.tolist(),
        'a': a,
        'b': b
    }

def pixel_to_real(coord, calib_x, calib_y):
    px, py = coord
    P = calib_x['a'] * px + calib_x['b']
    Q = calib_y['a'] * py + calib_y['b']
    return P, Q

def main():
    # 1. Load image
    img = cv2.imread(SAMPLE_IMAGE_PATH)
    if img is None:
        print(f"Error: Could not load image at {SAMPLE_IMAGE_PATH}")
        return
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # 2. Display image
    fig, ax = plt.subplots()
    ax.imshow(img_rgb)
    ax.set_title('Q–P Plot: Click for Calibration')

    # 3. X-axis calibration
    calib_x = get_axis_calibration('X', ax, img_rgb)

    # 4. Y-axis calibration
    calib_y = get_axis_calibration('Y', ax, img_rgb)

    # 5. Show for data point selection
    ax.set_title('Click data points (left-click). Right-click or close to finish.')
    plt.draw()
    print("\nClick on data points to digitise. Right-click or close window to finish.\n")
    pts = plt.ginput(n=-1, timeout=0)
    print(f"You clicked {len(pts)} data points.")
    plt.close(fig)

    # 6. Convert to real-world coordinates
    data = []
    for pt in pts:
        P, Q = pixel_to_real(pt, calib_x, calib_y)
        data.append((P, Q))

    # 7. Label
    label = input("Enter a label/tag for this point group: ")

    # 8. Save CSV
    csv_path = f"digitised_{label.replace(' ', '_')}.csv"
    with open(csv_path, 'w') as f:
        f.write('P (MPa),Q (MPa),Label\n')
        for P, Q in data:
            f.write(f"{P:.3f},{Q:.3f},{label}\n")
    print(f"Saved digitised data to {csv_path}")

    # 9. Save JSON metadata
    meta = {
        'image': SAMPLE_IMAGE_PATH,
        'calibration': {
            'X': calib_x,
            'Y': calib_y
        },
        'label': label,
        'timestamp': datetime.now().isoformat()
    }
    json_path = f"digitised_{label.replace(' ', '_')}_meta.json"
    with open(json_path, 'w') as f:
        json.dump(meta, f, indent=2)
    print(f"Saved metadata to {json_path}")

if __name__ == '__main__':
    main()
