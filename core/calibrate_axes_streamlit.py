import streamlit as st
from PIL import Image
from core.streamlit_drawing import get_click_coordinates

def calibrate_axes_streamlit(image_pil):
    # X-axis points
    x_points = get_click_coordinates(image_pil, "Click 2 points along the X-axis", key="x_axis")
    if len(x_points) != 2:
        st.stop()

    x1_pixel, y1_pixel = x_points[0]
    x2_pixel, y2_pixel = x_points[1]
    x1_data = st.number_input("Enter actual X-axis value for first point", key="x1")
    x2_data = st.number_input("Enter actual X-axis value for second point", key="x2")

    # Y-axis points
    y_points = get_click_coordinates(image_pil, "Click 2 points along the Y-axis", key="y_axis")
    if len(y_points) != 2:
        st.stop()

    x3_pixel, y3_pixel = y_points[0]
    x4_pixel, y4_pixel = y_points[1]
    y1_data = st.number_input("Enter actual Y-axis value for first point", key="y1")
    y2_data = st.number_input("Enter actual Y-axis value for second point", key="y2")

    # Transformation function
    def pixel_to_data(x_pixel, y_pixel):
        x_data = x1_data + (x_pixel - x1_pixel) * (x2_data - x1_data) / (x2_pixel - x1_pixel)
        y_data = y1_data + (y_pixel - y3_pixel) * (y2_data - y1_data) / (y4_pixel - y3_pixel)
        return x_data, y_data

    return pixel_to_data
