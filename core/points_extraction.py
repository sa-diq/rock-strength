import matplotlib.pyplot as plt
import pandas as pd
import time


def extract_points(img, sandstone_names, pixel_to_data):
    all_data_points = []
    for i, name in enumerate(sandstone_names):
        plt.close('all')
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111)
        ax.imshow(img)
        ax.set_title(f"Click on data points for {name}.\nClose the window when done.")
        print(f"Select points for {name}. Click on all points, then close the window.")
        plt.draw()        # Force draw
        plt.pause(0.1)           # Let UI catch up
        points = plt.ginput(n=-1, timeout=0)
        plt.close(fig)
        time.sleep(0.5)
        for x, y in points:
            x_data, y_data = pixel_to_data(x, y)
            all_data_points.append({
                'dataset': name,
                'x_pixel': x,
                'y_pixel': y,
                'x_data': x_data,
                'y_data': y_data
            })

    # Save to CSV
    df = pd.DataFrame(all_data_points)
    return df