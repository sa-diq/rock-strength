from streamlit_drawable_canvas import st_canvas
import streamlit as st
import numpy as np

def get_click_coordinates(image, instructions, key, stroke_width=3):
    st.write(instructions)
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color="#FF0000",
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
