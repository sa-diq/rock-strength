import matplotlib.pyplot as plt
import time

def calibrate_axes(img):
    # X-Axis
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.set_title("Click the Minimum and the Maximum Points on the X-Axis")
    print("Click 2 points along the X axis, then close the window.")
    x_axis_points = plt.ginput(2, timeout=0)
    plt.close(fig)
    time.sleep(0.5)

    x1_pixel, y1_pixel = x_axis_points[0]
    x2_pixel, y2_pixel = x_axis_points[1]

    x1_data = int(input("Enter the value of the minimum point on the X-axis: "))
    x2_data = int(input("Enter the value of the maximum point on the X-axis: "))

    # Y-Axis
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.imshow(img)
    ax.set_title("Click the Minimum and the Maximum Points on the Y-Axis")
    print("Click 2 points along the Y axis, then close the window.")
    y_axis_points = plt.ginput(2, timeout=0)
    plt.close(fig)
    time.sleep(0.5)

    x3_pixel, y3_pixel = y_axis_points[0]
    x4_pixel, y4_pixel = y_axis_points[1]

    y1_data = int(input("Enter the value of the minimum point on the Y-axis: "))
    y2_data = int(input("Enter the value of the maximum point on the Y-axis: "))

    # Coordinate transformation function
    def pixel_to_data(x_pixel, y_pixel):
        x_data = x1_data + (x_pixel - x1_pixel) * (x2_data - x1_data) / (x2_pixel - x1_pixel)
        y_data = y1_data + (y_pixel - y3_pixel) * (y2_data - y1_data) / (y4_pixel - y3_pixel)
        return x_data, y_data

    return pixel_to_data
