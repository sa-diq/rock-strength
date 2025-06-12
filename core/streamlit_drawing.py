from streamlit_drawable_canvas import st_canvas
import streamlit as st
import numpy as np

def get_click_coordinates(image, instructions, key, stroke_width=3):
    st.write(instructions)
    
    # Color selector
    color = st.selectbox(
        "Point color:",
        ["#FF00FF", "#00FFFF", "#32CD32", "#FFD700", "#FF1493", "#8A2BE2"],
        format_func=lambda x: {"#FF00FF": "Magenta", "#00FFFF": "Cyan", 
                              "#32CD32": "Lime", "#FFD700": "Gold",
                              "#FF1493": "Pink", "#8A2BE2": "Violet"}[x],
        key=f"{key}_color"
    )
    
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=color,
        background_color="#eee",
        background_image=image,
        update_streamlit=True,
        height=image.height,
        width=image.width,
        drawing_mode="point",
        key=key
    )

    if canvas_result.json_data and canvas_result.json_data["objects"]:
        return [
            (obj["left"], obj["top"])
            for obj in canvas_result.json_data["objects"]
            if obj["type"] == "circle"
        ]
    return []