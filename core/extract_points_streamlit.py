import streamlit as st
from core.streamlit_drawing import get_click_coordinates

def extract_points_streamlit(image_pil, sandstone_name, pixel_to_data):
    points = get_click_coordinates(
        image=image_pil,
        instructions=f"Click all data points for {sandstone_name}",
        key=f"points_{sandstone_name}"
    )
    
    if not points:
        return []
    
    data_points = []
    for x, y in points:
        # SIMPLE OFFSET CORRECTION - adjust these values based on your testing
        x_corrected = x + 5  # Start with +5 pixels to the right
        y_corrected = y + 0  # No Y correction for now
        
        x_data, y_data = pixel_to_data(x_corrected, y_corrected)
        data_points.append({
            "dataset": sandstone_name,
            "x_pixel": x_corrected,  # Store original click position
            "y_pixel": y_corrected,
            "P(MPa)": x_data,
            "Q(MPa)": y_data
        })
    
    return data_points