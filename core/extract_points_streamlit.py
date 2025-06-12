import streamlit as st
from core.streamlit_drawing import get_click_coordinates

def extract_points_streamlit(image_pil, sandstone_name, pixel_to_data):
    points = get_click_coordinates(
        image=image_pil,
        instructions=f"Click all data points for {sandstone_name}, then proceed",
        key=f"points_{sandstone_name}"
    )
    if not points:
        return []
    data_points = []
    for x, y in points:
        x_data, y_data = pixel_to_data(x, y)
        data_points.append({
            "dataset": sandstone_name,
            "x_pixel": x,
            "y_pixel": y,
            "P(MPa)": x_data,
            "Q(MPa)": y_data
        })
    return data_points
