import cv2
import numpy as np
import matplotlib.pyplot as plt

def detect_axes(image_path, show_plot=True):
    """
    Automatically detect the x and y axes in a plot image.
    Returns: (x_axis_line, y_axis_line) as ((x1, y1, x2, y2), ...)
    """
    # Load and preprocess the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Image not found at path: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Enhance contrast using CLAHE
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(16, 16))
    enhanced = clahe.apply(gray)

    # Edge detection
    edges = cv2.Canny(enhanced, 50, 150)

    # Morphological closing to remove noise and close gaps
    kernel = np.ones((3, 3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Hough Line Transform
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100, minLineLength=100, maxLineGap=10)
    if lines is None:
        print("No lines detected.")
        return None, None, None, None, None, None  # Return 6 values for unpacking

    # Function to extend lines
    def extend_line(x1, y1, x2, y2, width, height):
        if abs(x2 - x1) < 1e-6:  # Vertical line
            return (x1, 0, x1, height)
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        x0_ext = 0
        y0_ext = int(slope * x0_ext + intercept)
        xmax_ext = width
        ymax_ext = int(slope * xmax_ext + intercept)
        return (x0_ext, y0_ext, xmax_ext, ymax_ext)

    # Find the longest horizontal and vertical lines (likely axes)
    x_axis = None
    y_axis = None
    max_horiz = 0
    max_vert = 0
    height, width = img.shape[:2]

    for line in lines:
        x1, y1, x2, y2 = line[0]
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        angle = np.arctan2(dy, dx) * 180 / np.pi

        # Horizontal line detection
        if abs(angle) < 10 and dx > max_horiz:  # Horizontal line
            max_horiz = dx
            x_axis = extend_line(x1, y1, x2, y2, width, height)

        # Vertical line detection
        elif abs(angle - 90) < 10 and dy > max_vert:  # Vertical line
            max_vert = dy
            y_axis = extend_line(x1, y1, x2, y2, width, height)

    # Calculate x0, xmax, y0, ymax from detected axes
    x0 = y0 = xmax = ymax = None
    if x_axis:
        x0 = min(x_axis[0], x_axis[2])
        xmax = max(x_axis[0], x_axis[2])
    if y_axis:
        y0 = min(y_axis[1], y_axis[3])
        ymax = max(y_axis[1], y_axis[3])

    # Optionally show the detected axes
    if show_plot and (x_axis or y_axis):
        vis = img.copy()
        if x_axis:
            cv2.line(vis, (x_axis[0], x_axis[1]), (x_axis[2], x_axis[3]), (0, 255, 0), 3)
        if y_axis:
            cv2.line(vis, (y_axis[0], y_axis[1]), (y_axis[2], y_axis[3]), (255, 0, 0), 3)
        plt.figure(figsize=(8, 8))
        plt.imshow(cv2.cvtColor(vis, cv2.COLOR_BGR2RGB))
        plt.title(f'Detected Axes\nx0={x0}, xmax={xmax}, y0={y0}, ymax={ymax}')
        plt.axis('off')
        plt.show()

    return x_axis, y_axis, x0, xmax, y0, ymax

# Example usage:
# x_axis, y_axis, x0, xmax, y0, ymax = detect_axes('fig8.png')
# print(f'x0={x0}, xmax={xmax}, y0={y0}, ymax={ymax}')