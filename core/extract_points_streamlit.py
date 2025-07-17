import streamlit as st
from core.streamlit_drawing import get_click_coordinates

def extract_points_streamlit(image_pil, sandstone_name, pixel_to_data):
    """
    Extract points for a sandstone - this should only be called once to set up the interface
    """
    
    # Get coordinates from the drawing function
    points = get_click_coordinates(
        image=image_pil,
        instructions=f"Click all data points for {sandstone_name}",
        key=f"points_{sandstone_name}"
    )
    
    # Handle case where points might be None
    if not points:
        return []
    
    # Convert to data points format
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